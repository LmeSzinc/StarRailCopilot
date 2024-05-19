import re

import cv2
from pponnxcr.predict_system import BoxedResult

from module.base.utils import area_center, area_in_area
from module.logger import logger
from module.ocr.ocr import Ocr, OcrWhiteLetterOnComplexBackground
from module.ui.scroll import AdaptiveScroll
from tasks.daily.synthesize import SynthesizeUI
from tasks.planner.assets.assets_planner_result import *
from tasks.planner.keywords import ITEM_CLASSES
from tasks.planner.keywords.classes import ItemCurrency
from tasks.planner.model import PlannerMixin, PlannerResultRow

CALCULATE_TITLE.load_search(RESULT_CHECK.search)
MATERIAL_TITLE.load_search(RESULT_CHECK.search)
DETAIL_TITLE.load_search(RESULT_CHECK.search)


class OcrItemName(Ocr):
    def after_process(self, result):
        result = result.replace('念火之心', '忿火之心')
        result = re.sub('工造机$', '工造机杼', result)
        result = re.sub('工造轮', '工造迴轮', result)
        result = re.sub('月狂牙', '月狂獠牙', result)
        return result


class OcrPlannerResult(OcrWhiteLetterOnComplexBackground, OcrItemName):
    def __init__(self):
        # Planner currently CN only
        super().__init__(OCR_RESULT, lang='cn')
        self.limited_area = OCR_RESULT.area
        self.limit_y = 720

    def _match_result(
            self,
            result: str,
            keyword_classes,
            lang: str = 'cn',
            ignore_punctuation=True,
            ignore_digit=True):
        return super()._match_result(
            result,
            keyword_classes,
            lang,
            ignore_punctuation,
            ignore_digit,
        )

    def filter_detected(self, result: BoxedResult) -> bool:
        if not area_in_area(result.box, self.limited_area, threshold=0):
            return False
        if area_center(result.box)[1] > self.limit_y:
            return False
        return True

    def detect_and_ocr(self, image, *args, **kwargs):
        # Remove rows below DETAIL_TITLE
        if DETAIL_TITLE.match_template(image):
            self.limit_y = DETAIL_TITLE.button[3]
        else:
            self.limit_y = 720
        return super().detect_and_ocr(image, *args, **kwargs)

    def pre_process(self, image):
        r, g, b = cv2.split(image)
        cv2.max(r, g, dst=r)
        cv2.max(r, b, dst=r)
        image = cv2.merge([r, r, r])
        return image


class PlannerScan(SynthesizeUI, PlannerMixin):
    def is_in_planner_result(self):
        if self.appear(RESULT_CHECK):
            return True
        if self.appear(CALCULATE_TITLE):
            return True
        if self.appear(MATERIAL_TITLE):
            return True
        if self.appear(DETAIL_TITLE):
            return True
        return False

    def parse_planner_result_page(self) -> list[PlannerResultRow]:
        """
        Pages:
            in: planner result
        """
        ocr = OcrPlannerResult()
        results = ocr.detect_and_ocr(self.device.image)

        x_total = 842
        x_synthesize = 965
        x_demand = 1129

        def x_match(result: BoxedResult, x):
            rx = area_center(result.box)[0]
            return x - 50 <= rx <= x + 50

        def y_match(result: BoxedResult, y):
            rx = area_center(result.box)[1]
            return y - 15 <= rx <= y + 15

        # Split columns
        list_item = [r for r in results
                     if not r.ocr_text.isdigit() and ocr._match_result(r.ocr_text, keyword_classes=ITEM_CLASSES)]
        list_number = [r for r in results if r.ocr_text.isdigit()]
        list_total = [r for r in list_number if x_match(r, x_total)]
        list_synthesize = [r for r in list_number if x_match(r, x_synthesize)]
        list_demand = [r for r in list_number if x_match(r, x_demand)]

        # Structure
        out: list[PlannerResultRow] = []
        for item in list_item:
            y_item = area_center(item.box)[1]
            total = -1
            for number in list_total:
                if y_match(number, y_item):
                    total = int(number.ocr_text)
                    break
            synthesize = 0
            for number in list_synthesize:
                if y_match(number, y_item):
                    synthesize = int(number.ocr_text)
                    break
            demand = 0
            for number in list_demand:
                if y_match(number, y_item):
                    demand = int(number.ocr_text)
                    break
            item = ocr._match_result(item.ocr_text, keyword_classes=ITEM_CLASSES)
            row = PlannerResultRow(
                item=item,
                total=total,
                synthesize=synthesize,
                demand=demand
            )
            # Validate item
            # print(row)
            if row.total <= 0:
                logger.warning(f'Planner row with total <= 0, {row}')
                continue
            if row.synthesize < 0:
                # Credits always have `synthesize`=="-"
                if row.item.__class__ != ItemCurrency:
                    logger.warning(f'Planner row with synthesize < 0, {row}')
                    continue
            if row.demand < 0:
                logger.warning(f'Planner row with demand < 0, {row}')
                continue
            # Add
            out.append(row)

        logger.info(f'parse_planner_result_page: {out}')
        return out

    def parse_planner_result(self, skip_first_screenshot=True) -> list[PlannerResultRow]:
        """
        Pages:
            in: planner result
        """
        logger.hr('Parse planner result', level=2)
        scroll = AdaptiveScroll(RESULT_SCROLL.button, name=RESULT_SCROLL.name)
        scroll.drag_threshold = 0.1
        scroll.edge_threshold = 0.1
        scroll.parameters = {
            'height': 50,
            'prominence': 15,
            'width': 5,
        }
        if not skip_first_screenshot:
            self.device.screenshot()
            skip_first_screenshot = False
        if not scroll.at_top(main=self):
            scroll.set_top(main=self)

        out = []
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # Skip first page
            if self.appear(CALCULATE_TITLE):
                scroll.next_page(main=self, page=0.75)
                continue

            # Parse
            rows = self.parse_planner_result_page()
            for row in rows:
                if row not in out:
                    out.append(row)
            logger.attr('PlannerResult', len(rows))

            # Scroll
            if scroll.at_bottom(main=self):
                logger.info('Reached scroll end, stop')
                break
            elif self.appear(DETAIL_TITLE):
                logger.info('Reached DETAIL_TITLE, stop')
                break
            else:
                scroll.next_page(main=self, page=0.8)

        logger.hr('Planner Result')
        for row in out:
            logger.info(f'Planner item: {row.item.name}, {row.total}, {row.synthesize}, {row.demand}')

        self.planner_write_results(out)
        return out

    def run(self):
        self.device.screenshot()
        self.parse_planner_result()


if __name__ == '__main__':
    self = PlannerScan('src', task='PlannerScan')
    self.device.screenshot()
    self.parse_planner_result()
