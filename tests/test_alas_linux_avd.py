import unittest
import signal
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from module.alas import AzurLaneAutoScript
from module.device.device import Device
from module.device.platform.platform_linux import PlatformLinux
from module.webui.process_manager import ProcessManager


class SchedulerConfig:
    def __init__(self, tasks):
        self.tasks = list(tasks)
        self.task = None
        self.Optimization_WhenTaskQueueEmpty = 'close_emulator'
        self.task_calls = []

    def get_next(self):
        if len(self.tasks) > 1:
            return self.tasks.pop(0)
        return self.tasks[0]

    def bind(self, task):
        self.task = task

    def task_call(self, command):
        self.task_calls.append(command)


class NoDeviceWhileIdleScript(AzurLaneAutoScript):
    def __init__(self, config):
        super().__init__('test')
        self.__dict__['config'] = config
        self.device_accesses = 0

    @property
    def device(self):
        self.device_accesses += 1
        raise AssertionError('Device must stay lazy while no task is due')

    def wait_until(self, future):
        raise StopIteration


class FakeDevice:
    def __init__(self, events):
        self.events = events
        self.screenshot_tracking = []

    def screenshot(self):
        self.events.append('screenshot')

    def release_during_wait(self):
        self.events.append('release-device')

    def emulator_stop(self):
        self.events.append('stop-emulator')
        return True


class CachedDeviceScript(AzurLaneAutoScript):
    def __init__(self, config, device, events):
        super().__init__('test')
        self.__dict__['config'] = config
        self.__dict__['device'] = device
        self.events = events

    def stop(self):
        self.events.append('stop-cloud-game')

    def wait_until(self, future):
        raise StopIteration


class SchedulerIdleTest(unittest.TestCase):
    def test_future_task_does_not_initialize_device_or_start_emulator(self):
        """Catches close_emulator evaluating the lazy Device while SRC is idle."""
        future = SimpleNamespace(
            command='Dungeon',
            next_run=datetime.now() + timedelta(hours=1),
        )
        script = NoDeviceWhileIdleScript(SchedulerConfig([future]))

        with patch('module.base.resource.release_resources'):
            with self.assertRaises(StopIteration):
                script.get_next_task()

        self.assertEqual(script.device_accesses, 0)

    def test_pending_batch_keeps_one_device_then_idle_cleanup_is_idempotent(self):
        """Catches stopping between pending tasks or stopping the same AVD twice."""
        now = datetime.now()
        config = SchedulerConfig([
            SimpleNamespace(command='Dungeon', next_run=now - timedelta(seconds=2)),
            SimpleNamespace(command='Assignment', next_run=now - timedelta(seconds=1)),
            SimpleNamespace(command='DailyQuest', next_run=now + timedelta(hours=1)),
        ])
        events = []
        device = FakeDevice(events)
        script = CachedDeviceScript(config, device, events)

        self.assertEqual(script.get_next_task(), 'Dungeon')
        self.assertIs(script._get_existing_device(), device)
        self.assertEqual(script.get_next_task(), 'Assignment')
        self.assertIs(script._get_existing_device(), device)
        self.assertEqual(events, [])

        with patch('module.base.resource.release_resources'):
            with self.assertRaises(StopIteration):
                script.get_next_task()
            script._close_emulator_for_wait()

        self.assertEqual(
            events,
            ['screenshot', 'stop-cloud-game', 'release-device', 'stop-emulator'],
        )
        self.assertIsNone(script._get_existing_device())


class DeviceInitializationCleanupTest(unittest.TestCase):
    def test_failure_after_avd_start_stops_partially_initialized_device(self):
        """Catches an AVD leak when Device setup fails after Connection succeeds."""
        events = []
        config = SimpleNamespace()

        def platform_init(device, *args, **kwargs):
            passed_config = kwargs.get('config', args[0] if args else None)
            device.config = passed_config
            device.linux_avd_managed = True
            device.linux_avd = SimpleNamespace(
                settings=SimpleNamespace(enabled=True),
                stop=lambda: events.append('stop-emulator') or True,
            )

        with patch.object(PlatformLinux, '__init__', autospec=True, side_effect=platform_init), \
                patch.object(Device, 'screenshot_interval_set', side_effect=RuntimeError('setup failed')):
            with self.assertRaisesRegex(RuntimeError, 'setup failed'):
                Device(config=config)

        self.assertEqual(events, ['stop-emulator'])


