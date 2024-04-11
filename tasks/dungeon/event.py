import re

from module.logger import logger
from module.ocr.ocr import DigitCounter
from tasks.base.ui import UI
from tasks.dungeon.assets.assets_dungeon_event import (
    DOUBLE_CALYX_EVENT_TAG,
    DOUBLE_RELIC_EVENT_TAG,
    DOUBLE_ROGUE_EVENT_TAG,
    OCR_DOUBLE_EVENT_REMAIN,
    OCR_DOUBLE_EVENT_REMAIN_AT_COMBAT,
    OCR_DOUBLE_ROGUE_REMAIN,
)


class DoubleEventOcr(DigitCounter):
    def after_process(self, result):
        result = super().after_process(result)
        # re.sub as last resort, just in case
        # x12 -> x/12 but x112 does not change
        result = re.sub(r'(?<!\d)(\d[02-9]*)12$', r'\1/12', result)
        # x112 -> x/12
        result = re.sub(r'112$', '/12', result)
        return result


class DungeonEvent(UI):
    def has_double_calyx_event(self) -> bool:
        """
        Pages:
            in: page_guide, Survival_Index, nav at top
        """
        has = self.image_color_count(DOUBLE_CALYX_EVENT_TAG, color=(252, 209, 123), threshold=221, count=50)
        has |= self.image_color_count(DOUBLE_CALYX_EVENT_TAG, color=(252, 251, 140), threshold=221, count=50)
        logger.attr('Double calyx', has)
        return has

    def has_double_relic_event(self) -> bool:
        """
        Pages:
            in: page_guide, Survival_Index, nav at top
        """
        has = self.image_color_count(DOUBLE_RELIC_EVENT_TAG, color=(252, 209, 123), threshold=221, count=50)
        has |= self.image_color_count(DOUBLE_RELIC_EVENT_TAG, color=(252, 251, 140), threshold=221, count=50)
        logger.attr('Double relic', has)
        return has

    def has_double_rogue_event(self) -> bool:
        """
        Pages:
            in: page_guide, Survival_Index, nav at top
        """
        has = self.image_color_count(DOUBLE_ROGUE_EVENT_TAG, color=(252, 209, 123), threshold=221, count=50)
        has |= self.image_color_count(DOUBLE_ROGUE_EVENT_TAG, color=(252, 251, 140), threshold=221, count=50)
        # Anniversary 3x rogue event
        has |= self.image_color_count(DOUBLE_ROGUE_EVENT_TAG, color=(229, 62, 44), threshold=221, count=50)
        logger.attr('Double rogue', has)
        return has

    def has_double_event_at_combat(self) -> bool:
        """
        Pages:
            in: COMBAT_PREPARE
        """
        has = self.image_color_count(
            OCR_DOUBLE_EVENT_REMAIN_AT_COMBAT,
            color=(231, 188, 103),
            threshold=240, count=1000
        )
        logger.attr('Double event at combat', has)
        return has

    def _get_double_event_remain(self, button) -> int:
        ocr = DoubleEventOcr(button)
        remain, _, total = ocr.ocr_single_line(self.device.image)
        if total not in [3, 12]:
            logger.warning(f'Invalid double event remain')
            remain = 0
        return remain

    def get_double_event_remain(self) -> int:
        """
        Pages:
            in: page_guide, Survival_Index, selected at the nav with double event
        """
        remain = self._get_double_event_remain(OCR_DOUBLE_EVENT_REMAIN)
        logger.attr('Double event remain', remain)
        return remain

    def get_double_rogue_remain(self) -> int:
        """
        Pages:
            in: page_guide, Survival_Index, selected at the nav with double event
        """
        remain = self._get_double_event_remain(OCR_DOUBLE_ROGUE_REMAIN)
        logger.attr('Double event remain', remain)
        return remain

    def get_double_event_remain_at_combat(self) -> int | None:
        """
        Pages:
            in: COMBAT_PREPARE
        """
        if not self.has_double_event_at_combat():
            logger.attr('Double event remain at combat', 0)
            return 0

        ocr = DoubleEventOcr(OCR_DOUBLE_EVENT_REMAIN_AT_COMBAT)
        for row in ocr.detect_and_ocr(self.device.image):
            if not ocr.is_format_matched(row.ocr_text):
                continue
            remain, _, total = ocr.format_result(row.ocr_text)
            if total in [3, 12]:
                logger.attr('Double event remain at combat', remain)
                return remain
        logger.warning('Double event appears but failed to get remain')
        logger.attr('Double event remain at combat', None)
        return None
