import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from module.device.platform.platform_base import PlatformBase
from module.device.platform.platform_linux import LinuxAVDLifecycle, PlatformLinux


def avd_config():
    """Return a minimal valid AVD configuration for platform tests."""
    return SimpleNamespace(
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


class PlatformLinuxTest(unittest.TestCase):
    @staticmethod
    def select_platform(is_windows, is_linux):
        """Load the platform selector against isolated host flags."""
        selected = {
            'windows': object(),
            'linux': object(),
            'base': object(),
        }
        env = ModuleType('module.device.env')
        env.IS_WINDOWS = is_windows
        env.IS_LINUX = is_linux
        windows = ModuleType('module.device.platform.platform_windows')
        windows.PlatformWindows = selected['windows']
        linux = ModuleType('module.device.platform.platform_linux')
        linux.PlatformLinux = selected['linux']
        base = ModuleType('module.device.platform.platform_base')
        base.PlatformBase = selected['base']
        spec = importlib.util.spec_from_file_location(
            'test_platform_selector',
            Path(__file__).parents[1] / 'module/device/platform/plat.py',
        )
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {
            'module.device.env': env,
            'module.device.platform.platform_windows': windows,
            'module.device.platform.platform_linux': linux,
            'module.device.platform.platform_base': base,
        }):
            spec.loader.exec_module(module)
        return module.Platform, selected

    def test_linux_platform_selector_exposes_platform_linux(self):
        """Catches Linux silently falling back to the no-op PlatformBase."""
        from module.device.platform.plat import Platform

        self.assertIs(Platform, PlatformLinux)

    def test_windows_selector_still_uses_platform_windows(self):
        """Catches Linux support replacing the existing Windows backend."""
        platform, selected = self.select_platform(is_windows=True, is_linux=False)

        self.assertIs(platform, selected['windows'])

    def test_macos_selector_still_uses_platform_base(self):
        """Catches Linux support leaking into the macOS platform path."""
        platform, selected = self.select_platform(is_windows=False, is_linux=False)

        self.assertIs(platform, selected['base'])

    def test_avd_is_ready_before_connection_initialization(self):
        """Catches Connection touching ADB before the configured AVD is ready."""
        events = []
        lifecycle = SimpleNamespace(
            settings=SimpleNamespace(enabled=True),
            start=lambda: events.append('avd-ready') or True,
            stop=lambda: events.append('avd-stopped') or True,
        )

        with patch(
            'module.device.platform.platform_linux.LinuxAVDLifecycle',
            return_value=lifecycle,
        ), patch.object(
            PlatformBase,
            '__init__',
            autospec=True,
            side_effect=lambda self, config: events.append('connection-init'),
        ):
            platform = PlatformLinux(avd_config())

        self.assertEqual(events, ['avd-ready', 'connection-init'])
        self.assertTrue(platform.linux_avd_managed)

    def test_connection_failure_stops_the_avd_started_during_initialization(self):
        """Catches a leaked AVD when Connection initialization raises."""
        events = []
        lifecycle = SimpleNamespace(
            settings=SimpleNamespace(enabled=True),
            start=lambda: events.append('avd-ready') or True,
            stop=lambda: events.append('avd-stopped') or True,
        )

        with patch(
            'module.device.platform.platform_linux.LinuxAVDLifecycle',
            return_value=lifecycle,
        ), patch.object(
            PlatformBase,
            '__init__',
            autospec=True,
            side_effect=RuntimeError('connection failed'),
        ):
            with self.assertRaisesRegex(RuntimeError, 'connection failed'):
                PlatformLinux(avd_config())

        self.assertEqual(events, ['avd-ready', 'avd-stopped'])

    def test_connection_failure_retains_management_when_shutdown_fails(self):
        """Catches Device cleanup losing the controller after an unsuccessful stop."""
        lifecycle = SimpleNamespace(
            settings=SimpleNamespace(enabled=True),
            start=lambda: True,
            stop=lambda: False,
        )
        platform = object.__new__(PlatformLinux)

        with patch(
            'module.device.platform.platform_linux.LinuxAVDLifecycle',
            return_value=lifecycle,
        ), patch.object(
            PlatformBase,
            '__init__',
            autospec=True,
            side_effect=RuntimeError('connection failed'),
        ):
            with self.assertRaisesRegex(RuntimeError, 'connection failed'):
                platform.__init__(avd_config())

        self.assertTrue(platform.linux_avd_managed)


if __name__ == '__main__':
    unittest.main()
