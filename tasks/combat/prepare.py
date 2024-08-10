import module.config.server as server
from module.base.timer import Timer
from module.base.utils import color_similar, get_color
from module.logger import logger
from module.ocr.ocr import Digit
from tasks.combat.assets.assets_combat_prepare import (
    OCR_WAVE_COST,
    OCR_WAVE_COUNT,
    WAVE_MINUS,
    WAVE_PLUS,
    WAVE_SLIDER
)
from tasks.combat.stamina_status import StaminaStatus
from tasks.item.slider import Slider


class CombatPrepare(StaminaStatus):
    # Current combat waves,
    combat_waves = 1
    # Limit combat runs, 0 means no limit.
    combat_wave_limit = 0
    combat_wave_done = 0
    # E.g. 10, 30, 40
    combat_wave_cost = 10

    def combat_set_wave(self, count=6):
        """
        Args:
            count: 1 to 6

        Pages:
            in: COMBAT_PREPARE
        """
        slider = Slider(main=self, slider=WAVE_SLIDER)
        slider.set(count, 6)
        self.ui_ensure_index(
            count, letter=Digit(OCR_WAVE_COUNT, lang=server.lang),
            next_button=WAVE_PLUS, prev_button=WAVE_MINUS,
            skip_first_screenshot=True
        )

    def combat_has_multi_wave(self) -> bool:
        """
        If combat has waves to set.
        Most dungeons can do 6 times at one time while bosses don't.
        """
        return self.appear(WAVE_MINUS) or self.appear(WAVE_PLUS)

    def combat_get_trailblaze_power(self, expect_reduce=False, skip_first_screenshot=True) -> int:
        """
        Args:
            expect_reduce: Current value is supposed to be lower than the previous.
            skip_first_screenshot:

        Pages:
            in: COMBAT_PREPARE or COMBAT_REPEAT
        """
        timeout = Timer(1, count=2).start()
        before = self.config.stored.TrailblazePower.value
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            data = self.update_stamina_status(image=self.device.image)
            if data.stamina is None:
                continue
            # Confirm if it is > 240, sometimes just OCR errors
            # if current > 240 and timeout.reached():
            #     break
            if expect_reduce and timeout.reached():
                break
            if expect_reduce and data.stamina >= before:
                continue
            if data.stamina <= 240:
                break

        return data.stamina

    def combat_get_wave_cost(self, skip_first_screenshot=True):
        """
        Get traiblaze power cost and set it to `combat_cost`

        Returns:
            int: E.g. 10, 30, 40

        Pages:
            in: COMBAT_PREPARE
        """
        timeout = Timer(1.5, count=6).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            color = get_color(self.device.image, OCR_WAVE_COST.area)
            if color_similar(color, (229, 231, 223), threshold=30):
                logger.info(f'Combat is trailblaze power free')
                self.combat_wave_cost = 0
                return 0

            cost = Digit(OCR_WAVE_COST).ocr_single_line(self.device.image)
            if cost == 10:
                logger.attr('CombatMultiWave', self.combat_has_multi_wave())
                if self.combat_has_multi_wave():
                    self.combat_wave_cost = cost
                    return cost
                else:
                    logger.warning(f'Combat wave costs {cost} but does not has multiple waves')
                    self.combat_wave_cost = cost
                    return cost
            elif cost in [30, 40]:
                if self.combat_has_multi_wave():
                    logger.warning(f'Combat wave costs {cost} but has multiple waves, '
                                   f'probably wave amount is preset')
                    self.combat_set_wave(1)
                    # Don't skip_first_screenshot, combat_set_wave may not have screenshot updated
                    # skip_first_screenshot = True
                    timeout.reset()
                    continue
                else:
                    logger.attr('CombatMultiWave', self.combat_has_multi_wave())
                    self.combat_wave_cost = cost
                    return cost
            else:
                logger.warning(f'Unexpected combat wave cost: {cost}')
                continue

        logger.attr('CombatMultiWave', self.combat_has_multi_wave())
        if self.combat_has_multi_wave():
            cost = 10
        else:
            cost = 40
        logger.warning(f'Get combat wave cost timeout, assume it costs {cost}')
        self.combat_wave_cost = cost
        return cost
