import numpy as np
from ppocronnx.predict_system import BoxedResult
from collections import namedtuple
import cv2
import time

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

    def _ocr_single_stage(self, image, rect):
        """
        Args:
            image: binary image
            rect: (x1, y1, x2, y2) format
        Returns:
            (image, result, score)
        """
        start_time = time.time()
        text_image = crop(image, rect)
        result, score = self.model.ocr_single_line(text_image)
        result = self.after_process(result)
        logger.attr(name='%s %ss' % (self.name, float2str(time.time() - start_time)),
                    text=str(result))
        return text_image, result, score

    def _ocr_stages(self, image) -> list[BoxedResult]:
        stage_rectangles = self._detect_stage_rectangles(image)
        # cv2.imshow("", draw(image, stage_rectangles))
        # cv2.waitKey(0)

        image = self.pre_process(image)
        stages = []
        for rect in stage_rectangles:
            text_image, result, score = self._ocr_single_stage(image, rect)
            stages.append(BoxedResult(rect, text_image, result, score))

        return stages

    def detect_and_ocr_stages(self, image) -> list[BoxedResult]:
        ocr_results = self._ocr_stages(image)
        ocr_results = list(filter(
            lambda x: x.ocr_text.isdigit() and len(x.ocr_text) == 2
            and self.stage_range[0] <= int(x.ocr_text) <= self.stage_range[1],
            ocr_results))
        # eliminate duplicate
        ocr_results_dict = {}
        for ocr_result in ocr_results:
            if ocr_result.ocr_text not in ocr_results_dict:
                ocr_results_dict[ocr_result.ocr_text] = ocr_result
            elif ocr_result.score > ocr_results_dict[ocr_result.ocr_text].score:
                ocr_results_dict[ocr_result.ocr_text] = ocr_result
        ocr_results = list(ocr_results_dict.values())
        ocr_results.sort(key=lambda x: int(x.ocr_text))
        # find longest consecutive
        seq_start, seq_end = 0, 0
        max_seq_len = 1
        i, j = 0, 0
        while j < len(ocr_results):
            if int(ocr_results[j].ocr_text) - int(ocr_results[i].ocr_text) == j - i:
                j += 1
            else:
                if j - i > max_seq_len:
                    max_seq_len = j - i
                    seq_start, seq_end = i, j
                i = j
        if j - i > max_seq_len:
            max_seq_len = j - i
            seq_start, seq_end = i, j
        return ocr_results[seq_start:seq_end] if max_seq_len >= 4 else []

    def matched_ocr(self, image, keyword_classes, direct_ocr=False) -> list[OcrResultButton]:
        """
        See Ocr.matched_ocr
        """
        if not isinstance(keyword_classes, list):
            keyword_classes = [keyword_classes]

        results = self.detect_and_ocr_stages(image)
        for result in results:
            offset = (-70, -20)
            result.box = area_offset(result.box, offset)
        results = [
            OcrResultButton(result, keyword_classes)
            for result in results
        ]
        results = [result for result in results if result.matched_keyword is not None]
        logger.attr(name=f'LevelStageOcr matched',
                    text=results)
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

    def goto_stage(self, stage: int, skip_first_screenshot=True) -> bool:
        """
        Pages:
            in: main page of ForgottenHall
            out: prepare page of stage
        """
        logger.info(f'Goto stage: {stage}')
        return FORGOTTEN_STAGE_LIST.select_row(KEYWORDS_FORGOTTEN_STAGE_LIST.ForgottenStageId_01, self)


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
