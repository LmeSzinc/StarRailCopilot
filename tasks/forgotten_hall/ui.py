import numpy as np
from ppocronnx.predict_system import BoxedResult
from collections import namedtuple
import cv2

from module.base.utils import area_size, random_rectangle_vector_opted
from module.logger import logger
from tasks.base.ui import UI
from tasks.forgotten_hall.assets.assets_forgotten_hall import (
    FORGOTTEN_DRAG_AREA,
    FORGOTTEN_STAGE_ID_OCR,
    FORGOTTEN_STAGE_PREPARE
)
from module.ocr.ocr import Ocr, OcrResultButton
from module.base.timer import Timer
from module.base.button import ButtonWrapper


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


class ForgottenHall(UI):
    stage_range = (1, 99)

    def _drag_page(self, direction="left"):
        """
        Args:
            direction: left, right
        """
        ratio = np.random.uniform(0.8, 1)
        width, height = area_size(FORGOTTEN_DRAG_AREA.button)
        if direction == 'left':
            vector = (ratio * width, 0)
        elif direction == 'right':
            vector = (-ratio * width, 0)
        else:
            logger.warning(f'Unknown drag direction: {direction}')
            return

        p1, p2 = random_rectangle_vector_opted(vector, box=FORGOTTEN_DRAG_AREA.button)
        self.device.drag(p1, p2, name='ForgottenHall_DRAG')

    def _wait_stable(self, check_area: list[int]):
        # self.wait_until_stable(namedtuple("_CheckArea", ["area"])(area=check_area),
        #                        timer=Timer(0, count=0),
        #                        timeout=Timer(1.5, count=5))
        # need to find a proper way to wait stable, although it works fine without this now
        pass

    def _get_present_stages(self) -> list[BoxedResult]:
        """
        Get present stages in the current page
        Returns:
            list of BoxedResult, continuous and sorted by stage number, empty if not valid
        """
        ocr = LevelStageOcr(FORGOTTEN_STAGE_ID_OCR, stage_range=self.stage_range)
        results = ocr.detect_stages(self.device.image)
        return results

    def _stage_insight(self, stage: int, skip_first_screenshot=True) -> bool:
        """
        Pages:
            in: main page of ForgottenHall
            out: main page of ForgottenHall with stage insight
        """
        logger.info(f'Insight stage: {stage}')
        while 1:
            if not skip_first_screenshot:
                self.device.screenshot()
            else:
                skip_first_screenshot = False

            present_stages = self._get_present_stages()
            if not present_stages:
                logger.warning('No stage found')
                return False
            cur_min = int(present_stages[0].ocr_text)
            cur_max = int(present_stages[-1].ocr_text)

            # Found stage
            if cur_min <= stage <= cur_max:
                logger.info(f'Found stage: {stage}')
                return True

            # Drag pages
            if stage < cur_min:
                self._drag_page('left')
            elif cur_max < stage:
                self._drag_page('right')
            # Wait for swap animation
            self._wait_stable(present_stages[0].box)

    def _stage_enter(self, stage: int, skip_first_screenshot=True) -> bool:
        """
        Pages:
            in: main page of ForgottenHall with stage insight
            out: prepare page of stage
        """
        logger.info(f'Enter stage: {stage}')
        no_stage_timer = Timer(4)
        while 1:
            if not skip_first_screenshot:
                self.device.screenshot()
            else:
                skip_first_screenshot = False

            # In prepare page
            if self.appear(FORGOTTEN_STAGE_PREPARE):
                logger.info('Enter stage success')
                return True

            present_stages = self._get_present_stages()
            if not present_stages:
                if not no_stage_timer.started():
                    no_stage_timer.start()
                if no_stage_timer.reached():
                    logger.warning('No stage insight, enter stage failed')
                    return False
                continue
            cur_min = int(present_stages[0].ocr_text)
            cur_max = int(present_stages[-1].ocr_text)

            if not cur_min <= stage <= cur_max:
                logger.warning(f'stage: {stage} not insight')
                return False

            # click stage
            for stage_box in present_stages:
                if int(stage_box.ocr_text) == stage:
                    stage_icon_box = stage_box
                    offset = (-70, -20)
                    stage_icon_box.box = (
                        stage_icon_box.box[0] + offset[0],
                        stage_icon_box.box[1] + offset[1],
                        stage_icon_box.box[2] + offset[0],
                        stage_icon_box.box[3] + offset[1],
                    )
                    self.device.click(OcrResultButton(stage_box, []))
                    break

    def goto_stage(self, stage: int, skip_first_screenshot=True) -> bool:
        """
        Pages:
            in: main page of ForgottenHall
            out: prepare page of stage
        """
        logger.info(f'Goto stage: {stage}')
        if not self._stage_insight(stage, skip_first_screenshot):
            return False
        if not self._stage_enter(stage, skip_first_screenshot):
            return False
        return True


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
