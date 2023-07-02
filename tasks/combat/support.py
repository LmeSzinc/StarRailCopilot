from module.base.button import ButtonWrapper
from module.base.timer import Timer
from module.logger import logger
from tasks.base.ui import UI
from tasks.combat.assets.assets_combat_team import COMBAT_TEAM_PREPARE, COMBAT_TEAM_SUPPORT, COMBAT_TEAM_DISMISSSUPPORT
from tasks.combat.assets.assets_combat_support import COMBAT_SUPPORT_ADD, COMBAT_SUPPORT_LIST

class CombatSupport(UI):
    
    def support_set(self):
        """
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
            if self.appear(COMBAT_TEAM_DISMISSSUPPORT,interval=2):
                return True
            
            # Click
            if self.appear(COMBAT_TEAM_SUPPORT,interval=2):
                self.device.click(COMBAT_TEAM_SUPPORT)
                self.interval_reset(COMBAT_TEAM_SUPPORT)
                continue
            if self.appear(COMBAT_SUPPORT_LIST,interval=2):
                self.device.click(COMBAT_SUPPORT_ADD)
                self.interval_reset(COMBAT_SUPPORT_LIST)
                continue