from module.logger import logger
from tasks.base.ui import UI
from tasks.combat.assets.assets_combat_popup import *
from tasks.map.assets.assets_map_control import RUN_BUTTON


class CombatPopup(UI):
    def handle_combat_popup(self):
        """
        Returns:
            bool: If clicked
        """
        # combat specific buff popup in Echo_of_War_Rusted_Crypt_of_the_Iron_Carcass
        if self.match_template_color(Rusted_Crypt_1, interval=5):
            # RUN_BUTTON is somewhere safe to click, no side effect and not clicking the popup itself
            logger.info(f'{Rusted_Crypt_1} -> {RUN_BUTTON}')
            self.device.click(RUN_BUTTON)
            return True
        if self.match_template_color(Rusted_Crypt_2, interval=5):
            logger.info(f'{Rusted_Crypt_2} -> {RUN_BUTTON}')
            self.device.click(RUN_BUTTON)
            return True
