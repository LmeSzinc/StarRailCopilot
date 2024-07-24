import module.config.server as server
from module.base.timer import Timer
from module.base.utils import area_offset, crop
from module.logger import logger
from module.ocr.ocr import Digit
from tasks.base.assets.assets_base_popup import GET_REWARD, POPUP_CANCEL, POPUP_CONFIRM
from tasks.base.ui import UI
from tasks.combat.assets.assets_combat_finish import COMBAT_AGAIN, COMBAT_EXIT
from tasks.combat.assets.assets_combat_fuel import *
from tasks.combat.assets.assets_combat_prepare import COMBAT_PREPARE
from tasks.item.slider import Slider


class Fuel(UI):
    fuel_trailblaze_power = 60

    def _use_fuel_finish(self):
        """
        Two possible finish states after using fuel/extract trailblaze power:
        1. COMBAT_PREPARE
        2. COMBAT_AGAIN
        """
        if self.appear(COMBAT_AGAIN):
            if self.image_color_count(COMBAT_AGAIN, color=(227, 227, 228), threshold=221, count=50):
                logger.info(f'Use fuel finished at COMBAT_AGAIN')
                return True
        if self.appear(COMBAT_PREPARE):
            if self.image_color_count(COMBAT_PREPARE.button, color=(230, 230, 230), threshold=240, count=400):
                logger.info(f'Use fuel finished at COMBAT_AGAIN')
                return True
        return False

    def _fuel_confirm(self, skip_first_screenshot=True):
        """
        Pages:
            in: fuel popup
            out: _use_fuel_finish
        """
        logger.info('Fuel confirm')
        self.interval_clear([POPUP_CONFIRM, POPUP_CANCEL, GET_REWARD])
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._use_fuel_finish():
                break
            if self.handle_popup_confirm():
                continue
            if self.handle_reward():
                continue

        self._fuel_wait_leave()
        self.interval_reset([POPUP_CONFIRM, POPUP_CANCEL], interval=2)

    def _fuel_cancel(self, skip_first_screenshot=True):
        """
        Pages:
            in: fuel popup
            out: _use_fuel_finish
        """
        logger.info('Fuel cancel')
        self.interval_clear([POPUP_CONFIRM, POPUP_CANCEL, GET_REWARD])
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._use_fuel_finish():
                break
            if self.handle_popup_cancel():
                continue
            if self.handle_reward():
                continue

        self._fuel_wait_leave()
        self.interval_reset([POPUP_CONFIRM, POPUP_CANCEL], interval=2)

    def _fuel_wait_leave(self):
        # Blur disappears before popup
        # so there's a short period of time that COMBAT_AGAIN is unclickable
        # This is equivalent to poor sleep
        timer = self.get_interval_timer(COMBAT_AGAIN, interval=5, renew=True)
        timer.set_current(4.4)
        timer = self.get_interval_timer(COMBAT_EXIT, interval=5, renew=True)
        timer.set_current(4.4)

    def extract_reserved_trailblaze_power(self, current, skip_first_screenshot=True):
        """
        Extract reserved trailblaze power from previous combat.

        Returns:
            bool: If extracted
        """
        logger.info('Extract reserved trailblaze power')
        reserved = Digit(OCR_RESERVED_TRAILBLAZE_POWER).ocr_single_line(self.device.image)
        if reserved <= 0:
            logger.info('No reserved trailblaze power')
            return False

        self.interval_clear([POPUP_CONFIRM, POPUP_CANCEL, GET_REWARD])
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

        count = min(reserved, self.config.stored.TrailblazePower.FIXED_TOTAL - current)
        logger.info(f'Having {reserved} reserved, going to use {count}')
        self.set_reserved_trailblaze_power(count, total=reserved)
        self._fuel_confirm()
        return True

    def set_reserved_trailblaze_power(self, count, total):
        slider = Slider(main=self, slider=RESERVED_SLIDER)
        slider.set(count, total)
        self.ui_ensure_index(
            count, letter=Digit(OCR_EXTRACT_RESERVED_TRAILBLAZE_POWER_COUNT, lang=server.lang),
            next_button=RESERVED_PLUS, prev_button=RESERVED_MINUS,
            skip_first_screenshot=True
        )

    def set_fuel_count(self, count):
        slider = Slider(main=self, slider=FUEL_SLIDER)
        # Can only use 5 fuel at one time
        slider.set(count, 5)
        self.ui_ensure_index(
            count, letter=Digit(OCR_FUEL_COUNT, lang=server.lang),
            next_button=FUEL_PLUS, prev_button=FUEL_MINUS,
            skip_first_screenshot=True
        )

    def use_fuel(self, current, skip_first_screenshot=True):
        """
        Args:
            current:
            skip_first_screenshot:

        Returns:
            bool: If used

        Pages:
            in: COMBAT_AGAIN
            out: COMBAT_AGAIN
        """
        limit = self.config.stored.TrailblazePower.FIXED_TOTAL
        use = (limit - current) // self.fuel_trailblaze_power
        if use == 0:
            logger.info(f"Current trailblaze power is near {limit}, no need to use fuel")
            return False

        logger.info("Use Fuel")

        timeout = Timer(1, count=3)
        has_fuel = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(FUEL_SELECTED):
                logger.info('Fuel selected')
                break
            if self.appear(POPUP_CONFIRM):
                timeout.start()
                if self.appear(FUEL_SELECTED) or self.appear(FUEL):
                    has_fuel = True
                if not has_fuel and timeout.reached():
                    logger.info("No fuel found")
                    self._fuel_cancel()
                    return False
            if self.appear_then_click(FUEL):
                has_fuel = True
                continue
            if not self.appear(POPUP_CONFIRM) and self.appear_then_click(FUEL_ENTRANCE):
                continue

        offset = FUEL_SELECTED.button_offset
        image = crop(self.device.image, area_offset(OCR_FUEL.area, offset), copy=False)
        count = Digit(OCR_FUEL).ocr_single_line(image, direct_ocr=True)

        reserve = self.config.TrailblazePower_FuelReserve
        available_count = max(count - reserve, 0)
        use = min(use, available_count)
        logger.info(f'Having {count} fuel, reserve {reserve} fuel, going to use {use} fuel')
        if use <= 0:
            logger.info("Fuel remain is under the reserve threshold, stop using fuel")
            self._fuel_cancel()
            return False

        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(USING_FUEL):
                break
            if self.appear(FUEL) and self.handle_popup_confirm():
                continue
            if self.appear(FUEL_SELECTED) and self.handle_popup_confirm():
                continue

        self.set_fuel_count(use)
        self._fuel_confirm()
        return True
