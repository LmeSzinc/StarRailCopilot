import math
import os
import re
from dataclasses import dataclass


class LinuxAVDConfigurationError(ValueError):
    """Raised when a Linux Android Virtual Device setting is unsafe or invalid."""


class LinuxAVDStartError(RuntimeError):
    """Raised when an Android Virtual Device does not become ready in time."""

    def __init__(self, phase, elapsed):
        """
        Args:
            phase (str): Readiness phase that exceeded the startup deadline.
            elapsed (float): Seconds elapsed since startup began.
        """
        self.phase = phase
        self.elapsed = elapsed
        super().__init__(f'Linux AVD startup timed out in phase {phase} after {elapsed:.1f}s')


@dataclass(frozen=True)
class LinuxAVDSettings:
    """Validated settings for one Linux Android Virtual Device."""

    enabled: bool
    name: str
    emulator_path: str
    adb_path: str
    serial: str
    console_port: int
    memory_mb: int
    gpu: str
    headless: bool
    start_timeout: float
    stop_timeout: float

    @classmethod
    def from_config(cls, config):
        """Build Linux AVD settings without validating unrelated device types.

        Args:
            config: SRC configuration containing emulator and Linux AVD options.

        Returns:
            LinuxAVDSettings: Normalized and validated lifecycle settings.

        Raises:
            LinuxAVDConfigurationError: If an enabled AVD setting is invalid.
        """
        enabled = str(getattr(config, 'EmulatorInfo_Emulator', '')).strip() == 'AndroidAVD'
        name = cls._text(getattr(config, 'EmulatorInfo_name', ''))
        sdk_root = cls._text(getattr(config, 'LinuxAVD_SDKRoot', ''))
        emulator_path = cls._resolve_executable(
            cls._text(getattr(config, 'EmulatorInfo_path', '')),
            sdk_root,
            'emulator/emulator',
            'emulator',
        )
        adb_path = cls._resolve_executable(
            cls._text(getattr(config, 'LinuxAVD_AdbPath', '')),
            sdk_root,
            'platform-tools/adb',
            'adb',
        )
        serial = cls._text(getattr(config, 'Emulator_Serial', ''))

        if not enabled:
            return cls._disabled(name, emulator_path, adb_path, serial)

        console_port = cls._console_port(serial)
        memory_mb, start_timeout, stop_timeout = cls._numeric_settings(config)
        gpu = cls._text(getattr(config, 'LinuxAVD_GPU', 'host'))
        if not gpu:
            raise LinuxAVDConfigurationError('Linux AVD GPU mode must not be empty')
        cls._validate_name(name)

        return cls(
            enabled=True,
            name=name,
            emulator_path=emulator_path,
            adb_path=adb_path,
            serial=serial,
            console_port=console_port,
            memory_mb=memory_mb,
            gpu=gpu,
            headless=bool(getattr(config, 'LinuxAVD_Headless', True)),
            start_timeout=start_timeout,
            stop_timeout=stop_timeout,
        )

    @classmethod
    def _disabled(cls, name, emulator_path, adb_path, serial):
        """Return inert settings for physical devices and non-AVD emulators."""
        return cls(
            enabled=False,
            name=name,
            emulator_path=emulator_path,
            adb_path=adb_path,
            serial=serial,
            console_port=0,
            memory_mb=2048,
            gpu='host',
            headless=True,
            start_timeout=300,
            stop_timeout=60,
        )

    @staticmethod
    def _console_port(serial):
        """Validate an emulator serial and return its even console port."""
        match = re.fullmatch(r'emulator-(\d+)', serial)
        if match is None:
            raise LinuxAVDConfigurationError(
                f'Linux AVD serial must look like emulator-5554, got {serial!r}'
            )
        console_port = int(match.group(1))
        if not 5554 <= console_port <= 5682 or console_port % 2:
            raise LinuxAVDConfigurationError(
                f'Linux AVD console port must be even and between 5554 and 5682, got {console_port}'
            )
        return console_port

    @staticmethod
    def _numeric_settings(config):
        """Parse and validate memory and lifecycle timeout values."""
        try:
            memory_mb = int(getattr(config, 'LinuxAVD_MemoryMB', 2048))
            start_timeout = float(getattr(config, 'LinuxAVD_StartTimeout', 300))
            stop_timeout = float(getattr(config, 'LinuxAVD_StopTimeout', 60))
        except (TypeError, ValueError, OverflowError) as error:
            raise LinuxAVDConfigurationError(
                f'Linux AVD numeric settings are invalid: {error}'
            ) from error
        if not 1536 <= memory_mb <= 8192:
            raise LinuxAVDConfigurationError(
                f'Linux AVD memory must be between 1536 and 8192 MB, got {memory_mb}'
            )
        if not all(math.isfinite(value) and value > 0 for value in (start_timeout, stop_timeout)):
            raise LinuxAVDConfigurationError(
                'Linux AVD timeouts must be finite and greater than zero'
            )
        return memory_mb, start_timeout, stop_timeout

    @staticmethod
    def _validate_name(name):
        """Reject names that can be confused with emulator command options or paths."""
        if not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9._-]*', name):
            raise LinuxAVDConfigurationError(
                'Linux AVD name must start with a letter, number, or underscore and contain '
                'only letters, numbers, dot, underscore, or hyphen'
            )

    @staticmethod
    def _text(value):
        if value is None:
            return ''
        return str(value).strip()

    @staticmethod
    def _resolve_executable(explicit, sdk_root, relative, fallback):
        if explicit:
            return os.path.abspath(os.path.expanduser(explicit))
        if sdk_root:
            return os.path.abspath(os.path.join(os.path.expanduser(sdk_root), relative))
        for variable in ('ANDROID_SDK_ROOT', 'ANDROID_HOME'):
            root = os.environ.get(variable)
            if root:
                return os.path.abspath(os.path.join(os.path.expanduser(root), relative))
        return fallback

    def launch_command(self):
        """Build the persistent-data-preserving emulator command.

        Returns:
            list[str]: Emulator executable and arguments for this AVD.
        """
        command = [
            self.emulator_path,
            '-avd',
            self.name,
            '-port',
            str(self.console_port),
            '-memory',
            str(self.memory_mb),
            '-gpu',
            self.gpu,
            '-no-metrics',
        ]
        if self.headless:
            command.extend(['-no-window', '-no-audio'])
        return command
