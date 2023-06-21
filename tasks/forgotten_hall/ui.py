import numpy as np
from ppocronnx.predict_system import BoxedResult
import cv2
import time
from operator import attrgetter
from functools import reduce

from module.logger import logger
from tasks.base.ui import UI
from tasks.forgotten_hall.assets.assets_forgotten_hall import (
    FORGOTTEN_STAGE_ID_OCR,
    FORGOTTEN_STAGE_PREPARE
)
from module.ocr.ocr import Ocr, OcrResultButton
from module.base.button import ButtonWrapper
from module.ui.draggable_list import DraggableList
from module.base.utils import area_offset, crop, float2str, color_similarity_2d

from tasks.forgotten_hall.keywords import (
    KEYWORDS_FORGOTTEN_STAGE_LIST,
    ForgottenStageId
)


class LevelStageOcr(Ocr):
    def __init__(self, button: ButtonWrapper, lang=None, name=None, stage_range: tuple[int, int] = (1, 99)):
        """
        Args:
            stage_range: (min, max) stage id
            other args: see Ocr
        """
        super().__init__(button, lang=lang, name=name)
        self.stage_range = stage_range

    def pre_process(self, image):
        # convert to binary image, threshold = 254 cause StageId is pure white
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary_image = cv2.threshold(gray_image, 220, 255, cv2.THRESH_BINARY)
        binary_image_3ch = np.stack((binary_image,) * 3, axis=-1)
        return binary_image_3ch

    def after_process(self, result):
        result = super().after_process(result)
        replace_dict = {
            "O": "0", "o": "0", "*": "",
            ".": ""
        }
        for k, v in replace_dict.items():
            result = result.replace(k, v)
        if self.lang == 'ch':
            result = result.replace("米", "")

        return result

    def format_result(self, result: str) -> int:
        if result.isdigit() and self.stage_range[0] <= int(result) <= self.stage_range[1] and len(result) == 2:
            return int(result)
        else:
            return -1

    def _detect_stage_rectangles(self, raw_image):
        """
        Args:
            raw_image: image
        Returns:
            List of boxes containing stage id, in (x1, y1, x2, y2) format
        """
        image = crop(raw_image, self.button.area)
        yellow = color_similarity_2d(image, color=(250, 201, 111))
        gray = color_similarity_2d(image, color=(100, 109, 134))
        image = np.maximum(yellow, gray)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 3))
        image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)

        _, image = cv2.threshold(image, 210, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        rectangle = []
        for cont in contours:
            rect = cv2.boundingRect(cv2.convexHull(cont).astype(np.float32))
            # Filter with rectangle width
            if not 40 < rect[2] < 80:
                continue
            rect = (rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3])
            rect = area_offset(rect, offset=self.button.area[:2])
            # Move from stars to letters
            rect = area_offset((-10, -55, 50, -15), offset=rect[:2])
            rectangle.append(rect)
        return rectangle

    def _ocr_multi_lines(self, image, boxes) -> list[BoxedResult]:
        """
        Args:
            image:
            boxes: [(x1, y1, x2, y2), ...] format
        """
        start_time = time.time()
        image = self.pre_process(image)
        results = []
        for box in boxes:
            text_image = crop(image, box)
            result, score = self.model.ocr_single_line(text_image)
            result = self.after_process(result)
            results.append(BoxedResult(box, text_image, result, score))
        logger.attr(name='%s %ss' % (self.name, float2str(time.time() - start_time)),
                    text=str(results))
        return results

    def _ocr_stages(self, image) -> list[BoxedResult]:
        stage_rectangles = self._detect_stage_rectangles(image)
        return self._ocr_multi_lines(image, stage_rectangles)

    def detect_and_ocr_stages(self, image) -> list[BoxedResult]:
        ocr_results = self._ocr_stages(image)
        for ocr_result in ocr_results:
            ocr_result.ocr_text = self.format_result(ocr_result.ocr_text)
        ocr_results = filter(lambda x: x.ocr_text > 0, ocr_results)
        # eliminate duplicate and sort by key
        ocr_results = sorted(reduce(lambda dic, data: (dic.update({data.ocr_text: data}) if data.ocr_text not in dic or
                                    dic[data.ocr_text].score < data.score else None) or dic,
                                    ocr_results, {}).values(), key=attrgetter('ocr_text'))
        # find longest consecutive
        split_points = np.where(np.diff(list(map(attrgetter('ocr_text'), ocr_results))) != 1)[0] + 1
        longest_consecutive = max(np.array_split(ocr_results, split_points), key=len)
        for result in longest_consecutive:
            result.ocr_text = str(result.ocr_text)
        return list(longest_consecutive) if len(longest_consecutive) >= 4 else []

    def matched_ocr(self, image, keyword_classes, direct_ocr=False) -> list[OcrResultButton]:
        """
        See Ocr.matched_ocr
        """
        if not isinstance(keyword_classes, list):
            keyword_classes = [keyword_classes]

        results = self.detect_and_ocr_stages(image)
        for result in results:
            result.box = area_offset(result.box, (-70, -20))
        results = filter(lambda x: x.box[0] > 0, results)
        results = [
            OcrResultButton(result, keyword_classes)
            for result in results
        ]
        results = [result for result in results if result.matched_keyword is not None]
        logger.attr(name=f'LevelStageOcr matched', text=results)
        return results


class StageDraggableList(DraggableList):
    def is_row_selected(self, row, main) -> bool:
        button = self.keyword2button(row)
        if not button:
            return False
        if main.appear(FORGOTTEN_STAGE_PREPARE):
            return True
        return False


FORGOTTEN_STAGE_LIST = StageDraggableList(
    'ForgottenStageList', keyword_class=ForgottenStageId, ocr_class=LevelStageOcr, search_button=FORGOTTEN_STAGE_ID_OCR,
    drag_direction='right')


class ForgottenHall(UI):
    stage_range = (1, 99)
    _stage_entry_format = 'ForgottenStageId_%02d'

    def _check_stage_valid(self, stage: int) -> bool:
        if not isinstance(stage, int) or not self.stage_range[0] <= stage <= self.stage_range[1]:
            return False
        if not hasattr(KEYWORDS_FORGOTTEN_STAGE_LIST, self._stage_entry_format % stage):
            return False
        return True

    def insight_stage(self, stage: int) -> bool:
        """
        Pages:
            in: main page of ForgottenHall
            out: main page of ForgottenHall with stage insight
        """
        logger.info(f'Insight stage: {stage}')
        if not self._check_stage_valid(stage):
            logger.warning(f'Invalid stage: {stage}')
            return False
        return FORGOTTEN_STAGE_LIST.insight_row(
            getattr(KEYWORDS_FORGOTTEN_STAGE_LIST, self._stage_entry_format % stage), self)

    def goto_stage(self, stage: int) -> bool:
        """
        Pages:
            in: main page of ForgottenHall
            out: prepare page of stage
        """
        logger.info(f'Goto stage: {stage}')
        if not self._check_stage_valid(stage):
            logger.warning(f'Invalid stage: {stage}')
            return False
        return FORGOTTEN_STAGE_LIST.select_row(
            getattr(KEYWORDS_FORGOTTEN_STAGE_LIST, self._stage_entry_format % stage), self)


class ForgottenHallNormal(ForgottenHall):
    """
    The_Last_Vestiges_of_Towering_Citadel

    Examples:
    ui = ForgottenHallNormal('alas')
    ui.device.screenshot()
    ui.goto_stage(1)
    """
    stage_range = (1, 15)


class ForgottenHallChaos(ForgottenHall):
    stage_range = (1, 10)
