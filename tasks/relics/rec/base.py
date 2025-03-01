from dataclasses import dataclass
import os
from functools import reduce
from typing import Any, Dict, Generic, List, Tuple, TypeVar

import cv2
import numpy as np

from module.base.utils import area_offset, image_size, load_image, xywh2xyxy
from module.logger import logger

T = TypeVar('T')


def merge_two_rects(
        r1: Tuple[int, int, int, int],
        r2: Tuple[int, int, int, int]
) -> Tuple[int, int, int, int]:
    return (
        min(r1[0], r2[0]),  # left
        min(r1[1], r2[1]),  # top
        max(r1[2], r2[2]),  # right
        max(r1[3], r2[3])  # bottom
    )


@dataclass
class MatchResult(Generic[T]):
    result: T
    sim: float
    confidence: float
    area: Tuple[int, int, int, int]

    def to_log(self):
        name = self.result.name if self.result is not None else None
        return name, self.sim, self.confidence

    def __bool__(self):
        return self.result is not None

    def move_area_base(self, area: Tuple[int, int, int, int]):
        self.area = area_offset(self.area, offset=area[:2])
        return self


@dataclass
class OcrResult:
    result: str
    score: float
    area: Tuple[int, int, int, int]

    def move_area_base(self, area: Tuple[int, int, int, int]):
        self.area = area_offset(self.area, offset=area[:2])
        return self


class RelicRecBase:
    def __init__(self, lang='cn'):
        self.lang = lang
        self.root = os.path.abspath(os.path.join(__file__, '../../../../'))

        # Relics can have 0~4 substats, record the top of relic set to limit search area of substats
        self.relicset_top_y: int = 488

    def path(self, file: str) -> str:
        """
        A fast alternative of os.path.normpath
        """
        return f"{self.root}/{file}".replace('/', os.sep)

    def reset(self):
        self.relicset_top_y = 488

    def read_assets_folder(self, folder: str, keywords: List):
        assets = {}
        for keyword in keywords:
            file = self.path(f'{folder}/{keyword.name}.png')
            try:
                image = load_image(file)
            except FileNotFoundError:
                logger.error(f'Assets file not exist: {folder}/{keyword.name}.png')
                continue
            assets[keyword] = image
        return assets

    @staticmethod
    def match_template(
            image: np.ndarray,
            templates: Dict[Any, np.ndarray],
            min_sim: float = 0.
    ) -> MatchResult:
        """
        Args:
            image: Monochrome image
            templates: Templates to match
            min_sim:

        Returns:
            matched keyword or None, sim, confidence
        """
        sim_list = []
        ix, iy = image_size(image)
        for name, template in templates.items():
            # Check template size
            tx, ty = image_size(template)
            if tx > ix or ty > iy:
                continue
            res = cv2.matchTemplate(template, image, cv2.TM_CCOEFF_NORMED)
            _, sim, _, point = cv2.minMaxLoc(res)
            sim = round(sim, 3)
            area = (point[0], point[1], point[0] + tx, point[1] + ty)
            sim_list.append((name, sim, area))
            # print(name, sim, area)

        # Sort results
        sim_list = sorted(sim_list, key=lambda s: s[1], reverse=True)

        # No results
        try:
            first = sim_list[0]
        except IndexError:
            logger.warning(f'No relic match: {list(templates.keys())}')
            return MatchResult(result=None, sim=0., confidence=0., area=(0, 0, 0, 0))
        # Check best sim
        first_name, first_sim, first_area = first
        if first_sim <= min_sim:
            logger.warning(f'Low similarity relic match: {sim_list}')
            return MatchResult(result=None, sim=0., confidence=0., area=(0, 0, 0, 0))
        # Only 1 result
        try:
            second = sim_list[1]
        except IndexError:
            logger.warning(f'Only one relic match: {sim_list}')
            return MatchResult(result=first_name, sim=first_sim, confidence=1., area=first_area)
        # Multiple results
        confidence = round((first_sim - max(second[1], 0)) / first_sim, 3)
        if confidence > 0.15:
            # Best match is much better than second
            return MatchResult(result=first_name, sim=first_sim, confidence=confidence, area=first_area)
        else:
            # Poor match
            logger.warning(f'Poor relic match: {sim_list}')
            return MatchResult(result=first_name, sim=first_sim, confidence=confidence, area=first_area)

    @staticmethod
    def find_text_rows(image, merge=8, max_height=25) -> List[Tuple[int, int, int, int]]:
        """
        Find rectangles of a row of text from given image,
        auto merge multiple words into one row

        Args:
            image:
            merge: Merge word rectangles if their center_y from each other <= 8
            max_height: Drop words that have height > 25

        Returns:
            list: List of area
        """
        # Find rectangles
        list_word = []
        contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cont in contours:
            rect = cv2.boundingRect(cv2.convexHull(cont).astype(np.float32))
            rect = xywh2xyxy(rect)
            # Check max_height
            if rect[3] - rect[1] > max_height:
                logger.warning(f'Text row too high: {rect}')
                continue
            center_y = (rect[1] + rect[3]) // 2
            list_word.append((rect, center_y))

        # Sort
        list_word = sorted(list_word, key=lambda x: x[1])

        # Merge words
        list_row = []
        current_row = []
        current_center = None
        for rect, center_y in list_word:
            if not current_row:
                current_row.append(rect)
                current_center = center_y
            elif abs(center_y - current_center) <= merge:
                current_row.append(rect)
            else:
                list_row.append(reduce(merge_two_rects, current_row))
                current_row = [rect]
                current_center = center_y

        if current_row:
            list_row.append(reduce(merge_two_rects, current_row))

        return list_row
