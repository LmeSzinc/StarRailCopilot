from module.logger import logger
from module.ocr.ocr import Ocr, OcrResultButton
from module.base.timer import Timer

from tasks.base.page import page_menu
from tasks.base.ui import UI
from tasks.base.assets.assets_base_page import CLOSE,MENU_CHECK
from tasks.freebies.assets.assets_freebies_support_reward import MENU_TO_PROFILE, OCR_PROFILE, IN_PROFILE,CAN_GET_REWARD, GOT_REWARD
from tasks.freebies.keywords import *

class SupportReward(UI):
    
    def run(self):
        """
        Run get support reward task
        """
        self._get_support_reward()
        
    def _get_support_reward(self):
        self.ui_ensure(page_menu)
        
        self._goto_profile()
        self._get_reward()
        self._goto_menu()
        self.ui_ensure(page_menu)
        
    def _goto_profile(self):
        """
        Pages:
            in: MENU
            out: PROFILE
        """
        skip_first_screenshot = False
        ocr = Ocr(OCR_PROFILE)
        logger.info('Going to profile')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            
            if self.appear(IN_PROFILE):
                logger.info('Successfully in profile')
                return True
            
            if self.appear_then_click(MENU_TO_PROFILE):
                continue
            
            result = ocr.matched_ocr(self.device.image, [Profile])
            if len(result) == 0:
                logger.warning('Profile not found')
                continue
            else:
                logger.info('Profile found')
                self.device.click(OCR_PROFILE)
                continue
        
    def _get_reward(self):
        """
        Pages:
            in: PROFILE
            out: PROFILE
        """
        skip_first_screenshot = False
        logger.info('Getting reward')
        has_reward = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            
            if self.appear(GOT_REWARD):
                self.device.click(MENU_CHECK) # Avoid clicking on some other buttons
                continue
            
            if self.match_template_color(CAN_GET_REWARD, similarity=0.70):
                logger.info('Can get reward')
                self.device.click(CAN_GET_REWARD)
                has_reward = True
                continue
             
            if self.appear(IN_PROFILE): # and not self.appear(CAN_GET_REWARD):
                logger.info('Successfully got reward') if has_reward else logger.info('No reward')
                return True
    
    def _goto_menu(self):
        """
        Pages:
            in: PROFILE
            out: MENU
        """
        skip_first_screenshot = False
        logger.info('Going to menu')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            
            if self.appear(MENU_CHECK):
                return True
            
            if self.appear(IN_PROFILE):
                self.device.click(CLOSE)
                continue
            
    
if __name__ == '__main__':
    self = SupportReward('src')
    self.device.screenshot()
    self._get_support_reward()