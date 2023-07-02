import numpy as np

from module.base.timer import Timer
from module.base.utils import get_color
from module.logger import logger
from tasks.base.page import page_main
from tasks.base.ui import UI
from tasks.daily.assets.assets_daily_use_techniques import *
from tasks.dungeon.keywords import KEYWORDS_DUNGEON_LIST
from tasks.forgotten_hall.keywords import KEYWORDS_FORGOTTEN_HALL_STAGE
from tasks.forgotten_hall.ui import ForgottenHallUI
from tasks.map.control.joystick import MapControlJoystick


class UseTechniqueUI(UI):
    def _enter_forgotten_hall_dungeon(self, joystick: MapControlJoystick, skip_first_screenshot=True):
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
            joystick.handle_map_run()

    def _use_technique(self, count: int, remains: int, joystick: MapControlJoystick, skip_first_screenshot=True):
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            remains_after = joystick.map_get_technique_points()
            if remains - remains_after >= count:
                logger.info(f"{remains - remains_after} techniques used")
                break
            joystick.handle_map_E()

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
        joystick = MapControlJoystick(self.config, self.device)
        remains = joystick.map_get_technique_points()
        forgotten_hall = ForgottenHallUI(self.config, self.device)
        if remains >= count:
            logger.info(f"Already have {remains} techniques remaining")
            self._use_technique(count, remains, joystick, skip_first_screenshot)
        else:
            logger.info("Remains less than needed. Go to forgotten hall to charge")
            forgotten_hall.stage_goto(KEYWORDS_DUNGEON_LIST.The_Last_Vestiges_of_Towering_Citadel,
                                      KEYWORDS_FORGOTTEN_HALL_STAGE.Stage_1)
            self._enter_forgotten_hall_dungeon(joystick=joystick)
            self._use_technique(count, 5, joystick, skip_first_screenshot)
            forgotten_hall.exit_dungeon()
            self.ui_goto_main()
