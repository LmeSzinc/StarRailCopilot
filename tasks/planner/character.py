from typing import Optional

from pponnxcr.predict_system import BoxedResult

from module.base.button import ClickButton
from module.base.utils import random_rectangle_vector_opted
from module.exception import ScriptError
from module.logger import logger
from module.ocr.ocr import Ocr, OcrResultButton, Digit
from tasks.character.keywords import CharacterList
from tasks.cone.keywords import Cone
from tasks.planner.assets import assets_planner_selectpath as assets_path
from tasks.planner.assets.assets_planner_enter import CONE_MATERIAL_CHECK
from tasks.planner.assets.assets_planner_result import START_CALCULATE
from tasks.planner.assets.assets_planner_select import *
from tasks.planner.lang import PlannerLang
from tasks.planner.ui import PlannerUI


class SelectOcr(Ocr):
    merge_thres_x = 10
    merge_thres_y = 40

    def filter_detected(self, result: BoxedResult) -> bool:
        text = result.ocr_text.lower()
        # drop "Level 80" above character name
        if 'level' in text:
            return False
        if '等级' in text:
            return False
        # Not Owned
        if 'owne' in text:
            return False
        if '未拥有' in text:
            return False
        return True

    def after_process(self, result):
        # TheUnreachabl...As
        result, _,  _ = result.partition('...')
        # Thus Burnsthe DawnAS
        lower = result.lower()
        if lower.endswith('as'):
            result = result[:-2]
        elif lower.endswith('a'):
            result = result[:-1]
        return result

    def _match_result(
            self,
            result: str,
            keyword_classes,
            lang: str = None,
            ignore_punctuation=True,
            ignore_digit=True):

        if not isinstance(keyword_classes, list):
            keyword_classes = [keyword_classes]

        for keyword_class in keyword_classes:
            try:
                matched = keyword_class.find_startswith(
                    result,
                    lang=lang,
                    ignore_punctuation=ignore_punctuation
                )
                return matched
            except ScriptError:
                continue

        return None


