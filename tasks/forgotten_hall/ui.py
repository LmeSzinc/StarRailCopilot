import numpy as np
from ppocronnx.predict_system import BoxedResult
from collections import namedtuple
import cv2

from module.base.utils import area_size, random_rectangle_vector_opted
from module.logger import logger
from tasks.base.ui import UI
from tasks.forgotten_hall.assets.assets_forgotten_hall import (
    FORGOTTEN_STAGE_ID_OCR,
    FORGOTTEN_STAGE_PREPARE
)
from module.ocr.ocr import Ocr, OcrResultButton
from module.base.button import ButtonWrapper
from module.ui.draggable_list import DraggableList
from tasks.forgotten_hall.keywords import (
    KEYWORDS_FORGOTTEN_STAGE_LIST,
    ForgottenStageId
)


class LevelStageOcr:
    class LevelStageOcrDirect(Ocr):
        def after_process(self, result):
            result = super().after_process(result)
            replace_dict = {
                "O": "0", "o": "0", "*": "",
                "109": "09", "009": "09",     # bright line close to stage09 may be recognized as 1 or 0
                "71": "11"
            }
            for k, v in replace_dict.items():
                result = result.replace(k, v)
            if self.lang == 'ch':
                result = result.replace("米", "")

            return result

    class LevelStageOcrBinary(LevelStageOcrDirect):
        def pre_process(self, image):
            # convert to binary image, threshold = 254 cause StageId is pure white
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            _, binary_image = cv2.threshold(gray_image, 230, 255, cv2.THRESH_BINARY)
            binary_image_3ch = np.stack((binary_image,) * 3, axis=-1)
            return binary_image_3ch

    def __init__(self, button: ButtonWrapper, lang=None, name=None, stage_range: tuple[int, int] = (1, 99)):
        """
        Args:
            stage_range: (min, max) stage id
            other args: see Ocr
        """
        self.ocr_direct = self.LevelStageOcrDirect(button, lang=lang, name=name)
        self.ocr_binary = self.LevelStageOcrBinary(button, lang=lang, name=name)
        self.stage_range = stage_range

    def detect_stages(self, image, direct_ocr=False) -> list[BoxedResult]:
        """
        BinaryOcr has some problem with detecting stage 11, so we use both
        """
        raw_direct_results = self.ocr_direct.detect_and_ocr(image, direct_ocr=direct_ocr)
        raw_binary_results = self.ocr_binary.detect_and_ocr(image, direct_ocr=direct_ocr)
        ocr_results = raw_direct_results + raw_binary_results
        ocr_results = list(filter(
            lambda x: x.ocr_text.isdigit() and self.stage_range[0] <= int(x.ocr_text) <= self.stage_range[1],
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

        results = self.detect_stages(image, direct_ocr=direct_ocr)
        for result in results:
            offset = (-70, -20)
            result.box = (
                result.box[0] + offset[0],
                result.box[1] + offset[1],
                result.box[2] + offset[0],
                result.box[3] + offset[1],
            )
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
