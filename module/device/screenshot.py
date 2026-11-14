from datetime import datetime

import numpy as np

from module.base.decorator import cached_property
from module.base.utils import get_color, image_size
from module.device.base import DeviceBase
from module.device.method.adb import Adb
from module.device.method.ascreencap import AScreenCap
from module.device.method.droidcast import DroidCast
from module.device.method.ldopengl import LDOpenGL
from module.device.method.nemu_ipc import NemuIpc
from module.device.method.scrcpy import Scrcpy
from module.device.method.wsa import WSA
from module.exception import RequestHumanTakeover
from module.logger import logger


class Screenshot(DeviceBase, Adb, WSA, DroidCast, AScreenCap, Scrcpy, NemuIpc, LDOpenGL):
    _minicap_uninstalled = False
    image: np.ndarray

    @cached_property
    def screenshot_methods(self):
        return {
            'ADB': self.screenshot_adb,
            'ADB_nc': self.screenshot_adb_nc,
            'uiautomator2': self.screenshot_uiautomator2,
            'aScreenCap': self.screenshot_ascreencap,
            'aScreenCap_nc': self.screenshot_ascreencap_nc,
            'DroidCast': self.screenshot_droidcast,
            'DroidCast_raw': self.screenshot_droidcast_raw,
            'scrcpy': self.screenshot_scrcpy,
            'nemu_ipc': self.screenshot_nemu_ipc,
            'ldopengl': self.screenshot_ldopengl,
        }

    @cached_property
    def screenshot_method_override(self) -> str:
        # SRC only, use nemu_ipc if available
        available = self.nemu_ipc_available()
        logger.attr('nemu_ipc_available', available)
        if available:
            return 'nemu_ipc'
        available = self.ldopengl_available()
        logger.attr('ldopengl_available', available)
        if available:
            return 'ldopengl'
        return ''

    def screenshot(self):
        """
        Returns:
            np.ndarray:
        """
        self._screenshot_interval.wait()
        self._screenshot_interval.reset()

        for _ in range(2):
            if self.screenshot_method_override:
                method = self.screenshot_method_override
            else:
                method = self.config.Emulator_ScreenshotMethod
            method = self.screenshot_methods.get(method, self.screenshot_adb)

            self.image = method()

            # if self.config.Emulator_ScreenshotDedithering:
            #     # This will take 40-60ms
            #     cv2.fastNlMeansDenoising(self.image, self.image, h=17, templateWindowSize=1, searchWindowSize=2)
            self.image = self._handle_orientated_image(self.image)

            if self.config.Error_SaveError:
                self.screenshot_deque.append({'time': datetime.now(), 'image': self.image})

            if self.check_screen_size() and self.check_screen_black():
                break
            else:
                continue

        return self.image

    def check_screen_size(self):
        """
        Screen size must be 1280x720.
        Take a screenshot before call.
        """
        if self._screen_size_checked:
            return True

        orientated = False
        for _ in range(2):
            # Check screen size
            width, height = image_size(self.image)
            logger.attr('Screen_size', f'{width}x{height}')
            if width == 1280 and height == 720:
                self._screen_size_checked = True
                return True
            elif not orientated and (width == 720 and height == 1280):
                logger.info('Received orientated screenshot, handling')
                self.get_orientation()
                self.image = self._handle_orientated_image(self.image)
                orientated = True
                width, height = image_size(self.image)
                if width == 720 and height == 1280:
                    logger.info('Unable to handle orientated screenshot, continue for now')
                    return True
                else:
                    continue
            elif self.config.Emulator_Serial == 'wsa-0':
                self.display_resize_wsa(0)
                return False
            elif hasattr(self, 'app_is_running') and not self.app_is_running():
                logger.warning('Received orientated screenshot, game not running')
                return True
            else:
                logger.critical(f'Resolution not supported: {width}x{height}')
                logger.critical('Please set emulator resolution to 1280x720')
                raise RequestHumanTakeover

    def check_screen_black(self):
        if self._screen_black_checked:
            return True
        # Check screen color
        # May get a pure black screenshot on some emulators.
        color = get_color(self.image, area=(0, 0, 1280, 720))
        if sum(color) < 1:
            if self.config.Emulator_Serial == 'wsa-0':
                for _ in range(2):
                    display = self.get_display_id()
                    if display == 0:
                        return True
                logger.info(f'Game running on display {display}')
                logger.warning('Game not running on display 0, will be restarted')
                self.app_stop_uiautomator2()
                return False
            elif self.config.Emulator_ScreenshotMethod == 'uiautomator2':
                logger.warning(f'Received pure black screenshots from emulator, color: {color}')
                logger.warning('Uninstall minicap and retry')
                self.uninstall_minicap()
                self._screen_black_checked = False
                return False
            else:
                # logger.warning(f'Received pure black screenshots from emulator, color: {color}')
                # logger.warning(f'Screenshot method `{self.config.Emulator_ScreenshotMethod}` '
                #                f'may not work on emulator `{self.serial}`, or the emulator is not fully started')
                if self.is_mumu_family:
                    if self.config.Emulator_ScreenshotMethod == 'DroidCast':
                        self.droidcast_stop()
                    else:
                        logger.warning('If you are using MuMu X, please upgrade to version >= 12.1.5.0')
                self._screen_black_checked = False
                return False
        else:
            self._screen_black_checked = True
            return True
