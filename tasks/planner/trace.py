from module.base.button import ClickButton
from module.base.utils import area_offset
from module.logger import logger
from module.ocr.ocr import Digit
from tasks.planner.assets.assets_planner_trace import *
from tasks.planner.ui import PlannerUI


class PlannerTrace(PlannerUI):
    def planner_trace_enter(self):
        """
        Pages:
            in: TRACE_ENTER
            out: TRACE_CONFIRM
        """
        logger.info('Trace enter')
        for _ in self.loop():
            if self.appear(TRACE_CONFIRM):
                break
            if self.appear_then_click(TRACE_ENTER):
                continue

    def planner_trace_confirm(self):
        """
        Pages:
            in: TRACE_CONFIRM
            out: TRACE_ENTER
        """
        logger.info('Trace enter')
        for _ in self.loop():
            if self.appear(TRACE_ENTER):
                break
            if self.appear_then_click(TRACE_CONFIRM):
                continue

    def planner_trace_enable_all(self):
        logger.info('Trace enable all')
        for _ in self.loop():
            if self.image_color_count(TRACE_TOGGLE, color=(219, 194, 145), threshold=221, count=100):
                break
            if self.appear(TRACE_CONFIRM, interval=3):
                self.device.click(TRACE_TOGGLE)
                self.interval_reset(TRACE_CONFIRM)
                continue

    def planner_trace_level_set(self, level, skill_button: ButtonWrapper):
        """
        Note that
        1. all skill_button should similar to SKILL_ATTACK, being in the Y middle of SKIPP_OP_AREA
        2. SKILL_OP_AREA and its buttons are made on SKILL_ATTACK
        3. all frames of SKILL_ATTACK should have the same area

        Returns:
            bool: If success
        """
        logger.info(f'Trace level set {skill_button}, level={level}')
        # move SKIPP_OP_AREA according to skill_button
        if self.match_template_luma(skill_button):
            align = skill_button
        else:
            logger.warning(f'Cannot find skill_button {skill_button}')
            return False
        y = align.button[1] - SKILL_ATTACK.area[1]
        area = area_offset(SKILL_OP_AREA.area, offset=(0, y))

        # Move level operation buttons according to SKIPP_OP_AREA
        for button in [
            LEVEL_MINUS, LEVEL_MINUS_INACTIVE, LEVEL_PLUS, LEVEL_PLUS_INACTIVE,
        ]:
            button.load_search(area)
        x = 0
        if self.match_template_luma(LEVEL_MINUS):
            x, y = LEVEL_MINUS.matched_button._button_offset
        elif self.match_template_luma(LEVEL_MINUS_INACTIVE):
            x, y = LEVEL_MINUS_INACTIVE.matched_button._button_offset
        elif self.match_template_luma(LEVEL_PLUS):
            y = LEVEL_PLUS.matched_button._button_offset[1]
        elif self.match_template_luma(LEVEL_PLUS_INACTIVE):
            y = LEVEL_PLUS.matched_button._button_offset[1]
        else:
            logger.warning(f'Cannot find level op button')
            return False
        # move all along Y according to SKILL_OP_AREA
        # move LEVEL_VALUE_START along X according to LEVEL_MINUS
        for button in [LEVEL_MINUS, LEVEL_VALUE_START]:
            button.load_offset((x, y))
        for button in [LEVEL_PLUS, LEVEL_VALUE_TARGET]:
            button.load_offset((0, y))

        # check start
        ocr = Digit(ClickButton(LEVEL_VALUE_START.button), name=f'{skill_button}_START')
        start = ocr.ocr_single_line(self.device.image)
        if start > 0 and level < start:
            logger.info(f'Fixup level to level start: {start}')
            level = start

        # set target
        ocr = Digit(ClickButton(LEVEL_VALUE_TARGET.button), name=f'{skill_button}_TARGET')
        self.ui_ensure_index(
            level, letter=ocr, prev_button=LEVEL_MINUS, next_button=LEVEL_PLUS, skip_first_screenshot=True)
        return True

    def planner_trace_set(self):
        """
        Set all skill levels
        """
        self.planner_trace_enable_all()
        self.planner_trace_level_set(self.config.PlannerTarget_AttackLevel, skill_button=SKILL_ATTACK)
        self.planner_trace_level_set(self.config.PlannerTarget_SkillLevel, skill_button=SKILL_SKILL)
        self.planner_trace_level_set(self.config.PlannerTarget_UltimateLevel, skill_button=SKILL_ULTIMATE)
        self.planner_trace_level_set(self.config.PlannerTarget_TalentLevel, skill_button=SKILL_TALENT)
        self.planner_trace_level_set(self.config.PlannerTarget_MemoSkillLevel, skill_button=SKILL_MEMO_SKILL)
        self.planner_trace_level_set(self.config.PlannerTarget_MemoTalentLevel, skill_button=SKILL_MEMO_TALENT)