class SchedulerExitCleanupTest(unittest.TestCase):
    def test_exception_and_system_exit_cleanup_cached_avd_once(self):
        """Catches recoverable SRC exits bypassing cloud and emulator cleanup."""
        for failure in (RuntimeError('task failed'), SystemExit(1)):
            with self.subTest(failure=type(failure).__name__):
                events = []
                device = FakeDevice(events)
                script = CachedDeviceScript(SimpleNamespace(), device, events)
                script.__dict__['checker'] = SimpleNamespace(
                    wait_until_available=lambda: None,
                    is_recovered=lambda: False,
                )

                def fail_before_task():
                    raise failure

                script.get_next_task = fail_before_task
                with patch('module.base.resource.release_resources'):
                    with self.assertRaises(type(failure)):
                        script.loop()

                self.assertEqual(
                    events,
                    ['screenshot', 'stop-cloud-game', 'release-device', 'stop-emulator'],
                )
                self.assertIsNone(script._get_existing_device())

    def test_sigterm_is_converted_to_system_exit_so_finally_can_cleanup(self):
        """Catches SIGTERM bypassing Python cleanup before ProcessManager's grace expires."""
        events = []
        installed = {}
        previous_handler = object()
        script = CachedDeviceScript(SimpleNamespace(), FakeDevice(events), events)

        def scheduler_loop():
            handler = installed.get('handler')
            if handler is None:
                raise AssertionError('SIGTERM handler was not installed')
            handler(signal.SIGTERM, None)

        def install_handler(signum, handler):
            if callable(handler):
                installed['handler'] = handler
            else:
                installed['restored'] = handler

        script._scheduler_loop = scheduler_loop
        with patch('signal.getsignal', return_value=previous_handler), \
                patch('signal.signal', side_effect=install_handler), \
                patch('module.base.resource.release_resources'):
            with self.assertRaises(SystemExit):
                script.loop()

        self.assertIs(installed.get('restored'), previous_handler)
        self.assertEqual(
            events,
            ['screenshot', 'stop-cloud-game', 'release-device', 'stop-emulator'],
        )

    def test_cloud_stop_system_exit_still_stops_avd_then_propagates(self):
        """Catches cloud-stop failure bypassing the lower-level AVD cleanup."""
        events = []
        script = CachedDeviceScript(SimpleNamespace(), FakeDevice(events), events)

        def stop_then_exit():
            events.append('stop-cloud-game')
            raise SystemExit(7)

        script.stop = stop_then_exit
        with patch('module.base.resource.release_resources', side_effect=lambda: events.append('release')):
            with self.assertRaisesRegex(SystemExit, '7'):
                script._close_emulator_for_wait()

        self.assertEqual(
            events,
            ['screenshot', 'stop-cloud-game', 'release', 'release-device', 'stop-emulator'],
        )
        self.assertIsNone(script._get_existing_device())


class FakeManagedProcess:
    def __init__(self, exits_on_terminate):
        self.exits_on_terminate = exits_on_terminate
        self.running = True
        self.terminate_calls = 0
        self.join_timeouts = []
        self.kill_calls = 0

    def is_alive(self):
        return self.running

    def terminate(self):
        self.terminate_calls += 1
        if self.exits_on_terminate:
            self.running = False

    def join(self, timeout=None):
        self.join_timeouts.append(timeout)

    def kill(self):
        self.kill_calls += 1
        self.running = False


class ProcessManagerCleanupTest(unittest.TestCase):
    def test_linux_manual_stop_uses_sigterm_grace_before_sigkill(self):
        """Catches manual stop using uncatchable SIGKILL before AVD cleanup."""
        for exits_on_terminate in (True, False):
            with self.subTest(exits_on_terminate=exits_on_terminate):
                manager = object.__new__(ProcessManager)
                manager.config_name = 'test'
                manager._process_locks = {}
                manager.thd_log_queue_handler = None
                manager.renderables = []
                process = FakeManagedProcess(exits_on_terminate)
                manager._process = process

                manager.stop()

                self.assertEqual(process.terminate_calls, 1)
                self.assertEqual(len(process.join_timeouts), 1)
                self.assertGreater(process.join_timeouts[0], 0)
                self.assertEqual(process.kill_calls, 0 if exits_on_terminate else 1)


if __name__ == '__main__':
    unittest.main()
