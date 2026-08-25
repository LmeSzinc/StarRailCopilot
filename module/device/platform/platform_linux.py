from module.device.platform.linux_avd import LinuxAVDLifecycle
from module.device.platform.linux_avd_settings import (
    LinuxAVDConfigurationError,
    LinuxAVDSettings,
    LinuxAVDStartError,
)
from module.device.platform.platform_base import PlatformBase
from module.logger import logger

__all__ = [
    'LinuxAVDConfigurationError',
    'LinuxAVDLifecycle',
    'LinuxAVDSettings',
    'LinuxAVDStartError',
    'PlatformLinux',
]


class PlatformLinux(PlatformBase):
    """Linux platform adapter with optional Android AVD lifecycle management."""

    def __init__(self, config):
        """Start an enabled AVD before initializing the shared device connection.

        Args:
            config: SRC configuration containing device and Linux AVD options.

        Raises:
            BaseException: Re-raises startup and connection errors after AVD cleanup.
        """
        self.linux_avd = LinuxAVDLifecycle(config)
        self.linux_avd_managed = False
        if self.linux_avd.settings.enabled:
            self.linux_avd.start()
            self.linux_avd_managed = True
        try:
            super().__init__(config)
        except BaseException:
            self._cleanup_initialization_failure()
            raise

    def _cleanup_initialization_failure(self):
        """Preserve the primary initialization error while attempting AVD shutdown."""
        if not self.linux_avd_managed:
            return
        try:
            stopped = self.linux_avd.stop()
        except BaseException as cleanup_error:
            logger.warning(
                f'Failed to stop Linux AVD after platform initialization error: {cleanup_error}'
            )
            stopped = False
        self.linux_avd_managed = not stopped

    def emulator_start(self):
        """Start the configured Linux AVD or delegate to the base platform.

        Returns:
            bool: True when an enabled AVD reaches all readiness gates.
        """
        if not self.linux_avd.settings.enabled:
            return super().emulator_start()
        started = self.linux_avd.start()
        self.linux_avd_managed = bool(started)
        return started

    def emulator_stop(self):
        """Stop the configured Linux AVD or delegate to the base platform.

        Returns:
            bool: True when an enabled AVD has completely disappeared.
        """
        if not self.linux_avd.settings.enabled:
            return super().emulator_stop()
        stopped = self.linux_avd.stop()
        if stopped:
            self.linux_avd_managed = False
        return stopped
