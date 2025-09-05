from module.base.timer import Timer
from module.base.utils import random_rectangle_vector_opted
from module.logger import logger
from tasks.base.assets.assets_base_page import CLOSE, MAP_EXIT
from tasks.base.page import page_gacha
from tasks.base.ui import UI
from tasks.daily.assets.assets_daily_trial import *


class CharacterTrial(UI):
    def enter_himeko_trial(self):
        """
        Pages:
            in: Any
            out: page_main, in himeko trial
        """
        logger.info('Enter Himeko trial')
        switched = False
        if self.appear(HIMEKO_CHECK):
            logger.info(f'Already at {HIMEKO_CHECK}')
        elif self.match_template_color(START_TRIAL):
            logger.info(f'Already at {START_TRIAL}')
        elif self.match_template_color(REGULAR_GACHA_CHECK):
            logger.info(f'Already at {REGULAR_GACHA_CHECK}')
        elif self.ui_page_appear(page_gacha):
            logger.info(f'Already at {page_gacha}')
        else:
            switched = self.ui_ensure(page_gacha)

        # page_gacha -> in himeko trial
        skip_first_screenshot = True
        info_closed = False
        info_timeout = Timer(2, count=4).start()
        first_gacha = switched
        in_regular_gacha = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_in_main():
                if info_closed:
                    logger.info('In Himeko trial')
                    break
                if info_timeout.reached():
                    logger.info('In Himeko trial (wait INFO_CLOSE timeout)')
                    break
            else:
                info_timeout.reset()

            # In map
            if self.appear_then_click(INFO_CLOSE):
                info_closed = True
                continue
            # Switch to Himeko trial
            if self.appear(START_TRIAL) \
                    and not self.appear(HIMEKO_CHECK) \
                    and self.appear_then_click(HIMEKO_CLICK, interval=2):
                continue
            if self.appear(HIMEKO_CHECK) \
                    and self.match_template_color(START_TRIAL, interval=2):
                self.device.click(START_TRIAL)
                continue
            # Switch to regular trial
            if self.match_template_color(REGULAR_GACHA_CHECK) \
                    and self.match_color(CHARACTER_TRIAL, interval=2):
                self.device.click(CHARACTER_TRIAL)
                in_regular_gacha = True
                continue
            # scroll down to regular gacha
            if not in_regular_gacha and not self.match_template_color(REGULAR_GACHA_CLICK) \
                    and self.ui_page_appear(page_gacha, interval=2):
                if first_gacha:
                    self.device.sleep(0.3)
                    first_gacha = False
                p1, p2 = random_rectangle_vector_opted(
                    (0, -120), box=REGULAR_GACHA_CLICK.search, random_range=(-5, -10, 5, 10), padding=0)
                self.device.drag(p1, p2, name=f'REGULAR_GACHA_DRAG')
                self.interval_reset(page_gacha.check_button)
                continue
            if self.match_template_color(REGULAR_GACHA_CLICK, interval=2):
                # Poor sleep indeed, clicks won't be response unless other elements are loaded
                # Waiting for gacha banner moving
                if first_gacha:
                    self.device.sleep(0.3)
                    first_gacha = False
                self.device.click(REGULAR_GACHA_CLICK)
                continue

    def exit_trial(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_main, in trial
            out: START_TRIAL
        """
        logger.info('Exit trial')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.match_template_color(START_TRIAL):
                break
            if self.is_in_map_exit(interval=2):
                self.device.click(MAP_EXIT)
                continue
            if self.handle_popup_confirm():
                continue

    def exit_trial_to_main(self, skip_first_screenshot=True):
        """
        Pages:
            in: START_TRIAL
            out: page_main
        """
        logger.info('Exit trial to main')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.is_in_main():
                break

            if self.match_template_color(START_TRIAL, interval=2):
                logger.info(f'{START_TRIAL} -> {CLOSE}')
                self.device.click(CLOSE)
                continue
            if self.match_color(CHARACTER_TRIAL, interval=2):
                logger.info(f'{CHARACTER_TRIAL} -> {CLOSE}')
                self.device.click(CLOSE)
                continue
