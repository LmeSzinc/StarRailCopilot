import re

import numpy as np

from module.base.filter import MultiLangFilter
from module.base.timer import Timer
from module.base.utils import get_color
from module.logger import logger
from module.ocr.ocr import Ocr, OcrResultButton
from tasks.rogue.assets.assets_rogue_curio import CURIO_ENFORCE, OCR_ROGUE_CURIO
from tasks.rogue.assets.assets_rogue_ui import BLESSING_CONFIRM, BLESSING_ENHANCED, BLESSING_LOST, BLESSING_OBTAINED
from tasks.rogue.blessing.preset import CURIO_PRESET
from tasks.rogue.blessing.selector import RogueSelector
from tasks.rogue.blessing.utils import get_regex_from_keyword_name, parse_name
from tasks.rogue.keywords import RogueCurio

CURIO_FILTER_ATTR = tuple()
CURIO_ATTR_NAME = 'curio_name'
patt = get_regex_from_keyword_name(RogueCurio, CURIO_ATTR_NAME)
CURIO_FILTER_ATTR += (CURIO_ATTR_NAME,)
CURIO_FILTER_PRESET = ('random', 'unrecorded')
FILTER_REGEX = re.compile(patt)
CURIO_FILTER = MultiLangFilter(FILTER_REGEX, CURIO_FILTER_ATTR, CURIO_FILTER_PRESET)


class RogueCurioOcr(Ocr):
    merge_thres_y = 40

    def after_process(self, result):
        result = super().after_process(result)
        if self.lang == 'cn':
            replace_pattern_dict = {
                "般": "骰",
                "漂灭": "湮灭",
                "殷子": "骰子",
            }
            for pattern, replace in replace_pattern_dict.items():
                result = re.sub(pattern, replace, result)
        return result


class RogueCurioSelector(RogueSelector):
    def recognition(self):
        self.ocr_results = []
        ocr = RogueCurioOcr(OCR_ROGUE_CURIO)
        results = ocr.matched_ocr(self.main.device.image, RogueCurio)
        expect_num = 3
        if len(results) != expect_num:
            logger.warning(f"The OCR result does not match the curio count. "
                           f"Expect {expect_num}, but recognized {len(results)} only.")
        self.ocr_results = results
        return results

    def ui_select(self, target: OcrResultButton | None, skip_first_screenshot=True):
        def is_curio_selected():
            return np.mean(get_color(self.main.device.image, tuple(target.area))) > 60  # shiny background

        def is_select_curio_complete():
            """
                Case 1: back to main page
                Case 2: event page
                Case 3: is_page_choose_blessing()
                Case 4: BLESSING_ENHANCED
                Case 5: BLESSING_OBTAINED
                Case 6: BLESSING_LOST
            """
            if self.main.is_in_main():
                logger.info("Main page checked")
                return True
            if self.main.is_page_event():
                logger.info("Event page checked")
                return True
            if self.main.is_page_choose_blessing():
                logger.info("is_page_choose_blessing() checked")
                return True
            if self.main.appear(BLESSING_ENHANCED):
                logger.info("BLESSING_ENHANCED checked")
                return True
            if self.main.appear(BLESSING_OBTAINED):
                logger.info("BLESSING_OBTAINED checked")
                return True
            if self.main.appear(BLESSING_LOST):
                logger.info("BLESSING_LOST checked")
                return True
            return False

        enforce = False
        if not target:
            enforce = True
        interval = Timer(1)
        # start -> selected
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.main.device.screenshot()

            if is_curio_selected():
                if enforce:
                    logger.info("Curio selected (enforce)")
                else:
                    logger.info(f"Curio {target} selected")
                break
            if interval.reached():
                if enforce:
                    self.main.device.click(CURIO_ENFORCE)
                else:
                    self.main.device.click(target)
                interval.reset()

        skip_first_screenshot = True
        # Avoid double-clicking
        interval = Timer(3, count=6)
        # selected -> confirm
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.main.device.screenshot()

            if is_select_curio_complete():
                break
            if self.main.handle_popup_confirm():
                continue
            if interval.reached():
                self.main.device.click(BLESSING_CONFIRM)
                interval.reset()

    def try_select(self, option: OcrResultButton | str):
        if option == 'random':
            target = np.random.choice(self.ocr_results)
            self.ui_select(target)
            return True
        if option == 'unrecorded':
            for result in self.ocr_results:
                if self.main.is_unrecorded(result, (0, -720, 300, 0)):
                    self.ui_select(result)
                    return True
            return False

        if isinstance(option, OcrResultButton):
            self.ui_select(option)
            return True
        return False

    def load_filter(self):
        filter_ = CURIO_FILTER
        string = ""
        match self.main.config.RogueBlessing_PresetCurioFilter:
            case 'preset':
                string = CURIO_PRESET[self.main.config.RogueWorld_Path]
            case 'custom':
                string = self.main.config.RogueBlessing_CustomCurioFilter
        string = parse_name(string)

        if not string.endswith('random'):
            string += '> random'
        match self.main.config.RogueBlessing_SelectionStrategy:
            case 'unrecorded-first':
                string = 'unrecorded > ' + string
            case 'before-random':
                string = string.replace('random', 'unrecorded > random')

        filter_.load(string)
        self.filter_ = filter_
