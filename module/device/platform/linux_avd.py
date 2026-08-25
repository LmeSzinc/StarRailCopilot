import os
import signal
import subprocess
import time

from module.device.platform.linux_avd_settings import LinuxAVDSettings, LinuxAVDStartError
from module.logger import logger


class LinuxAVDLifecycle:
    """Start, verify, adopt, and stop one configured Linux Android AVD."""

    def __init__(
            self,
            config,
            runner=None,
            popen=None,
            process_iter=None,
            monotonic=None,
            sleeper=None,
            poll_interval=1.0,
            logger_instance=None,
    ):
        """Create an injectable AVD lifecycle controller.

        Args:
            config: SRC configuration containing emulator and Linux AVD options.
            runner: Optional subprocess-compatible command runner.
            popen: Optional subprocess-compatible process launcher.
            process_iter: Optional iterator for host processes.
            monotonic: Optional monotonic clock callable.
            sleeper: Optional sleep callable used between readiness checks.
            poll_interval (float): Maximum seconds between readiness checks.
            logger_instance: Optional logger-compatible object.
        """
        self.settings = LinuxAVDSettings.from_config(config)
        self._runner = runner or self._run_command
        self._popen = popen or self._start_process
        self._process_iter = process_iter or self._iter_processes
        self._monotonic = monotonic or time.monotonic
        self._sleep = sleeper or time.sleep
        self.poll_interval = float(poll_interval)
        self._logger = logger_instance or logger
        self._started_at = 0.0
        self._last_result = None
        self._launched_process = None
        self._launched_process_group = None

    @staticmethod
    def _run_command(command, timeout):
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

    @staticmethod
    def _start_process(command, **kwargs):
        return subprocess.Popen(command, **kwargs)

    @staticmethod
    def _iter_processes():
        import psutil
        return psutil.process_iter(['pid', 'cmdline'])

    @staticmethod
    def _process_cmdline(process):
        try:
            info = getattr(process, 'info', {})
            command = info.get('cmdline') if isinstance(info, dict) else None
            if command is None:
                command = process.cmdline()
            return [str(item) for item in command or []]
        except Exception:
            return []

    def matching_processes(self):
        """Find exact host processes for the configured AVD and console port.

        Returns:
            list: Matching emulator or QEMU process objects.
        """
        matches = []
        for process in self._process_iter():
            command = self._process_cmdline(process)
            if not self._is_android_emulator_process(command):
                continue
            avd_match = self._option_matches(command, '-avd', self.settings.name) \
                or f'@{self.settings.name}' in command
            port_match = self._option_matches(command, '-port', str(self.settings.console_port))
            if avd_match and port_match:
                matches.append(process)
        return matches

    def _is_android_emulator_process(self, command):
        if not command:
            return False

        executable = os.path.realpath(command[0])
        configured = os.path.realpath(self.settings.emulator_path)
        executable_name = os.path.basename(executable)
        configured_name = os.path.basename(configured)
        if executable_name == configured_name:
            return not os.path.isabs(self.settings.emulator_path) or executable == configured

        if not executable_name.startswith('qemu-system-'):
            return False
        if not os.path.isabs(self.settings.emulator_path):
            return True
        try:
            return os.path.commonpath([executable, os.path.dirname(configured)]) \
                == os.path.dirname(configured)
        except ValueError:
            return False

    @staticmethod
    def _option_matches(command, option, value):
        for index, item in enumerate(command[:-1]):
            if item == option and command[index + 1] == value:
                return True
        return False

    def _remaining(self, deadline):
        return max(deadline - self._monotonic(), 0.0)

    def _call(self, command, deadline):
        remaining = self._remaining(deadline)
        if remaining <= 0:
            return None
        try:
            result = self._runner(command, timeout=min(5.0, remaining))
        except (OSError, subprocess.SubprocessError) as error:
            self._last_result = error
            return None
        self._last_result = result
        return result

    @staticmethod
    def _stdout(result):
        if result is None:
            return ''
        output = getattr(result, 'stdout', '')
        return output.decode(errors='replace') if isinstance(output, bytes) else str(output)

    def _wait_for(self, phase, predicate, deadline):
        """Poll one readiness predicate until it succeeds or the deadline expires.

        Args:
            phase (str): Human-readable readiness phase.
            predicate: Callable returning whether the phase is ready.
            deadline (float): Absolute monotonic startup deadline.

        Raises:
            LinuxAVDStartError: If the shared startup deadline expires.
        """
        self._logger.info(f'Linux AVD waiting for {phase}')
        while True:
            if predicate():
                elapsed = self._monotonic() - self._started_at
                self._logger.info(f'Linux AVD {phase} ready after {elapsed:.1f}s')
                return
            if self._remaining(deadline) <= 0:
                error = LinuxAVDStartError(phase, self._monotonic() - self._started_at)
                self._logger.error(str(error))
                raise error
            self._sleep(min(self.poll_interval, self._remaining(deadline)))

    def _adb(self, *arguments):
        return [self.settings.adb_path, '-s', self.settings.serial, *arguments]

    def _serial_online(self, deadline):
        result = self._call(self._adb('get-state'), deadline)
        return self._command_succeeded(result) \
            and self._stdout(result).strip() == 'device'

    @staticmethod
    def _command_succeeded(result):
        return result is not None and getattr(result, 'returncode', 1) == 0

    def _launch_or_adopt(self):
        """Launch a missing AVD, or adopt an exact existing instance.

        Raises:
            OSError: If the emulator process cannot be launched.
        """
        if self.matching_processes():
            self._logger.info(
                f'Linux AVD {self.settings.name!r} is already running; adopting it'
            )
            return

        command = self.settings.launch_command()
        self._logger.info(
            f'Linux AVD launching {self.settings.name!r} on {self.settings.serial}: {command}'
        )
        self._launched_process = self._popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            close_fds=True,
            start_new_session=True,
        )
        self._launched_process_group = getattr(self._launched_process, 'pid', None)

    def _wait_until_ready(self, deadline):
        """Verify all startup gates in their required order.

        Args:
            deadline (float): Absolute monotonic startup deadline shared by all gates.

        Raises:
            LinuxAVDStartError: If any readiness gate exceeds the deadline.
        """
        checks = (
            ('process', lambda: bool(self.matching_processes())),
            ('adb_serial', lambda: self._serial_online(deadline)),
            ('boot_completed', lambda: self._boot_completed(deadline)),
            ('adb_shell', lambda: self._adb_shell_ready(deadline)),
            ('package_manager', lambda: self._package_manager_ready(deadline)),
        )
        for phase, predicate in checks:
            self._wait_for(phase, predicate, deadline)

    def _boot_completed(self, deadline):
        result = self._call(
            self._adb('shell', 'getprop', 'sys.boot_completed'),
            deadline,
        )
        return self._command_succeeded(result) and self._stdout(result).strip() == '1'

    def _adb_shell_ready(self, deadline):
        result = self._call(
            self._adb('shell', 'echo', 'src-avd-ready'),
            deadline,
        )
        return self._command_succeeded(result) \
            and self._stdout(result).strip() == 'src-avd-ready'

    def _package_manager_ready(self, deadline):
        result = self._call(
            self._adb('shell', 'pm', 'path', 'android'),
            deadline,
        )
        return self._command_succeeded(result) \
            and self._stdout(result).strip().startswith('package:')

    def _cleanup_failed_start(self, error):
        """Attempt shutdown while preserving the original startup exception.

        Args:
            error (BaseException): Startup error that will be re-raised by start().
        """
        if not isinstance(error, LinuxAVDStartError):
            self._logger.error(f'Linux AVD startup failed: {error}')
        self._logger.warning('Linux AVD startup failed; attempting cleanup')
        try:
            self.stop()
        except BaseException as cleanup_error:
            self._logger.error(f'Linux AVD startup cleanup failed: {cleanup_error}')

    def start(self):
        """Start or adopt the configured AVD and wait for all readiness gates.

        Returns:
            bool: True when lifecycle management is disabled or the AVD is ready.

        Raises:
            LinuxAVDStartError: If the shared startup deadline expires.
            BaseException: Re-raises launch and interruption errors after cleanup.
        """
        if not self.settings.enabled:
            return True

        self._started_at = self._monotonic()
        deadline = self._started_at + self.settings.start_timeout
        try:
            self._launch_or_adopt()
            self._wait_until_ready(deadline)
        except BaseException as error:
            self._cleanup_failed_start(error)
            raise

        elapsed = self._monotonic() - self._started_at
        self._logger.info(f'Linux AVD startup completed after {elapsed:.1f}s')
        return True

    def stop(self):
        """Stop the configured AVD and wait for its serial and exact process to disappear.

        Returns:
            bool: True when the AVD is fully stopped or management is disabled.
        """
        if not self.settings.enabled:
            return True

        self._logger.info(
            f'Linux AVD shutdown requested for {self.settings.name!r} on {self.settings.serial}'
        )
        deadline = self._monotonic() + self.settings.stop_timeout
        if self._is_stopped(deadline):
            return self._finish_shutdown('Linux AVD is already stopped')
        owns_process = bool(self.matching_processes()) or self._launched_process_alive()
        serial_online = self._serial_online(deadline)
        if serial_online and owns_process:
            self._logger.info('Linux AVD sending adb emu kill')
            self._call(self._adb('emu', 'kill'), deadline)
        elif serial_online:
            self._logger.warning(
                'Linux AVD serial is online without the configured exact process; '
                'refusing adb emu kill'
            )
        if self._wait_for_shutdown(deadline):
            return self._finish_shutdown('Linux AVD process and ADB serial disappeared')
        return self._force_stop()

    def _force_stop(self):
        """Escalate from SIGTERM to SIGKILL with bounded waits.

        Returns:
            bool: True if an escalation phase completely stops the AVD.
        """
        force_wait = min(max(self.settings.stop_timeout / 2, self.poll_interval), 10.0)
        phases = (
            (
                signal.SIGTERM,
                'terminate',
                'Linux AVD graceful shutdown timed out; sending SIGTERM',
                'Linux AVD stopped after SIGTERM',
            ),
            (
                signal.SIGKILL,
                'kill',
                'Linux AVD SIGTERM timed out; sending SIGKILL',
                'Linux AVD stopped after SIGKILL',
            ),
        )
        for signum, method, warning, success in phases:
            self._logger.warning(warning)
            self._signal_matching_processes(signum, method)
            if self._wait_for_shutdown(self._monotonic() + force_wait):
                return self._finish_shutdown(success)

        self._logger.error('Linux AVD shutdown failed: process or ADB serial is still present')
        return False

    def _finish_shutdown(self, message):
        """Clear tracked process state after a verified shutdown."""
        self._logger.info(message)
        self._clear_launched_process()
        return True

    def _is_stopped(self, deadline):
        """Check all process and ADB conditions without waiting."""
        return not self.matching_processes() \
            and not self._serial_online(deadline) \
            and not self._launched_process_alive()

    def _clear_launched_process(self):
        process = self._launched_process
        poll = getattr(process, 'poll', None)
        if callable(poll):
            try:
                poll()
            except OSError:
                pass
        self._launched_process = None
        self._launched_process_group = None

    def _signal_matching_processes(self, signum, method):
        """Signal the launched emulator session, or exact adopted processes.

        Args:
            signum (int): POSIX signal for a process group started by this controller.
            method (str): Equivalent psutil process method for adopted instances.
        """
        processes = self.matching_processes()
        process_group = self._launched_process_group
        if self._matching_process_uses_group(processes, process_group):
            try:
                os.killpg(process_group, signum)
                return
            except OSError:
                pass

        for process in processes:
            try:
                getattr(process, method)()
            except (OSError, RuntimeError):
                continue

    def _launched_process_alive(self):
        poll = getattr(self._launched_process, 'poll', None)
        if not callable(poll):
            return False
        try:
            return poll() is None
        except OSError:
            return False

    def _matching_process_uses_group(self, processes, process_group):
        """Check that a remembered process group still belongs to this AVD.

        Args:
            processes (list): Exact AVD processes visible on the host.
            process_group (int or None): Remembered launcher process group.

        Returns:
            bool: True if signaling the complete group is still safe.
        """
        if process_group is None or process_group in (os.getpid(), os.getpgrp()):
            return False
        launched_pid = getattr(self._launched_process, 'pid', None)
        if launched_pid == process_group and self._launched_process_alive():
            try:
                return os.getpgid(launched_pid) == process_group
            except OSError:
                pass
        for process in processes:
            try:
                if os.getpgid(process.pid) == process_group:
                    return True
            except OSError:
                continue
        return False

    def _wait_for_shutdown(self, deadline):
        """Poll until all exact process and ADB shutdown conditions are met.

        Args:
            deadline (float): Absolute monotonic shutdown deadline.

        Returns:
            bool: True only when the serial and every tracked process disappear.
        """
        while self._monotonic() < deadline:
            if self._is_stopped(deadline):
                return True
            self._sleep(min(self.poll_interval, self._remaining(deadline)))
        return False
