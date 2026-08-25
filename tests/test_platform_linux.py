import unittest
import signal
from subprocess import CompletedProcess
from types import SimpleNamespace
from unittest.mock import patch

from module.device.platform.platform_linux import (
    LinuxAVDConfigurationError,
    LinuxAVDLifecycle,
    LinuxAVDSettings,
    LinuxAVDStartError,
)


class LinuxAVDSettingsTest(unittest.TestCase):
    @staticmethod
    def config(**overrides):
        values = dict(
            EmulatorInfo_Emulator='AndroidAVD',
            EmulatorInfo_name='src-cloud',
            EmulatorInfo_path='/opt/android-sdk/emulator/emulator',
            Emulator_Serial='emulator-5554',
            LinuxAVD_SDKRoot='/opt/android-sdk',
            LinuxAVD_AdbPath='/opt/android-sdk/platform-tools/adb',
            LinuxAVD_MemoryMB=2048,
            LinuxAVD_GPU='host',
            LinuxAVD_Headless=True,
            LinuxAVD_StartTimeout=300,
            LinuxAVD_StopTimeout=60,
        )
        values.update(overrides)
        return SimpleNamespace(**values)

    def test_launch_command_uses_configured_low_memory_host_gpu_without_destructive_flags(self):
        """Catches ignored AVD, port, RAM, GPU, or persistent-data settings."""
        config = self.config()

        settings = LinuxAVDSettings.from_config(config)

        self.assertEqual(
            settings.launch_command(),
            [
                '/opt/android-sdk/emulator/emulator',
                '-avd',
                'src-cloud',
                '-port',
                '5554',
                '-memory',
                '2048',
                '-gpu',
                'host',
                '-no-metrics',
                '-no-window',
                '-no-audio',
            ],
        )
        destructive = {'-wipe-data', '-data', '-no-snapshot-save'}
        self.assertTrue(destructive.isdisjoint(settings.launch_command()))

    def test_invalid_serial_memory_name_and_timeout_are_rejected(self):
        """Catches unsafe ambiguous serials and emulator arguments."""
        invalid = [
            {'Emulator_Serial': '127.0.0.1:5555'},
            {'Emulator_Serial': 'emulator-5555'},
            {'Emulator_Serial': 'emulator-5684'},
            {'LinuxAVD_MemoryMB': 1024},
            {'LinuxAVD_MemoryMB': 8193},
            {'EmulatorInfo_name': ''},
            {'EmulatorInfo_name': '../src-cloud'},
            {'EmulatorInfo_name': 'src cloud'},
            {'EmulatorInfo_name': '..'},
            {'EmulatorInfo_name': '-wipe-data'},
            {'LinuxAVD_GPU': ''},
            {'LinuxAVD_StartTimeout': 0},
            {'LinuxAVD_StopTimeout': -1},
            {'LinuxAVD_StartTimeout': float('nan')},
            {'LinuxAVD_StopTimeout': float('inf')},
            {'LinuxAVD_MemoryMB': 'not-a-number'},
            {'LinuxAVD_StartTimeout': 'not-a-number'},
        ]

        for overrides in invalid:
            with self.subTest(overrides=overrides):
                with self.assertRaises(LinuxAVDConfigurationError):
                    LinuxAVDSettings.from_config(self.config(**overrides))

    def test_non_avd_linux_configuration_is_not_validated_or_managed(self):
        """Catches the Linux platform breaking physical and non-AVD devices."""
        config = SimpleNamespace(
            EmulatorInfo_Emulator='auto',
            EmulatorInfo_name='',
            EmulatorInfo_path='',
            Emulator_Serial='127.0.0.1:5555',
        )

        settings = LinuxAVDSettings.from_config(config)

        self.assertFalse(settings.enabled)


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class FakeProcess:
    def __init__(self, pid=321, command=None, on_terminate=None, on_kill=None):
        self.pid = pid
        self.terminate_calls = 0
        self.kill_calls = 0
        self._on_terminate = on_terminate
        self._on_kill = on_kill
        self.info = {
            'pid': pid,
            'cmdline': command or [
                '/opt/android-sdk/emulator/emulator',
                '-avd',
                'src-cloud',
                '-port',
                '5554',
            ],
        }

    def terminate(self):
        self.terminate_calls += 1
        if self._on_terminate is not None:
            self._on_terminate()

    def kill(self):
        self.kill_calls += 1
        if self._on_kill is not None:
            self._on_kill()