class PlannerSelect(PlannerUI, PlannerLang):
    def ocr_planner_select_area(self):
        if self.planner_lang == 'cn':
            area = CHARACTER_AREA_CN.area
        elif self.planner_lang == 'en':
            area = CHARACTER_AREA_EN.area
        else:
            logger.warning(f'Cannot convert planner lang {self.planner_lang} to select area, use cn instead')
            area = CHARACTER_AREA_CN.area
        return ClickButton(area)

    def get_planner_character(self, target: CharacterList) -> Optional[OcrResultButton]:
        area = self.ocr_planner_select_area()
        ocr = SelectOcr(area, name='PlannerCharacter', lang=self.planner_lang)
        results = ocr.matched_ocr(self.device.image, lang=self.planner_lang, keyword_classes=CharacterList)

        if target.is_trailblazer:
            # we can't distinguish trailblazers by name
            # but with path and type selected, the first one is the target
            for result in results:
                if target.is_trailblazer:
                    logger.info(f'Found target character: {target}')
                    return result
        else:
            for result in results:
                if target == result.matched_keyword:
                    logger.info(f'Found target character: {target}')
                    return result
        return None

    def get_planner_cone(self, target: Cone) -> Optional[OcrResultButton]:
        area = self.ocr_planner_select_area()
        ocr = SelectOcr(area, name='PlannerCone', lang=self.planner_lang)
        results = ocr.matched_ocr(self.device.image, lang=self.planner_lang, keyword_classes=Cone)
        for result in results:
            if target == result.matched_keyword:
                logger.info(f'Found target cone: {target}')
                return result
        return None

    def select_planner_character(self, target: CharacterList):
        """
        Pages:
            in: is_in_planner_select
            out: page_planner, MATERIAL_CALCULATION_CHECK, CHARACTER_MATERIAL_CHECK, with character selected
        """
        logger.hr('Select planner character')
        logger.info(f'Select character: {target}')
        self.planner_character_path.set(target.character_path, main=self)
        self.planner_character_type.set(target.combat_type, main=self)
        area = self.ocr_planner_select_area().area

        self.device.stuck_record_clear()
        self.device.click_record_clear()
        result = None
        for _ in range(10):
            r = self.get_planner_character(target)
            if r:
                result = r
                break
            p1, p2 = random_rectangle_vector_opted(
                (0, -300), box=area, random_range=(-20, -20, 20, 20))
            self.device.drag(p1, p2, name=f'PLANNER_SELECT_DRAG')
            self.device.screenshot()

        if result is None:
            logger.warning('Failed to select after 7 trail')
            self.planner_aside_close()
            self.ui_ensure_planner()
            return False

        # select
        for _ in self.loop():
            if self.match_template_color(START_CALCULATE):
                if self.match_template_color(CHARACTER_LEVEL):
                    logger.info(f'Character selected ({CHARACTER_LEVEL})')
                    return True
                if self.match_template_color(CHARACTER_SWITCH):
                    logger.info(f'Character selected ({CHARACTER_SWITCH})')
                    return True
            if self.is_in_planner_select(interval=5):
                self.device.click(result)
                self.interval_reset(assets_path.All_CHECK)
                continue

    def select_planner_cone(self, target: Cone):
        """
        Pages:
            in: is_in_planner_select
            out: page_planner, MATERIAL_CALCULATION_CHECK, CHARACTER_MATERIAL_CHECK, with cone selected
        """
        logger.hr('Select planner cone')
        logger.info(f'Select cone: {target}')
        self.planner_character_path.set(target.character_path, main=self)
        area = self.ocr_planner_select_area().area

        self.device.stuck_record_clear()
        self.device.click_record_clear()
        result = None
        for _ in range(10):
            r = self.get_planner_cone(target)
            if r:
                result = r
                break
            p1, p2 = random_rectangle_vector_opted(
                (0, -300), box=area, random_range=(-20, -20, 20, 20))
            self.device.drag(p1, p2, name=f'PLANNER_SELECT_DRAG')
            self.device.screenshot()

        if result is None:
            logger.warning('Failed to select after 7 trail')
            self.planner_aside_close()
            self.ui_ensure_planner()
            return False

        # select
        for _ in self.loop():
            if self.match_template_color(START_CALCULATE):
                # Note that cone select endswith CONE_SWITCH
                # because it needs scrolling to see CONE_LEVEL
                if self.match_template_color(CONE_SWITCH):
                    logger.info(f'Cone selected ({CONE_SWITCH})')
                    return True
                # calculate cone only
                if self.planner_calculate_target.get(main=self) == CONE_MATERIAL_CHECK:
                    if self.match_template_color(CHARACTER_SWITCH):
                        logger.info(f'Cone selected ({CONE_MATERIAL_CHECK}, {CHARACTER_SWITCH})')
                        return True
            if self.is_in_planner_select(interval=5):
                self.device.click(result)
                self.interval_reset(assets_path.All_CHECK)
                continue

    def character_set_level(self, level, level_button):
        """
        Args:
            level_button (ButtonWrapper)

        Returns:
            bool: If success

        Pages:
            in: CHARACTER_LEVEL

        Examples:
            self.planner_insight_character()
            self.character_set_level(80, level_button=CHARACTER_LEVEL)
            self.planner_insight_cone()
            self.character_set_level(80, level_button=CONE_LEVEL)
        """
        appear = self.match_template_luma(level_button)
        if not appear:
            logger.warning(f'Cannot find level_button {level_button}')
            return False
        # handle CONE_LEVEL
        if level_button != CHARACTER_LEVEL:
            y = level_button.area[1] - CHARACTER_LEVEL.area[1]
            offset = level_button.matched_button._button_offset
            level_button.matched_button._button_offset = (offset[0], offset[1] + y)
        # move other buttons accordingly
        for button in [LEVEL_MINUS, LEVEL_PLUS, LEVEL_VALUE_START, LEVEL_VALUE_TARGET]:
            button.load_offset(level_button)

        # check start
        ocr = Digit(ClickButton(LEVEL_VALUE_START.button), name=f'{level_button}_START')
        start = ocr.ocr_single_line(self.device.image)
        if start > 0 and level < start:
            logger.info(f'Fixup level to level start: {start}')
            level = start

        # set target
        ocr = Digit(ClickButton(LEVEL_VALUE_TARGET.button), name=f'{level_button}_TARGET')
        self.ui_ensure_index(
            level, letter=ocr, prev_button=LEVEL_MINUS, next_button=LEVEL_PLUS, skip_first_screenshot=True)
        return True


if __name__ == '__main__':
    self = PlannerSelect('oversea')
    self.device.screenshot()
    self.ui_ensure_planner()
    c = CharacterList.find_name('DanHengImbibitorLunae')
    self.select_planner_character(c)
