from lxml import etree

from module.device.env import IS_WINDOWS
# Patch pkg_resources before importing adbutils and uiautomator2
from module.device.pkg_resources import get_distribution

# Just avoid being removed by import optimization
_ = get_distribution

from module.device.app_control import AppControl
from module.device.control import Control
from module.device.screenshot import Screenshot
from module.exception import (
    EmulatorNotRunningError,
    RequestHumanTakeover
)
from module.logger import logger


class Device(Screenshot, Control, AppControl):

    def __init__(self, *args, **kwargs):
        for trial in range(4):
            try:
                super().__init__(*args, **kwargs)
                break
            except EmulatorNotRunningError:
                if trial >= 3:
                    logger.critical('Failed to start emulator after 3 trial')
                    raise RequestHumanTakeover
                # Try to start emulator
                if self.emulator_instance is not None:
                    self.emulator_start()
                else:
                    logger.critical(
                        f'No emulator with serial "{self.config.Emulator_Serial}" found, '
                        f'please set a correct serial'
                    )
                    raise RequestHumanTakeover

        # Auto-fill emulator info
        if IS_WINDOWS and self.config.EmulatorInfo_Emulator == 'auto':
            _ = self.emulator_instance

        self.screenshot_interval_set()
        self.method_check()

        # Auto-select the fastest screenshot method
        if not self.config.is_template_config and self.config.Emulator_ScreenshotMethod == 'auto':
            self.run_simple_screenshot_benchmark()

        # Early init
        if self.config.is_actual_task:
            if self.config.Emulator_ControlMethod == 'MaaTouch':
                self.early_maatouch_init()
            if self.config.Emulator_ControlMethod == 'minitouch':
                self.early_minitouch_init()

    def run_simple_screenshot_benchmark(self):
        """
        Perform a screenshot method benchmark, test 3 times on each method.
        The fastest one will be set into config.
        """
        logger.info('run_simple_screenshot_benchmark')
        # Check resolution first
        self.resolution_check_uiautomator2()
        # Perform benchmark
        from module.daemon.benchmark import Benchmark
        bench = Benchmark(config=self.config, device=self)
        method = bench.run_simple_screenshot_benchmark()
        # Set
        with self.config.multi_set():
            self.config.Emulator_ScreenshotMethod = method
            # if method == 'nemu_ipc':
            #     self.config.Emulator_ControlMethod = 'nemu_ipc'

    def method_check(self):
        """
        Check combinations of screenshot method and control methods
        """
        # nemu_ipc should be together
        # if self.config.Emulator_ScreenshotMethod == 'nemu_ipc' and self.config.Emulator_ControlMethod != 'nemu_ipc':
        #     logger.warning('When using nemu_ipc, both screenshot and control should use nemu_ipc')
        #     self.config.Emulator_ControlMethod = 'nemu_ipc'
        # if self.config.Emulator_ScreenshotMethod != 'nemu_ipc' and self.config.Emulator_ControlMethod == 'nemu_ipc':
        #     logger.warning('When not using nemu_ipc, both screenshot and control should not use nemu_ipc')
        #     self.config.Emulator_ControlMethod = 'minitouch'
        # Allow Hermit on VMOS only
        if self.config.Emulator_ControlMethod == 'Hermit' and not self.is_vmos:
            logger.warning('ControlMethod Hermit is allowed on VMOS only')
            self.config.Emulator_ControlMethod = 'MaaTouch'
        if self.config.Emulator_ScreenshotMethod == 'ldopengl' \
                and self.config.Emulator_ControlMethod == 'minitouch':
            logger.warning('Use MaaTouch on ldplayer')
            self.config.Emulator_ControlMethod = 'MaaTouch'

        # Fallback to auto if nemu_ipc and ldopengl are selected on non-corresponding emulators
        if self.config.Emulator_ScreenshotMethod == 'nemu_ipc':
            if not (self.is_emulator and self.is_mumu_family):
                logger.warning('ScreenshotMethod nemu_ipc is available on MuMu Player 12 only, fallback to auto')
                self.config.Emulator_ScreenshotMethod = 'auto'
        if self.config.Emulator_ScreenshotMethod == 'ldopengl':
            if not (self.is_emulator and self.is_ldplayer_bluestacks_family):
                logger.warning('ScreenshotMethod ldopengl is available on LD Player only, fallback to auto')
                self.config.Emulator_ScreenshotMethod = 'auto'
        # DroidCast is available on SDK 23 (Android 6.0) to SDK 32 (Android 12)
        if self.config.Emulator_ScreenshotMethod in ['DroidCast', 'DroidCast_raw']:
            if self.sdk_ver < 23 or self.sdk_ver > 32:
                logger.warning(f'ScreenshotMethod {self.config.Emulator_ScreenshotMethod} is available on '
                               f'Android 6.0 to 12 only (current sdk_ver={self.sdk_ver}), fallback to auto')
                self.config.Emulator_ScreenshotMethod = 'auto'
        if not IS_WINDOWS and self.config.Emulator_ScreenshotMethod in ['nemu_ipc', 'ldopengl']:
            logger.warning(f'ScreenshotMethod {self.config.Emulator_ScreenshotMethod} is available on Windows only, '
                           f'fallback to auto')
            self.config.Emulator_ScreenshotMethod = 'auto'

    def screenshot(self):
        """
        Returns:
            np.ndarray:
        """
        self.stuck_record_check()

        try:
            super().screenshot()
        except RequestHumanTakeover:
            if not self.ascreencap_available:
                logger.error('aScreenCap unavailable on current device, fallback to auto')
                self.run_simple_screenshot_benchmark()
                super().screenshot()
            else:
                raise

        return self.image

    def dump_hierarchy(self) -> etree._Element:
        self.stuck_record_check()
        return super().dump_hierarchy()

    def release_during_wait(self):
        # Scrcpy server is still sending video stream,
        # stop it during wait
        if self.config.Emulator_ScreenshotMethod == 'scrcpy':
            self._scrcpy_server_stop()
        if self.config.Emulator_ScreenshotMethod == 'nemu_ipc':
            self.nemu_ipc_release()

    def get_orientation(self):
        """
        Callbacks when orientation changed.
        """
        o = super().get_orientation()

        self.on_orientation_change_maatouch()

        return o


    def set_clipboard(self, text):
        self.u2.set_clipboard(text)

    def app_start(self):
        super().app_start()
        self.stuck_record_clear()
        self.click_record_clear()

    def app_stop(self):
        super().app_stop()
        self.stuck_record_clear()
        self.click_record_clear()