class FakeAndroidBoundary:
    def __init__(self, running=False, boot_outputs=None):
        self.running = running
        self.serial_online = running
        self.process = FakeProcess()
        self.boot_outputs = list(boot_outputs or ['1'])
        self.launches = []
        self.commands = []

    def process_iter(self):
        return [self.process] if self.running else []

    def popen(self, command, **kwargs):
        self.launches.append((list(command), kwargs))
        self.running = True
        self.serial_online = True
        return self.process

    def run(self, command, timeout):
        command = list(command)
        self.commands.append(command)
        if command[-2:] == ['getprop', 'sys.boot_completed']:
            output = self.boot_outputs.pop(0) if self.boot_outputs else ''
        elif command[-2:] == ['echo', 'src-avd-ready']:
            output = 'src-avd-ready'
        elif command[-3:] == ['pm', 'path', 'android']:
            output = 'package:/system/framework/framework-res.apk'
        elif command[-2:] == ['emu', 'kill']:
            self.running = False
            self.serial_online = False
            output = 'OK'
        elif command[-1:] == ['get-state']:
            output = 'device' if self.serial_online else ''
        else:
            output = ''
        return CompletedProcess(command, 0 if output else 1, stdout=output, stderr='')


class FakeLogger:
    def __init__(self):
        self.records = []

    def info(self, message):
        self.records.append(('info', str(message)))

    def warning(self, message):
        self.records.append(('warning', str(message)))

    def error(self, message):
        self.records.append(('error', str(message)))


class LinuxAVDLifecycleStartTest(unittest.TestCase):
    @staticmethod
    def lifecycle(boundary, clock=None, **config_overrides):
        clock = clock or FakeClock()
        config = LinuxAVDSettingsTest.config(**config_overrides)
        return LinuxAVDLifecycle(
            config,
            runner=boundary.run,
            popen=boundary.popen,
            process_iter=boundary.process_iter,
            monotonic=clock.monotonic,
            sleeper=clock.sleep,
            poll_interval=0.1,
        )

    def test_stopped_avd_launches_then_checks_adb_boot_shell_and_package_manager_in_order(self):
        """Catches skipped/reordered readiness gates or a duplicate launch."""
        boundary = FakeAndroidBoundary(running=False)
        lifecycle = self.lifecycle(boundary)

        self.assertTrue(lifecycle.start())

        self.assertEqual(len(boundary.launches), 1)
        self.assertEqual(
            [command[3:] for command in boundary.commands],
            [
                ['get-state'],
                ['shell', 'getprop', 'sys.boot_completed'],
                ['shell', 'echo', 'src-avd-ready'],
                ['shell', 'pm', 'path', 'android'],
            ],
        )

    def test_running_avd_is_adopted_without_duplicate_launch(self):
        """Catches launching a second emulator for an already-running target."""
        boundary = FakeAndroidBoundary(running=True)
        lifecycle = self.lifecycle(boundary)

        self.assertTrue(lifecycle.start())

        self.assertEqual(boundary.launches, [])

    def test_boot_timeout_reports_phase_and_attempts_cleanup(self):
        """Catches an unbounded boot wait or a timed-out emulator left running."""
        boundary = FakeAndroidBoundary(running=False, boot_outputs=['', '', '', ''])
        lifecycle = self.lifecycle(
            boundary,
            LinuxAVD_StartTimeout=0.25,
            LinuxAVD_StopTimeout=0.2,
        )

        with self.assertRaises(LinuxAVDStartError) as caught:
            lifecycle.start()

        self.assertEqual(caught.exception.phase, 'boot_completed')
        self.assertIn(
            ['/opt/android-sdk/platform-tools/adb', '-s', 'emulator-5554', 'emu', 'kill'],
            boundary.commands,
        )
        self.assertFalse(boundary.running)

    def test_readiness_phases_and_timeout_cleanup_are_logged(self):
        """Catches opaque startup failures with no phase or cleanup evidence."""
        boundary = FakeAndroidBoundary(running=False, boot_outputs=['', '', '', ''])
        clock = FakeClock()
        fake_logger = FakeLogger()
        lifecycle = LinuxAVDLifecycle(
            LinuxAVDSettingsTest.config(
                LinuxAVD_StartTimeout=0.25,
                LinuxAVD_StopTimeout=0.2,
            ),
            runner=boundary.run,
            popen=boundary.popen,
            process_iter=boundary.process_iter,
            monotonic=clock.monotonic,
            sleeper=clock.sleep,
            poll_interval=0.1,
            logger_instance=fake_logger,
        )

        with self.assertRaises(LinuxAVDStartError):
            lifecycle.start()

        messages = [message for _, message in fake_logger.records]
        self.assertTrue(any('process' in message for message in messages))
        self.assertTrue(any('adb_serial' in message for message in messages))
        self.assertTrue(any('boot_completed' in message for message in messages))
        self.assertTrue(any('timed out' in message for message in messages))
        self.assertTrue(any('cleanup' in message.lower() for message in messages))


