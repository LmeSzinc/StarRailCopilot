import re

from module.base.decorator import cached_property
from module.logger import logger
from module.ocr.ocr import Ocr
from tasks.relics.assets.assets_relics_rec import REC_RELICLEVEL
from tasks.relics.rec.base import RelicRecBase


class RecRelicLevel(RelicRecBase):
    @cached_property
    def ocr_reliclevel(self):
        return Ocr(REC_RELICLEVEL, name='OcrRelicLevel')

    def rec_reliclevel(self, image) -> int:
        """
        Get relic level from image
        """
        ocr = self.ocr_reliclevel
        result = ocr.ocr_single_line(image)

        # Use Ocr class directly instead of inheriting Digit class to reduce logging
        # In current ALAS framework, logging would take 1~2ms
        result = result.strip().replace(' ', '').replace('+', '')
        result = result.replace('O', '0')

        res = re.search(r'(\d+)', result)
        if res:
            return int(res.group(1))
        else:
            logger.warning(f'No digit found in {result}')
            return -1
