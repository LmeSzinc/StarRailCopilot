import numpy as np
from scipy import signal
from module.base.button import ButtonWrapper
from module.base.timer import Timer
from module.base.utils import area_size,crop,rgb2luma
from module.logger import logger
from tasks.base.ui import UI
from module.ui.scroll import Scroll
from tasks.combat.assets.assets_combat_team import COMBAT_TEAM_PREPARE, COMBAT_TEAM_SUPPORT, COMBAT_TEAM_DISMISSSUPPORT
from tasks.combat.assets.assets_combat_support import COMBAT_SUPPORT_ADD, COMBAT_SUPPORT_LIST, COMBAT_SUPPORT_LIST_SCROLL, COMBAT_SUPPORT_LIST_GRID
from tasks.character.assets.assets_character import *

class SupportCharacters():
    
    def __init__(self):
        self.support_list = self._genetate_support_list()
        
    def _genetate_support_list(self):
        import tasks.character.assets.assets_character
        # 获取该模块下所有的ButtonWrapper对象的名称，然后生成一个字典，key为名称，value为ButtonWrapper对象
        return {name: getattr(tasks.character.assets.assets_character, name) for name in dir(tasks.character.assets.assets_character) if isinstance(getattr(tasks.character.assets.assets_character, name), ButtonWrapper)}
    
    def get_character_by_name(self, name:str):
        """
        Args:
            name (str): Character name
        
        Returns:
            ButtonWrapper: Character button
        """
        logger.info(f'Support list:{self.support_list}')
        return self.support_list.get(name)
                
support_characters = SupportCharacters()


class SupportListScroll(Scroll):
    
    def cal_position(self, main):
        """
        Args:
            main (ModuleBase):
            
        Returns:
            float: 0 to 1.
        """
        image = main.device.image
        line = rgb2luma(crop(image, self.area)).flatten()
        width = area_size(self.area)[0]
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

    def support_set(self,support_character_name:str="Jing_Yuan"):
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
        CHARACTER:ButtonWrapper=support_characters.get_character_by_name(support_character_name)
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            
            # End
            if self.appear(COMBAT_TEAM_DISMISSSUPPORT,interval=2):
                return True
            
            # Click
            if self.appear(COMBAT_TEAM_SUPPORT,interval=2):
                self.device.click(COMBAT_TEAM_SUPPORT)
                self.interval_reset(COMBAT_TEAM_SUPPORT)
                continue
            if self.appear(COMBAT_SUPPORT_LIST,interval=2):
                self._search_support(CHARACTER)
                self.device.click(COMBAT_SUPPORT_ADD)
                self.interval_reset(COMBAT_SUPPORT_LIST)
                continue
    
    def _search_support(self,CHARACTER:ButtonWrapper=Jing_Yuan):
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
        CHARACTER.matched_button.search = COMBAT_SUPPORT_LIST_GRID.search
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
                    
                if self.appear_then_click(CHARACTER, similarity=0.7):
                    logger.info(f'Found support:{CHARACTER.name}')
                    return True
                
                if not scroll.at_bottom(main=self):
                    scroll.next_page(main=self)
                    continue
                else:
                    logger.info('Support not found')
                    return False