class StopBoundary:
    def __init__(self, kill_result='both'):
        self.running = True
        self.serial_online = True
        self.kill_result = kill_result
        self.commands = []
        self.sleep_calls = 0
        self.process = FakeProcess(
            on_terminate=self._terminated,
            on_kill=self._killed,
        )
        self.unrelated = FakeProcess(
            pid=999,
            command=['/opt/android-sdk/emulator/emulator', '-avd', 'other', '-port', '5556'],
        )

    def process_iter(self):
        processes = [self.unrelated]
        if self.running:
            processes.append(self.process)
        return processes

    def run(self, command, timeout):
        command = list(command)
        self.commands.append(command)
        if command[-1:] == ['get-state']:
            output = 'device' if self.serial_online else ''
        elif command[-2:] == ['emu', 'kill']:
            if self.kill_result in ('both', 'process'):
                self.running = False
            if self.kill_result in ('both', 'serial'):
                self.serial_online = False
            output = 'OK'
        else:
            output = ''
        return CompletedProcess(command, 0 if output else 1, stdout=output, stderr='')

    def after_sleep(self):
        self.sleep_calls += 1
        if self.kill_result == 'serial' and self.sleep_calls == 1:
            self.running = False
        elif self.kill_result == 'process' and self.sleep_calls == 1:
            self.serial_online = False

    def _terminated(self):
        if self.kill_result == 'term':
            self.running = False
            self.serial_online = False

    def _killed(self):
        self.running = False
        self.serial_online = False


