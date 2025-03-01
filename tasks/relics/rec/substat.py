from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from module.base.decorator import cached_property
from module.base.utils import area_limit, area_pad, crop, extract_letters
from module.logger import logger
from module.ocr.ocr import Ocr
from tasks.relics.assets.assets_relics_rec import REC_SUBSTAT, REC_SUBVALUE
from tasks.relics.keywords import SubStat, substat
from tasks.relics.rec.base import MatchResult, OcrResult, RelicRecBase


class RecSubStat(RelicRecBase):
    @cached_property
    def assets_substat(self) -> Dict[SubStat, np.ndarray]:
        assets = [
            substat.HP,
            substat.ATK,
            substat.DEF,
            substat.CRITRate,
            substat.CRITDMG,
            substat.SPD,
            substat.EffectHitRate,
            substat.EffectRES,
            substat.BreakEffect,
        ]
        return self.read_assets_folder(
            f'assets/{self.lang}/relics/rec_substat',
            assets,
        )

    @cached_property
    def ocr_subvalue(self):
        return Ocr(None, name='OcrSubValue')

    def _get_letter_box(self, image) -> List[Tuple[int, int, int, int]]:
        """
        Iter letter boxes from a cropped image (letter in black, background in white)
        """
        # Extract letter,
        # Letter is now in white and background in black
        blur = cv2.GaussianBlur(image, (5, 5), 0)
        cv2.subtract(blur, image, dst=blur)
        # Turn letters into rectangles
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 5))
        cv2.morphologyEx(blur, cv2.MORPH_CLOSE, kernel, dst=blur)
        cv2.inRange(blur, 17, 255, dst=blur)
        # from PIL import Image
        # Image.fromarray(blur, mode='L').show()

        rows = self.find_text_rows(blur)
        return rows

    def _get_substat_area(self, area: Tuple) -> Optional[Tuple]:
        """
        Limit area in relicset_top_y
        """
        x1, y1, x2, y2 = area
        y2 = min(y2, self.relicset_top_y)
        if y2 - y1 < 20:
            # Not enough height to a row of text
            return None
        return x1, y1, x2, y2

    def rec_subname(self, image) -> List[MatchResult[SubStat]]:
        """
        Get sub stat from image
        """
        area = self._get_substat_area(REC_SUBSTAT.area)
        if area is None:
            logger.attr('subname', [])
            return []
        image = crop(image, area, copy=False)
        image = extract_letters(image, letter=(255, 255, 255), threshold=255)

        result_list = []
        limit = (0, 0, area[2] - area[0], area[3] - area[1])
        pad = 3
        for rect in self._get_letter_box(image):
            rect = area_pad(rect, pad=-pad)
            rect = area_limit(rect, limit)
            row_image = crop(image, rect, copy=True)
            # from PIL import Image
            # Image.fromarray(row_image, mode='L').show()

            result = self.match_template(row_image, self.assets_substat)
            result.move_area_base(rect).move_area_base(area)
            result_list.append(result)

        logger.attr('subname', [r.to_log() for r in result_list])
        result_list = [r for r in result_list if r]
        return result_list

    def rec_subvalue(self, image) -> List[OcrResult]:
        """
        Get sub stat value from image
        """
        area = self._get_substat_area(REC_SUBVALUE.area)
        if area is None:
            return []
        image = crop(image, area, copy=False)

        limit = (0, 0, area[2] - area[0], area[3] - area[1])
        pad = 3
        image_list = []
        rect_list = []
        letter_image = extract_letters(image, letter=(255, 255, 255), threshold=255)
        for rect in self._get_letter_box(letter_image):
            rect = area_pad(rect, pad=-pad)
            rect = area_limit(rect, limit)
            # print(rect)
            row_image = crop(image, rect, copy=False)
            image_list.append(row_image)
            rect_list.append(rect)

        ocr = self.ocr_subvalue
        value_list = ocr.ocr_multi_lines(image_list)

        result_list = []
        for v, rect in zip(value_list, rect_list):
            r = OcrResult(result=v[0], score=v[1], area=rect)
            r.move_area_base(area)
            result_list.append(r)
        return result_list
