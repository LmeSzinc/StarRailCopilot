import unittest
import signal
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

from module.alas import AzurLaneAutoScript
from module.device.device import Device
from module.device.platform.platform_linux import PlatformLinux
from module.exception import RequestHumanTakeover
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
    def __init__(self, events, linux_avd_managed=True, stop_result=True):
        self.events = events
        self.screenshot_tracking = []
        self.linux_avd_managed = linux_avd_managed
        self.stop_result = stop_result

    def screenshot(self):
        self.events.append('screenshot')

    def release_during_wait(self):
        self.events.append('release-device')

    def emulator_stop(self):
        self.events.append('stop-emulator')
        return self.stop_result


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

    def test_non_linux_close_emulator_keeps_the_upstream_device_path(self):
        """Catches Linux lazy-device behavior leaking into other platforms."""
        future = SimpleNamespace(
            command='Dungeon',
            next_run=datetime.now() + timedelta(hours=1),
        )
        events = []
        device = FakeDevice(events)
        script = CachedDeviceScript(SchedulerConfig([future]), device, events)

        with patch('module.alas.IS_LINUX', False), \
                patch('module.base.resource.release_resources'):
            with self.assertRaises(StopIteration):
                script.get_next_task()

        self.assertEqual(
            events,
            ['screenshot', 'stop-cloud-game', 'release-device', 'stop-emulator'],
        )
        self.assertIs(script._get_existing_device(), device)

    def test_linux_non_avd_device_keeps_the_upstream_device_path(self):
        """Catches Linux physical/network devices entering AVD cleanup."""
        future = SimpleNamespace(
            command='Dungeon',
            next_run=datetime.now() + timedelta(hours=1),
        )
        events = []
        device = FakeDevice(events, linux_avd_managed=False)
        script = CachedDeviceScript(SchedulerConfig([future]), device, events)

        with patch('module.base.resource.release_resources'):
            with self.assertRaises(StopIteration):
                script.get_next_task()

        self.assertEqual(
            events,
            ['screenshot', 'stop-cloud-game', 'release-device', 'stop-emulator'],
        )
        self.assertIs(script._get_existing_device(), device)

    def test_non_linux_loop_does_not_run_linux_exit_cleanup(self):
        """Catches scheduler-finally behavior changing Windows or macOS."""
        script = AzurLaneAutoScript('test')
        script._scheduler_loop = Mock(return_value='finished')
        script._close_emulator_for_wait = Mock(
            side_effect=AssertionError('Linux cleanup must not run')
        )

        with patch('module.alas.IS_LINUX', False):
            self.assertEqual(script.loop(), 'finished')

        script._close_emulator_for_wait.assert_not_called()

    def test_linux_non_avd_loop_does_not_run_avd_exit_cleanup(self):
        """Catches physical/network devices entering the AVD-only loop wrapper."""
        events = []
        script = CachedDeviceScript(
            SimpleNamespace(EmulatorInfo_Emulator='auto'),
            FakeDevice(events, linux_avd_managed=False),
            events,
        )
        script._scheduler_loop = Mock(return_value='finished')
        script._close_emulator_for_wait = Mock(
            side_effect=AssertionError('AVD cleanup must not run')
        )

        self.assertEqual(script.loop(), 'finished')

        script._close_emulator_for_wait.assert_not_called()

    def test_linux_loop_cleans_avd_enabled_after_scheduler_start(self):
        """Catches a runtime config switch bypassing the scheduler exit cleanup."""
        events = []
        script = CachedDeviceScript(
            SimpleNamespace(EmulatorInfo_Emulator='auto'),
            FakeDevice(events, linux_avd_managed=False),
            events,
        )

        def scheduler_loop():
            script.__dict__['device'].linux_avd_managed = True
            raise RuntimeError('task failed after enabling AVD')

        script._scheduler_loop = scheduler_loop
        with patch('module.base.resource.release_resources'):
            with self.assertRaisesRegex(RuntimeError, 'task failed after enabling AVD'):
                script.loop()

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

    def test_partial_device_cleanup_preserves_system_exit_from_initialization(self):
        """Catches cleanup replacing the primary SystemExit with a stop failure."""
        config = SimpleNamespace()

        def platform_init(device, *args, **kwargs):
            device.config = kwargs.get('config', args[0] if args else None)
            device.linux_avd_managed = True

        with patch.object(PlatformLinux, '__init__', autospec=True, side_effect=platform_init), \
                patch.object(Device, 'screenshot_interval_set', side_effect=SystemExit(11)), \
                patch.object(Device, 'emulator_stop', side_effect=KeyboardInterrupt()):
            with self.assertRaisesRegex(SystemExit, '11'):
                Device(config=config)

    def test_android_avd_is_rejected_before_device_init_on_non_linux(self):
        """Catches a Linux-only emulator option entering another platform backend."""
        config = SimpleNamespace(EmulatorInfo_Emulator='AndroidAVD')

        with patch('module.device.device.IS_LINUX', False), \
                patch.object(Device, '_initialize') as initialize:
            with self.assertRaises(RequestHumanTakeover):
                Device(config=config)

        initialize.assert_not_called()


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

    def test_direct_web_task_system_exit_still_cleans_the_avd(self):
        """Catches Web tool tasks bypassing loop() and its SIGTERM cleanup."""
        events = []

        class DirectTaskScript(CachedDeviceScript):
            def daemon(self):
                events.append('daemon')
                raise SystemExit(9)

        previous_handler = object()
        installed = []
        script = DirectTaskScript(
            SimpleNamespace(),
            FakeDevice(events),
            events,
        )

        with patch('signal.getsignal', return_value=previous_handler), \
                patch('signal.signal', side_effect=lambda signum, handler: installed.append(handler)), \
                patch('module.base.resource.release_resources'):
            with self.assertRaisesRegex(SystemExit, '9'):
                script.run_single_task('daemon')

        self.assertIs(installed[-1], previous_handler)
        self.assertEqual(
            events,
            [
                'screenshot',
                'daemon',
                'screenshot',
                'stop-cloud-game',
                'release-device',
                'stop-emulator',
            ],
        )
        self.assertIsNone(script._get_existing_device())

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

    def test_failed_avd_shutdown_is_retained_and_retried_on_scheduler_exit(self):
        """Catches an AVD stop failure being forgotten before the idle wait."""
        future = SimpleNamespace(
            command='Dungeon',
            next_run=datetime.now() + timedelta(hours=1),
        )
        events = []
        device = FakeDevice(events, stop_result=False)
        script = CachedDeviceScript(SchedulerConfig([future]), device, events)
        script.__dict__['checker'] = SimpleNamespace(
            wait_until_available=lambda: None,
            is_recovered=lambda: False,
        )

        with patch('module.base.resource.release_resources'):
            with self.assertRaises(RequestHumanTakeover):
                script.loop()

        self.assertIs(script._get_existing_device(), device)
        self.assertEqual(events.count('stop-emulator'), 2)

    def test_linux_non_avd_direct_task_keeps_upstream_exit_behavior(self):
        """Catches Web tools stopping a physical/network device after completion."""
        events = []

        class DirectTaskScript(CachedDeviceScript):
            def daemon(self):
                events.append('daemon')

        device = FakeDevice(events, linux_avd_managed=False)
        script = DirectTaskScript(
            SimpleNamespace(EmulatorInfo_Emulator='auto'),
            device,
            events,
        )

        self.assertTrue(script.run_single_task('daemon'))

        self.assertEqual(events, ['screenshot', 'daemon'])
        self.assertIs(script._get_existing_device(), device)


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

                with patch(
                    'module.webui.process_manager.load_config',
                    return_value=SimpleNamespace(
                        EmulatorInfo_Emulator='AndroidAVD',
                        LinuxAVD_StopTimeout=1,
                    ),
                ):
                    manager.stop()

                self.assertEqual(process.terminate_calls, 1)
                self.assertEqual(len(process.join_timeouts), 1)
                self.assertGreater(process.join_timeouts[0], 0)
                self.assertEqual(process.kill_calls, 0 if exits_on_terminate else 1)

    def test_linux_non_avd_manual_stop_keeps_upstream_kill_behavior(self):
        """Catches AVD SIGTERM grace leaking into other Linux device types."""
        manager = object.__new__(ProcessManager)
        manager.config_name = 'test'
        manager._process_locks = {}
        manager.thd_log_queue_handler = None
        manager.renderables = []
        process = FakeManagedProcess(exits_on_terminate=True)
        manager._process = process

        with patch(
            'module.webui.process_manager.load_config',
            return_value=SimpleNamespace(EmulatorInfo_Emulator='auto'),
        ):
            manager.stop()

        self.assertEqual(process.terminate_calls, 0)
        self.assertEqual(process.join_timeouts, [])
        self.assertEqual(process.kill_calls, 1)

    def test_linux_manual_stop_grace_covers_configured_avd_shutdown(self):
        """Catches the parent force-killing cleanup before StopTimeout expires."""
        manager = object.__new__(ProcessManager)
        manager.config_name = 'test'
        manager._process_locks = {}
        manager.thd_log_queue_handler = None
        manager.renderables = []
        process = FakeManagedProcess(exits_on_terminate=True)
        manager._process = process

        config = SimpleNamespace(
            EmulatorInfo_Emulator='AndroidAVD',
            LinuxAVD_StopTimeout=60,
        )
        with patch('module.webui.process_manager.load_config', return_value=config):
            manager.stop()

        self.assertEqual(process.join_timeouts, [85])


if __name__ == '__main__':
    unittest.main()
