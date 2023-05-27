from module.base.timer import Timer
from module.logger import logger
from tasks.base.page import page_camera
from tasks.base.ui import UI
from tasks.base.assets.assets_base_page import CLOSE
from tasks.camera.assets.assets_camera_ui import *

class CameraUI(UI):
    def take_picture(self, skip_first_screenshot=True):
        """
        Examples:
            self = CameraUI('alas')
            self.device.screenshot()
            self.take_picture()
        """
        self.ui_ensure(page_camera)
        timeout = Timer(2, count=4).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            
            if self.appear_then_click(TAKE_PICTURE):
                continue
            if timeout.reached():
                logger.warning('Wait picture being taken timeout')
                break
            if self.appear(PICTURE_TAKEN):
                logger.info('Picture was taken')
                self.device.click(CLOSE)
                break
    