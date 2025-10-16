from module.exception import ScriptError
from module.logger import logger
from tasks.character.keywords import CharacterList
from tasks.cone.keywords import Cone
from tasks.planner.assets.assets_planner_enter import CHARACTER_MATERIAL_CHECK, CONE_MATERIAL_CHECK
from tasks.planner.assets.assets_planner_result import RESULT_CHECK, START_CALCULATE
from tasks.planner.assets.assets_planner_select import CHARACTER_LEVEL, CONE_LEVEL
from tasks.planner.character import PlannerSelect
from tasks.planner.scan import PlannerScan


class PlannerTarget(PlannerSelect, PlannerScan):
    def planner_start_calculate(self):
        """
        Pages:
            in: START_CALCULATE
        """
        logger.info('Planner start calculate')
        for _ in self.loop():
            if self.appear(RESULT_CHECK):
                break
            if self.match_template_color(START_CALCULATE, interval=3):
                self.device.click(START_CALCULATE)
                continue

    def planner_calculate(self):
        """
        Returns:
            bool: If success
        """
        # Check target
        try:
            if self.config.PlannerTarget_Character == '_none_':
                character = None
            else:
                character = CharacterList.find_name(self.config.PlannerTarget_Character)
        except ScriptError:
            logger.info(f'Invalid character name: {self.config.PlannerTarget_Character}')
            return False
        try:
            if self.config.PlannerTarget_Cone == '_none_':
                cone = None
            else:
                cone = Cone.find_name(self.config.PlannerTarget_Cone)
        except ScriptError:
            logger.info(f'Invalid cone name: {self.config.PlannerTarget_Cone}')
            return False
        character: "CharacterList | None" = character
        cone: "Cone | None" = cone
        if not character and not cone:
            logger.info('Empty character and cone, no need to calculate')
            return False

        # set target
        logger.hr('Planner calculate', level=1)
        self.ui_ensure_planner()

        if character:
            logger.hr('Select planner character', level=2)
            self.planner_calculate_target.set(CHARACTER_MATERIAL_CHECK, main=self)
            self.planner_insight_character()
            self.planner_character_enter()
            self.select_planner_character(target=character)
            self.planner_insight_character()
            self.character_set_level(level=self.config.PlannerTarget_CharacterLevel, level_button=CHARACTER_LEVEL)
            if cone:
                logger.hr('Select planner cone', level=2)
                self.planner_insight_cone()
                self.planner_cone_enter()
                self.select_planner_cone(target=cone)
                # scroll to see level
                self.planner_insight_cone()
                self.character_set_level(level=self.config.PlannerTarget_ConeLevel, level_button=CONE_LEVEL)
        else:
            # has_cone
            logger.hr('Select planner cone', level=2)
            self.planner_calculate_target.set(CONE_MATERIAL_CHECK, main=self)
            # if cone only, cone shows at character's position, so we switch ui like character
            self.planner_insight_character()
            self.planner_character_enter()
            self.select_planner_cone(target=cone)
            self.character_set_level(level=self.config.PlannerTarget_CharacterLevel, level_button=CHARACTER_LEVEL)

        # calculate
        self.planner_start_calculate()
        self.parse_planner_result()
        return True


if __name__ == '__main__':
    self = PlannerTarget('oversea')
    self.config.override(PlannerTarget_Character='Evernight')
    self.config.override(PlannerTarget_Cone='To_Evernight_Stars')
    self.planner_calculate()
