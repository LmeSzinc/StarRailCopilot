from module.base.timer import Timer
from module.logger import logger
from module.ocr.ocr import *
from tasks.base.page import page_camera
from tasks.base.ui import UI
from tasks.base.assets.assets_base_page import CLOSE
from tasks.daily.assets.assets_daily import *

class CameraUI(UI):
    def take_picture(self, skip_first_screenshot=True):
        """
        Examples:
            self = CameraUI('alas')
            self.device.screenshot()
            self.take_picture()
        """
        self.ui_ensure(page_camera)
        picture_taken = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            
            if self.appear_then_click(TAKE_PICTURE):
                continue
            if not picture_taken and self.appear(PICTURE_TAKEN):
                logger.info('Picture was taken')
                picture_taken = True
                continue
            if picture_taken and self.appear_then_click(CLOSE):
                break
                