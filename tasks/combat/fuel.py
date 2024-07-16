
import module.config.server as server

from module.base.utils import crop, area_offset
from module.logger import logger
from module.ocr.ocr import Digit
from tasks.base.assets.assets_base_popup import POPUP_CONFIRM, POPUP_CANCEL
from tasks.base.ui import UI
from tasks.item.slider import Slider
from tasks.combat.assets.assets_combat_finish import COMBAT_AGAIN
from tasks.combat.assets.assets_combat_prepare import (
    COMBAT_PREPARE,
    EXTRACT_RESERVED_TRAILBLAZE_POWER,
    FUEL,
    FUEL_MINUS,
    FUEL_PLUS,
    FUEL_SELECTED,
    OCR_FUEL,
    OCR_FUEL_COUNT,
    OCR_RESERVED_TRAILBLAZE_POWER,
    OCR_EXTRACT_RESERVED_TRAILBLAZE_POWER_COUNT,
    RESERVED_TRAILBLAZE_POWER_ENTRANCE,
    RESERVED_MINUS,
    RESERVED_PLUS,
    RESERVED_SLIDER,
    FUEL_ENTRANCE,
    USING_FUEL,
    FUEL_SLIDER
)


class Fuel(UI):
    fuel_trailblaze_power = 60
    trailblaze_max_limit = 240

    def _use_fuel_finish(self):
        """
        Two possible finish states after using fuel/extract trailblaze power:
        1. COMBAT_PREPARE
        2. COMBAT_AGAIN
        """
        return self.appear(COMBAT_PREPARE) or self.appear(COMBAT_AGAIN)
        
    def extract_reserved_trailblaze_power(self, current, skip_first_screenshot=True):
        """
        Extract reserved trailblaze power from previous combat.

        Returns:
            int: Reserved trailblaze power
        """
        logger.info('Extract reserved trailblaze power')
        reserved = Digit(OCR_RESERVED_TRAILBLAZE_POWER).ocr_single_line(self.device.image)
        if reserved == 0:
            logger.info('No reserved trailblaze power')
            return

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            
            if self.appear(POPUP_CONFIRM):
                break
            if self.appear_then_click(EXTRACT_RESERVED_TRAILBLAZE_POWER):
                continue
            if self.appear_then_click(RESERVED_TRAILBLAZE_POWER_ENTRANCE):
                continue

        count = min(reserved, self.trailblaze_max_limit - current)
        self.set_reserved_trailblaze_power(count, total=reserved)

        skip_first_screenshot = True

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._use_fuel_finish():
                break
            if self.appear_then_click(POPUP_CONFIRM):
                continue
            if self.handle_reward():
                continue

    def set_reserved_trailblaze_power(self, count, total):
        slider = Slider(main=self, slider=RESERVED_SLIDER)
        slider.set(count, total)
        self.ui_ensure_index(
            count, letter=Digit(OCR_EXTRACT_RESERVED_TRAILBLAZE_POWER_COUNT, lang=server.lang),
            next_button=RESERVED_PLUS, prev_button=RESERVED_MINUS,
            skip_first_screenshot=True
        )

    def set_fuel_count(self, count, total):
        slider = Slider(main=self, slider=FUEL_SLIDER)
        slider.set(count, total)
        self.ui_ensure_index(
            count, letter=Digit(OCR_FUEL_COUNT, lang=server.lang),
            next_button=FUEL_PLUS, prev_button=FUEL_MINUS,
            skip_first_screenshot=True
        )

    def use_fuel(self, current, skip_first_screenshot=True):
        need = (self.trailblaze_max_limit - current) // self.fuel_trailblaze_power
        if need == 0:
            logger.info(f"Current trailblaze power is near {self.trailblaze_max_limit}, no need to use fuel")
            return

        logger.info("Use Fuel")
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(POPUP_CONFIRM) and not (self.appear(FUEL_SELECTED) and self.appear(FUEL)):
                logger.info("No fuel found")
                return 
            if self.appear(FUEL_SELECTED):
                break
            if self.appear_then_click(FUEL):
                continue
            if self.appear_then_click(FUEL_ENTRANCE):
                continue

        offset = FUEL_SELECTED.button_offset
        count = Digit(OCR_FUEL).ocr_single_line(crop(self.device.image, area_offset(OCR_FUEL.area, offset)),
                                                direct_ocr=True)

        available_count = count - self.config.TrailblazePower_UseFuelUntilRemainCount
        need = min(need, available_count)
        if need <= 0:
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

            if self.appear(USING_FUEL):
                break
            if self.appear(FUEL) and self.appear_then_click(POPUP_CONFIRM):
                continue
        
        self.set_fuel_count(need, count)

        skip_first_screenshot = True

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._use_fuel_finish():
                break
            if self.appear_then_click(POPUP_CONFIRM):
                continue
            if self.handle_reward():
                continue