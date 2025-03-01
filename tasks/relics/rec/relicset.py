from typing import Dict, Optional

import cv2
import numpy as np

from module.base.decorator import cached_property
from module.base.utils import area_pad, crop, extract_letters
from module.logger import logger
from tasks.relics.assets.assets_relics_rec import REC_RELICSET
from tasks.relics.keywords import RelicSet
from tasks.relics.rec.base import MatchResult, RelicRecBase


class RecRelicSet(RelicRecBase):
    @cached_property
    def assets_relicset(self) -> Dict[RelicSet, np.ndarray]:
        assets = RelicSet.instances.values()
        return self.read_assets_folder(
            f'assets/{self.lang}/relics/rec_relicset',
            assets,
        )

    def rec_relicset(self, image) -> Optional[MatchResult[RelicSet]]:
        """
        Get relic set from image
        """
        area = REC_RELICSET.area
        image = crop(image, area, copy=False)

        # Find orange names
        letter_image = extract_letters(image, letter=(235, 161, 66), threshold=128)
        blur = cv2.GaussianBlur(letter_image, (5, 5), 0)
        cv2.subtract(blur, letter_image, dst=blur)
        # Turn letters into rectangles
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 5))
        cv2.morphologyEx(blur, cv2.MORPH_CLOSE, kernel, dst=blur)
        cv2.inRange(blur, 17, 255, dst=blur)
        # from PIL import Image
        # Image.fromarray(blur, mode='L').show()

        # Find rectangles
        rows = self.find_text_rows(blur, max_height=30)
        # Pick the first row of text
        # In EN, names of relic set are long and may have two rows, we detect the first row only
        try:
            rect = rows[0]
        except IndexError:
            logger.warning(f'Empty relic set rows')
            return None

        # Re-extract text
        rect = area_pad(rect, pad=-4)
        letter_image = crop(image, rect, copy=False)
        letter_image = extract_letters(letter_image, letter=(235, 161, 66), threshold=255)
        # from PIL import Image
        # Image.fromarray(letter_image, mode='L').show()

        result = self.match_template(letter_image, self.assets_relicset)
        result.move_area_base(rect).move_area_base(area)
        logger.attr('relicset', result.to_log())
        self.relicset_top_y = result.area[1]
        if result:
            return result
        else:
            return None
