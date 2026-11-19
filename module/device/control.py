from module.base.button import ClickButton
from module.base.decorator import cached_property
from module.base.utils import *
from module.device.base import DeviceBase
from module.device.method.hermit import Hermit
from module.device.method.maatouch import MaaTouch
from module.device.method.minitouch import Minitouch
from module.device.method.nemu_ipc import NemuIpc
from module.device.method.scrcpy import Scrcpy
from module.logger import logger


class Control(DeviceBase, Hermit, Minitouch, Scrcpy, MaaTouch, NemuIpc):

    @cached_property
    def click_methods(self):
        return {
            'ADB': self.click_adb,
            'uiautomator2': self.click_uiautomator2,
            'minitouch': self.click_minitouch,
            'Hermit': self.click_hermit,
            'MaaTouch': self.click_maatouch,
            'nemu_ipc': self.click_nemu_ipc,
        }

    def long_click(self, button, duration=(1, 1.2)):
        """Method to long click a button.

        Args:
            button (button.Button): AzurLane Button instance.
            duration(int, float, tuple):
        """
        self.handle_control_check(button)
        x, y = random_rectangle_point(button.button)
        x, y = ensure_int(x, y)
        duration = ensure_time(duration)
        logger.info(
            'Click %s @ %s, %s' % (point2str(x, y), button, duration)
        )
        method = self.config.Emulator_ControlMethod
        if method == 'minitouch':
            self.long_click_minitouch(x, y, duration)
        elif method == 'uiautomator2':
            self.long_click_uiautomator2(x, y, duration)
        elif method == 'scrcpy':
            self.long_click_scrcpy(x, y, duration)
        elif method == 'MaaTouch':
            self.long_click_maatouch(x, y, duration)
        elif method == 'nemu_ipc':
            self.long_click_nemu_ipc(x, y, duration)
        else:
            self.swipe_adb((x, y), (x, y), duration)

    def swipe(self, p1, p2, duration=(0.1, 0.2), name='SWIPE', distance_check=True):
        self.handle_control_check(name)
        p1, p2 = ensure_int(p1, p2)
        duration = ensure_time(duration)
        method = self.config.Emulator_ControlMethod
        if method == 'uiautomator2':
            logger.info('Swipe %s -> %s, %s' % (point2str(*p1), point2str(*p2), duration))
        elif method in ['minitouch', 'MaaTouch', 'scrcpy', 'nemu_ipc']:
            logger.info('Swipe %s -> %s' % (point2str(*p1), point2str(*p2)))
        else:
            # ADB needs to be slow, or swipe doesn't work
            duration *= 2.5
            logger.info('Swipe %s -> %s, %s' % (point2str(*p1), point2str(*p2), duration))

        if distance_check:
            if np.linalg.norm(np.subtract(p1, p2)) < 10:
                # Should swipe a certain distance, otherwise AL will treat it as click.
                # uiautomator2 should >= 6px, minitouch should >= 5px
                logger.info('Swipe distance < 10px, dropped')
                return

        if method == 'minitouch':
            self.swipe_minitouch(p1, p2)
        elif method == 'uiautomator2':
            self.swipe_uiautomator2(p1, p2, duration=duration)
        elif method == 'scrcpy':
            self.swipe_scrcpy(p1, p2)
        elif method == 'MaaTouch':
            self.swipe_maatouch(p1, p2)
        elif method == 'nemu_ipc':
            self.swipe_nemu_ipc(p1, p2)
        else:
            self.swipe_adb(p1, p2, duration=duration)


    def drag(self, p1, p2, segments=1, shake=(0, 15), point_random=(-10, -10, 10, 10), shake_random=(-5, -5, 5, 5),
             swipe_duration=0.25, shake_duration=0.1, name='DRAG'):
        self.handle_control_check(name)
        p1, p2 = ensure_int(p1, p2)
        logger.info(
            'Drag %s -> %s' % (point2str(*p1), point2str(*p2))
        )
        method = self.config.Emulator_ControlMethod
        if method == 'minitouch':
            self.drag_minitouch(p1, p2, point_random=point_random)
        elif method == 'uiautomator2':
            self.drag_uiautomator2(
                p1, p2, segments=segments, shake=shake, point_random=point_random, shake_random=shake_random,
                swipe_duration=swipe_duration, shake_duration=shake_duration)
        elif method == 'scrcpy':
            self.drag_scrcpy(p1, p2, point_random=point_random)
        elif method == 'MaaTouch':
            self.drag_maatouch(p1, p2, point_random=point_random)
        elif method == 'nemu_ipc':
            self.drag_nemu_ipc(p1, p2, point_random=point_random)
        else:
            logger.warning(f'Control method {method} does not support drag well, '
                           f'falling back to ADB swipe may cause unexpected behaviour')
            self.swipe_adb(p1, p2, duration=ensure_time(swipe_duration * 2))
            self.click(ClickButton(area=area_offset(point_random, p2), name=name))
