import numpy as np

from module.base.timer import Timer
from module.base.utils import get_color
from module.logger import logger
from tasks.base.page import page_main
from tasks.daily.assets.assets_daily_use_techniques import *
from tasks.dungeon.keywords import KEYWORDS_DUNGEON_LIST
from tasks.forgotten_hall.keywords import KEYWORDS_FORGOTTEN_HALL_STAGE
from tasks.forgotten_hall.ui import ForgottenHallUI
from tasks.map.control.joystick import MapControlJoystick


class UseTechniqueUI(MapControlJoystick, ForgottenHallUI):
    def _enter_forgotten_hall_dungeon(self, skip_first_screenshot=True):
        interval = Timer(1)
        while 1:  # enter ui -> popup
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(EFFECT_NOTIFICATION):
                break
            if interval.reached() and np.mean(get_color(self.device.image, ENTER_FORGOTTEN_HALL_DUNGEON.area)) > 128:
                self.device.click(ENTER_FORGOTTEN_HALL_DUNGEON)
                interval.reset()
                continue
            if (interval.reached()
                    # avoid click on loading page
                    and np.mean(get_color(self.device.image, FIRST_CHARACTER.area)) > 30):
                self.device.click(FIRST_CHARACTER)
                interval.reset()
        skip_first_screenshot = True
        while 1:  # pop up -> dungeon inside
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.match_template_color(DUNGEON_ENTER_CHECKED):
                logger.info("Forgotten hall dungeon entered")
                break
            self.handle_map_run()

    def _use_technique(self, count: int, skip_first_screenshot=True):
        remains = self.map_get_technique_points()
        if count > remains:
            logger.warning(f"Try to use technique {count} times but only have {remains}")
            return
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            remains_after = self.map_get_technique_points()
            if remains - remains_after >= count:
                logger.info(f"{remains - remains_after} techniques used")
                break
            self.handle_map_E()

    def use_technique(self, count: int, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot:
            count: use {count} times

        Examples:
            self = UseTechniquesUI('alas')
            self.device.screenshot()
            self.use_techniques(2)

        Pages:
            in: Any
            out: page_forgotten_hall, FORGOTTEN_HALL_CHECKED
        """
        logger.hr('Use techniques', level=2)
        self.ui_ensure(page_main)
        self.stage_goto(KEYWORDS_DUNGEON_LIST.The_Last_Vestiges_of_Towering_Citadel,
                        KEYWORDS_FORGOTTEN_HALL_STAGE.Stage_1)
        self._enter_forgotten_hall_dungeon()
        self._use_technique(count, skip_first_screenshot=skip_first_screenshot)
        self.exit_dungeon()
        self.ui_goto_main()
