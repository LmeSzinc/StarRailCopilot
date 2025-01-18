import re

from pydantic import BaseModel

from module.base.timer import Timer
from module.base.utils import crop
from module.logger import logger
from module.ocr.ocr import Digit, DigitCounter
from tasks.base.ui import UI
from tasks.combat.assets.assets_combat_stamina_status import *


class StaminaOcr(DigitCounter):
    def after_process(self, result):
        result = super().after_process(result)
        # The trailblaze power icon is recognized as 买
        # OCR_TRAILBLAZE_POWER includes the icon because the length varies by value
        result = re.sub(r'[买米装来：（）]', '', result)
        # 61240 -> 6/240
        result = re.sub(r'1240$', '/240', result)
        # 0*0/24 -> 0/240
        result = re.sub(r'24$', '240', result)
        # * 50/2401+)
        # 73/3001+)
        result = result.replace('/2401', '/240')
        result = result.replace('/3001', '/300')
        return result


class ReservedOcr(Digit):
    pass


class ImmersifierOcr(DigitCounter):
    pass


class DataStaminaStatus(BaseModel):
    stamina: int | None
    reserved: int | None
    immersifier: int | None


class StaminaStatus(UI):
    def get_stamina_status(self, image) -> DataStaminaStatus:
        """
        Update trailblaze power, stored trailblaze power, immersifier

        Returns:
            int: Stamina, or None if stamina not displayed or error on OCR
            int: Reserved stamina
            int: Immersifier
        """
        for button in [STAMINA_ICON, RESERVED_ICON, IMMERSIFIER_ICON]:
            button.load_search(ICON_SEARCH.area)

        stamina = None
        if STAMINA_ICON.match_template(image):
            STAMINA_OCR.load_offset(STAMINA_ICON)
            im = crop(image, STAMINA_OCR.button, copy=False)
            stamina, _, total = StaminaOcr(STAMINA_OCR).ocr_single_line(im, direct_ocr=True)
            maximum = self.config.stored.TrailblazePower.FIXED_TOTAL
            if total > maximum or total == 0:
                logger.warning(f'Unexpected stamina total: {total}')
                stamina = None

        reserved = None
        if RESERVED_ICON.match_template(image):
            RESERVED_OCR.load_offset(RESERVED_ICON)
            im = crop(image, RESERVED_OCR.button, copy=False)
            reserved = ReservedOcr(RESERVED_OCR).ocr_single_line(im, direct_ocr=True)
            maximum = self.config.stored.Reserved.FIXED_TOTAL
            if reserved > maximum:
                logger.warning(f'Unexpected reserved value: {reserved}')
                reserved = None

        immersifier = None
        if IMMERSIFIER_ICON.match_template(image):
            IMMERSIFIER_OCR.load_offset(IMMERSIFIER_ICON)
            im = crop(image, IMMERSIFIER_OCR.button, copy=False)
            immersifier, _, total = StaminaOcr(IMMERSIFIER_OCR).ocr_single_line(im, direct_ocr=True)
            maximum = self.config.stored.Immersifier.FIXED_TOTAL
            if total != maximum:
                logger.warning(f'Unexpected immersifier total: {total}')
                immersifier = None

        return DataStaminaStatus(
            stamina=stamina,
            reserved=reserved,
            immersifier=immersifier,
        )

    def update_stamina_status(
            self,
            image=None,
            skip_first_screenshot=True,
            expect_stamina=False,
            expect_reserved=False,
            expect_immersifier=False,
    ) -> DataStaminaStatus:
        """
        Update stamina status with retry

        Args:
            image: Detect given image only, no new screenshot will be taken
                and all expect_* are considered False
            skip_first_screenshot:
            expect_stamina:
                True to expect stamina exists, retry detect if it wasn't
            expect_reserved:
            expect_immersifier:

        Pages:
            in: page_guild, Survival_Index, Simulated_Universe
                or page_rogue, LEVEL_CONFIRM
                or rogue, REWARD_CLOSE
        """
        timeout = Timer(1, count=2).start()
        if image is None:
            image = self.device.image
            use_cached_image = False
        else:
            skip_first_screenshot = True
            use_cached_image = True

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
                image = self.device.image

            # Timeout
            if timeout.reached():
                logger.warning('dungeon_update_stamina() timeout')
                return DataStaminaStatus(
                    stamina=None,
                    reserved=None,
                    immersifier=None,
                )

            # Ocr
            status = self.get_stamina_status(image)
            valid = True
            if expect_stamina and status.stamina is None:
                valid = False
            if expect_reserved and status.reserved is None:
                valid = False
            if expect_immersifier and status.immersifier is None:
                valid = False
            if status.stamina is None and status.reserved is None and status.immersifier is None:
                logger.warning('update_stamina_status: No icon detected')
                valid = False

            # Write config
            with self.config.multi_set():
                if status.stamina is not None:
                    self.config.stored.TrailblazePower.value = status.stamina
                if status.reserved is not None:
                    self.config.stored.Reserved.value = status.reserved
                if status.immersifier is not None:
                    self.config.stored.Immersifier.value = status.immersifier

            if use_cached_image or valid:
                return status
            else:
                continue
