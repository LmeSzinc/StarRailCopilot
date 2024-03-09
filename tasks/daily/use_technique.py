from module.base.timer import Timer
from module.logger import logger
from tasks.character.keywords import LIST_BACKGROUND_TECHNIQUE_RANGES, LIST_BACKGROUND_TECHNIQUE
from tasks.character.switch import CharacterSwitch
from tasks.dungeon.keywords import KEYWORDS_DUNGEON_LIST
from tasks.forgotten_hall.keywords import KEYWORDS_FORGOTTEN_HALL_STAGE
from tasks.forgotten_hall.ui import ForgottenHallUI
from tasks.map.control.joystick import MapControlJoystick


class UseTechniqueUI(MapControlJoystick, ForgottenHallUI):

    def use_technique_(self, count: int, skip_first_screenshot=True):
        remains = self.map_get_technique_points()
        if count > remains:
            logger.warning(f"Try to use technique {count} times but only have {remains}")
            return

        # Handle technique animation when it's being used
        # INFO │ Click ( 900,  600) @ E_BUTTON
        # INFO │ [TechniquePoints] 4
        # INFO │ [TechniquePoints] 3
        # INFO │ [TechniquePoints] 4
        # INFO │ [TechniquePoints] 3
        # INFO │ [TechniquePoints] 3
        confirm = Timer(.5, 2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            remains_after = self.map_get_technique_points()
            # In case the first count of remains is wrong
            remains = max(remains_after, remains)
            if remains - remains_after >= count:
                if confirm.reached() or count <= 1:
                    logger.info(f"{remains - remains_after} techniques used")
                    break
            else:
                confirm.reset()

            self.handle_map_E()

    def use_technique(self, count: int = 2, skip_first_screenshot=True):
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
        self.stage_goto(KEYWORDS_DUNGEON_LIST.The_Last_Vestiges_of_Towering_Citadel,
                        KEYWORDS_FORGOTTEN_HALL_STAGE.Stage_1)
        if not self.team_is_prepared():
            self.team_choose_first_4()
        self.enter_forgotten_hall_dungeon()
        self.use_technique_(count, skip_first_screenshot=skip_first_screenshot)
        self.exit_dungeon()
        self.ui_goto_main()

    def use_background_technique(self):
        character_switch = CharacterSwitch(self.config, self.device)
        if character_switch.character_current is None:
            character_switch.character_switch_to_ranged()
        if character_switch.character_current in LIST_BACKGROUND_TECHNIQUE_RANGES:
            self.use_technique_(1)

    def use_background_technique_deplete(self):
        character_switch = CharacterSwitch(self.config, self.device)
        if character_switch.character_current is None:
            character_switch.character_switch_to_ranged()
        last_character = character_switch.character_current
        characters = [c for c in LIST_BACKGROUND_TECHNIQUE if c in character_switch.characters]
        remains = self.map_get_technique_points()
        for i, c in enumerate(characters[:remains]):
            character_switch.character_switch(c)
            self.use_technique_(1)
        character_switch.character_switch(last_character)