class LinuxAVDLifecycleStopTest(unittest.TestCase):
    @staticmethod
    def lifecycle(boundary, timeout=0.2):
        clock = FakeClock()

        def sleeper(seconds):
            clock.sleep(seconds)
            boundary.after_sleep()

        config = LinuxAVDSettingsTest.config(LinuxAVD_StopTimeout=timeout)
        lifecycle = LinuxAVDLifecycle(
            config,
            runner=boundary.run,
            popen=lambda *args, **kwargs: None,
            process_iter=boundary.process_iter,
            monotonic=clock.monotonic,
            sleeper=sleeper,
            poll_interval=0.1,
        )
        return lifecycle

    def test_already_stopped_is_idempotent(self):
        """Catches shutdown trying to start or signal an absent emulator."""
        boundary = StopBoundary()
        boundary.running = False
        boundary.serial_online = False

        self.assertTrue(self.lifecycle(boundary).stop())
        self.assertFalse(any(command[-2:] == ['emu', 'kill'] for command in boundary.commands))

    def test_graceful_stop_waits_for_both_process_and_serial(self):
        """Catches declaring success when only one shutdown condition disappears."""
        for kill_result in ('both', 'serial', 'process'):
            with self.subTest(kill_result=kill_result):
                boundary = StopBoundary(kill_result=kill_result)

                self.assertTrue(self.lifecycle(boundary).stop())

                self.assertFalse(boundary.running)
                self.assertFalse(boundary.serial_online)
                if kill_result != 'both':
                    self.assertGreater(boundary.sleep_calls, 0)

    def test_timeout_terminates_then_kills_only_the_matching_avd(self):
        """Catches leaked emulator memory or termination of an unrelated AVD."""
        term_boundary = StopBoundary(kill_result='term')
        self.assertTrue(self.lifecycle(term_boundary).stop())
        self.assertEqual(term_boundary.process.terminate_calls, 1)
        self.assertEqual(term_boundary.process.kill_calls, 0)
        self.assertEqual(term_boundary.unrelated.terminate_calls, 0)

        kill_boundary = StopBoundary(kill_result='none')
        self.assertTrue(self.lifecycle(kill_boundary).stop())
        self.assertEqual(kill_boundary.process.terminate_calls, 1)
        self.assertEqual(kill_boundary.process.kill_calls, 1)
        self.assertEqual(kill_boundary.unrelated.kill_calls, 0)

    def test_launched_emulator_fallback_signals_the_complete_process_group(self):
        """Catches a launcher dying while its QEMU child remains alive."""
        boundary = StopBoundary(kill_result='none')
        lifecycle = self.lifecycle(boundary)
        lifecycle._launched_process_group = boundary.process.pid

        def kill_group(process_group, signum):
            self.assertEqual(process_group, boundary.process.pid)
            self.assertEqual(signum, signal.SIGTERM)
            boundary.running = False
            boundary.serial_online = False

        with patch(
            'module.device.platform.linux_avd.os.killpg',
            side_effect=kill_group,
        ) as killpg, patch(
            'module.device.platform.linux_avd.os.getpgid',
            return_value=boundary.process.pid,
        ):
            self.assertTrue(lifecycle.stop())

        killpg.assert_called_once()
        self.assertEqual(boundary.process.terminate_calls, 0)
        self.assertIsNone(lifecycle._launched_process_group)

    def test_reused_process_group_is_not_signaled(self):
        """Catches a stale launcher PID targeting a different process group."""
        boundary = StopBoundary(kill_result='term')
        lifecycle = self.lifecycle(boundary)
        lifecycle._launched_process_group = boundary.process.pid

        with patch(
            'module.device.platform.linux_avd.os.getpgid',
            return_value=boundary.process.pid + 1,
        ), patch('module.device.platform.linux_avd.os.killpg') as killpg:
            self.assertTrue(lifecycle.stop())

        killpg.assert_not_called()
        self.assertEqual(boundary.process.terminate_calls, 1)

    def test_unenumerated_launched_process_is_still_stopped_by_its_group(self):
        """Catches startup cleanup treating an unenumerated Popen as stopped."""
        boundary = StopBoundary(kill_result='none')
        boundary.running = False
        boundary.serial_online = False
        lifecycle = self.lifecycle(boundary)
        launched = SimpleNamespace(pid=4321)
        launched.running = True
        launched.poll = lambda: None if launched.running else 0
        lifecycle._launched_process = launched
        lifecycle._launched_process_group = launched.pid

        def kill_group(process_group, signum):
            self.assertEqual(process_group, launched.pid)
            self.assertEqual(signum, signal.SIGTERM)
            launched.running = False

        with patch(
            'module.device.platform.linux_avd.os.getpgid',
            return_value=launched.pid,
        ), patch(
            'module.device.platform.linux_avd.os.killpg',
            side_effect=kill_group,
        ) as killpg:
            self.assertTrue(lifecycle.stop())

        killpg.assert_called_once()
        self.assertIsNone(lifecycle._launched_process)

    def test_process_matcher_rejects_non_emulator_commands_with_the_same_flags(self):
        """Catches fallback signals targeting an unrelated command line."""
        boundary = StopBoundary()
        boundary.unrelated.info['cmdline'] = [
            '/usr/bin/python3',
            'worker.py',
            '-avd',
            'src-cloud',
            '-port',
            '5554',
        ]
        lifecycle = self.lifecycle(boundary)

        self.assertEqual(lifecycle.matching_processes(), [boundary.process])

    def test_serial_collision_never_kills_an_unrelated_avd(self):
        """Catches startup cleanup killing a different AVD that owns the serial."""
        boundary = StopBoundary(kill_result='none')
        boundary.running = False
        boundary.serial_online = True
        lifecycle = self.lifecycle(boundary)

        self.assertFalse(lifecycle.stop())

        self.assertFalse(any(command[-2:] == ['emu', 'kill'] for command in boundary.commands))
        self.assertEqual(boundary.unrelated.terminate_calls, 0)
        self.assertEqual(boundary.unrelated.kill_calls, 0)


if __name__ == '__main__':
    unittest.main()
