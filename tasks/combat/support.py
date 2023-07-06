import cv2
import numpy as np
from scipy import signal
from module.base.button import ButtonWrapper
from module.base.timer import Timer
from module.base.utils import area_size,crop,rgb2luma
from module.logger import logger
from tasks.base.ui import UI
from module.ui.scroll import Scroll
from tasks.combat.assets.assets_combat_team import COMBAT_TEAM_SUPPORT, COMBAT_TEAM_DISMISSSUPPORT
from tasks.combat.assets.assets_combat_support import COMBAT_SUPPORT_ADD, COMBAT_SUPPORT_LIST, COMBAT_SUPPORT_LIST_SCROLL, COMBAT_SUPPORT_LIST_GRID
from PIL import Image
from module.base.button import Button, ButtonWrapper

class SupportCharacter():
    
    def __init__(self, name,screenshot,similarity=0.85):
        self.name = name
        self.image = self._scale_character()
        self.screenshot = screenshot
        self.similarity = similarity
        self.area = self._find_character()
        self.button = self._generate_character_button()
        
    def _scale_character(self):
        """
        Returns:
            Image: Character image after scaled
        """
        img = Image.open(f"assets/character/{self.name}.png")
        img = img.resize((85, 82))
        return img
    
    def _find_character(self):
        character = np.array(self.image)
        support_list_img = self.screenshot
        res = cv2.matchTemplate(character, support_list_img, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= self.similarity)
        return None if len(loc[0]) == 0 else (loc[1][0], loc[0][0], loc[1][0] + character.shape[1], loc[0][0] + character.shape[0])
    
    def _generate_character_button(self):
        return ButtonWrapper(
            name=self.name,
            share=Button(
                file=f'./assets/character/{self.name}.png',
                area=self.area,
                search=self.area,
                color=(0, 0, 0),
                button=self.area,
            ),
        ) if self.area is not None else None


class SupportListScroll(Scroll):
    
    def cal_position(self, main):
        """
        Args:
            main (ModuleBase):
            
        Returns:
            float: 0 to 1.
        """
        image = main.device.image
        
        temp_area = list(self.area)
        temp_area[0] = int(temp_area[0] * 0.95)
        temp_area[2] = int(temp_area[2] * 1.05)
        
        line = rgb2luma(crop(image, temp_area)).flatten()
        width = area_size(temp_area)[0]
        parameters = {
            'height': 180,
            'prominence': 30,
            'distance': width * 0.75,
        }
        peaks, _ = signal.find_peaks(line, **parameters)
        peaks //= width
        self.length = len(peaks)
        middle = np.mean(peaks)
        
        position = (middle - self.length / 2) / (self.total - self.length)
        position = position if position > 0 else 0.0
        position = position if position < 1 else 1.0
        logger.attr(self.name, f'{position:.2f} ({middle}-{self.length / 2})/({self.total}-{self.length})')
        return position


class CombatSupport(UI):

    def support_set(self,support_character_name:str="FirstCharacter"):
        """
        Args:
            support_character_name (str): Support character name
        
        Returns:
            bool: If clicked
        
        Pages:
            in: COMBAT_PREPARE
            mid: COMBAT_SUPPORT_LIST
            out: COMBAT_PREPARE
        """
        logger.hr('Combat support')
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            
            # End
            if self.appear(COMBAT_TEAM_DISMISSSUPPORT):
                return True
            
            # Click
            if self.appear(COMBAT_TEAM_SUPPORT,interval=2):
                self.device.click(COMBAT_TEAM_SUPPORT)
                self.interval_reset(COMBAT_TEAM_SUPPORT)
                continue
            if self.appear(COMBAT_SUPPORT_LIST,interval=2):
                if support_character_name != "FirstCharacter":
                    self._search_support(support_character_name) # Search support
                self.device.click(COMBAT_SUPPORT_ADD)
                self.interval_reset(COMBAT_SUPPORT_LIST)
                continue
    
    def _search_support(self,support_character_name="JingYuan"):
        """
        Args:
            CHARACTER: support character
        
        Returns:
            bool: True if found support else False
        
        Pages:
            in: COMBAT_SUPPORT_LIST
            out: COMBAT_SUPPORT_LIST
        """
        logger.hr('Combat support search')
        scroll = SupportListScroll(area=COMBAT_SUPPORT_LIST_SCROLL.area, color=(194,196,205), name=COMBAT_SUPPORT_LIST_SCROLL.name)
        if scroll.appear(main=self):
            if not scroll.at_bottom(main=self):
                scroll.set_bottom(main=self)
                scroll.set_top(main=self)
                
            logger.info('Searching support')
            skip_first_screenshot = False
            while 1:
                if skip_first_screenshot:
                    skip_first_screenshot = False
                else:
                    self.device.screenshot()
                
                character = SupportCharacter(support_character_name,self.device.image)
                if button := character.button:
                    self.device.click(button)
                    logger.info('Support found')
                    return True
                
                if not scroll.at_bottom(main=self):
                    scroll.next_page(main=self)
                    continue
                else:
                    logger.info('Support not found')
                    return False