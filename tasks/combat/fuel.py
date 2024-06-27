from module.base.utils import crop, area_offset
from module.logger import logger
from module.ocr.ocr import Digit
from tasks.base.assets.assets_base_popup import POPUP_CONFIRM, POPUP_CANCEL
from tasks.base.ui import UI
from tasks.combat.assets.assets_combat_prepare import (
    EXTRACT_RESERVED_TRAILBLAZE_POWER,
    FUEL,
    FUEL_SELECTED,
    OCR_FUEL,
    OCR_RESERVED_TRAILBLAZE_POWER,
    RESERVED_TRAILBLAZE_POWER_ENTRANCE,
    FUEL_ENTRANCE,
)


class Fuel(UI):
    def extract_reserved_trailblaze_power(self, skip_first_screenshot=True):
        """
        Extract reserved trailblaze power from previous combat.

        Returns:
            int: Reserved trailblaze power
        """
        logger.info('Extract reserved trailblaze power')
        current = Digit(OCR_RESERVED_TRAILBLAZE_POWER).ocr_single_line(self.device.image)
        if current == 0:
            logger.info('No reserved trailblaze power')
            return

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear_then_click(EXTRACT_RESERVED_TRAILBLAZE_POWER):
                continue
            if self.appear_then_click(RESERVED_TRAILBLAZE_POWER_ENTRANCE):
                continue
            if self.appear_then_click(POPUP_CONFIRM):
                continue
            if self.handle_reward():
                break

    def use_fuel(self, skip_first_screenshot=True):
        logger.info("Use Fuel")
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if not self.appear(FUEL) and not self.appear(FUEL_SELECTED):
                logger.info("No fuel found")
                return 
            if self.appear(FUEL_SELECTED):
                break
            if self.appear_then_click(FUEL):
                continue
            if self.appear_then_click(FUEL_ENTRANCE):
                continue
            if self.handle_reward():
                break

        offset = FUEL_SELECTED.button_offset
        count = Digit(OCR_FUEL).ocr_single_line(crop(self.device.image, area_offset(OCR_FUEL.area, offset)),
                                                direct_ocr=True)
        if count <= self.config.Dungeon_UseFuelUntilRemainCount:
            logger.info("Fuel remain is under the threshold, stop using fuel")
            while 1:
                self.device.screenshot()
                if self.appear_then_click(POPUP_CANCEL):
                    return

        skip_first_screenshot = True

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.handle_reward():
                break
            # by default, use one fuel each time
            if self.appear_then_click(POPUP_CONFIRM):
                continue