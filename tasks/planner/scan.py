import re
import cv2
from pponnxcr.predict_system import BoxedResult
from tkinter import filedialog
from lxml import etree

from module.base.utils import area_center, area_in_area
from module.exception import GamePageUnknownError
from module.logger import logger
from module.ocr.ocr import Ocr, OcrWhiteLetterOnComplexBackground
from module.ui.scroll import AdaptiveScroll
from tasks.base.page import page_planner
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
        result = re.sub('^火之心', '忿火之心', result)
        result = re.sub('工造机$', '工造机杼', result)
        result = re.sub('工造迥?轮', '工造迴轮', result)
        result = re.sub('月狂[療撩]?牙', '月狂獠牙', result)
        # 毁灭者的未路 思绪末屑
        result = result.replace('未路', '末路')
        result = result.replace('未屑', '末屑')
        result = result.replace('粉未', '粉末')
        # Error words on blank background
        result = re.sub('^[國東]', '', result)
        result = re.sub('時$', '', result)
        return result


class OcrPlannerResult(OcrWhiteLetterOnComplexBackground, OcrItemName):
    min_box = (16, 20)

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
        image = cv2.subtract((255, 255, 255, 0), image)
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
        if self.config.PlannerScan_ParseHTML:
            out = self.parse_planner_html()
            return out
        if not self.ui_page_appear(page_planner):
            logger.error('Not in page_planner, game must in the planner result page before scanning')
            raise GamePageUnknownError

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

    def parse_planner_html(self):
        my_filetypes = [('HTML files', '*.htm;*.html'), ('all files', '.*')]
        # TODO: dialog title i18n
        html_filename = filedialog.askopenfilename(title="Please select saved plan page:",
                                                   filetypes=my_filetypes)
        with open(html_filename, 'r', encoding='utf-8') as file:
            html_content = file.read()

        tree = etree.parse(html_filename, etree.HTMLParser())

        # find cost-table-row
        rows = tree.xpath('//div[starts-with(@class, "cost-table-row")]')
        img_name_table: dict[str, str] = {}
        results: dict[str, PlannerResultRow] = {}
        ocr = OcrPlannerResult()

        for row in rows:
            # get total num; create img to item name table
            item_name = row.xpath(
                './/div[starts-with(@class, "td td-name")]/div[@class="name"]/text()')[0].strip()
            img_src = row.xpath(
                './/div[starts-with(@class, "td td-icon")]//img/@src')[0].strip()
            img_name = re.search(r'([^/]+\.png)$', img_src).group(1)
            img_name_table[img_name] = item_name
            total_str = row.xpath(
                './/div[@class="td td-needs"]/text()')[0].strip()
            total_num = int(total_str)
            if item_name not in results:
                item = ocr._match_result(
                    item_name, keyword_classes=ITEM_CLASSES, lang=self.config.Emulator_GameLanguage)
                results[item_name] = PlannerResultRow(
                    item=item, total=total_num, synthesize=0, demand=0)

        result_inventory_required = tree.xpath(
            '//div[@class="result-inventory-part part part-required"]/div[@class="cards"]/div')  # 需刷取
        # result_inventory_payable = tree.xpath(
        #     '//div[@class="result-inventory-part part part-payable"]/div[@class="cards"]/div')  # 可消耗
        result_inventory_remaining = tree.xpath(
            '//div[@class="result-inventory-part part part-remaining"]/div[@class="cards"]/div')  # 可合成

        def _html_write_row(result_inventory, results: dict[str, PlannerResultRow], field: str):
            # get item name
            img_src = result_inventory.xpath(
                './/div[@class="img-wrapper"]/img/@src')[0].strip()
            img_name = re.search(r'([^/]+\.png)$', img_src).group(1)
            if img_name not in img_name_table:
                raise KeyError(
                    f"Unknown image name {img_name}")
            item_name = img_name_table[img_name]
            # get num
            count_str = result_inventory.xpath(
                './/div[starts-with(@class, "count")]/text()')[0].strip()
            count = int(count_str)

            # TODO:如何不依靠if else实现result添加？能否不使用dict对应item_name和PlannerResultRow？
            if item_name in results:
                if field == "total":
                    results[item_name].total = count
                elif field == "synthesize":
                    results[item_name].synthesize = count
                elif field == "demand":
                    results[item_name].demand = count

        for row in result_inventory_required:  # 需刷取
            _html_write_row(row, results, "demand")
        # for row in result_inventory_payable:  # 可消耗
        #     _html_write_row(row, results, "synthesize")
        for row in result_inventory_remaining:  # 可合成
            _html_write_row(row, results, "synthesize")
        results: list[PlannerResultRow] = list(results.values())
        logger.hr('Planner Result')
        for row in results:
            logger.info(
                f'Planner item: {row.item.name}, {row.total}, {row.synthesize}, {row.demand}')

        self.planner_write_results(results)
        return results

    def run(self):
        self.device.screenshot()
        self.parse_planner_result()


if __name__ == '__main__':
    self = PlannerScan('src', task='PlannerScan')
    self.device.screenshot()
    self.parse_planner_result()
