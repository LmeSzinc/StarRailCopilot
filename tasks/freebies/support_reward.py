from module.base.decorator import cached_property
from module.base.timer import Timer
from module.logger import logger
from module.ui.switch import Switch
from tasks.base.assets.assets_base_page import CLOSE, MAIN_GOTO_MENU, MENU_CHECK
from tasks.base.page import page_main, page_menu
from tasks.base.ui import UI
from tasks.freebies.assets.assets_freebies_support_reward import *


class SupportReward(UI):
    @cached_property
    def showcase(self):
        switch = Switch('ProfileShowcase', is_selector=True)
        switch.add_state(
            SHOWCASE_BATTLE_CHECK,
            check_button=SHOWCASE_BATTLE_CHECK,
        )
        switch.add_state(
            SHOWCASE_CHARACTER_CHECK,
            check_button=SHOWCASE_CHARACTER_CHECK,
        )
        switch.add_state(
            SHOWCASE_COLLECTION_CHECK,
            check_button=SHOWCASE_COLLECTION_CHECK,
        )
        return switch

    def run(self):
        """
        Run get support reward task
        """
        self.ui_ensure(page_menu)

        self._goto_profile()
        self.showcase.set(SHOWCASE_CHARACTER_CHECK, main=self)
        self._get_reward()
        self._goto_menu()

    def _goto_profile(self):
        """
        Pages:
            in: MENU
            out: PROFILE
        """
        logger.info('Going to profile')
        self.interval_clear(page_main.check_button)
        for _ in self.loop():
            if self.appear(IN_PROFILE):
                logger.info('Successfully in profile')
                break

            if self.appear_then_click(MENU_TO_PROFILE):
                continue
            if self.appear_then_click(PROFILE):
                continue
            # Accidentally at page_main
            if self.ui_page_appear(page_main, interval=5):
                logger.info(f'{page_main} -> {MAIN_GOTO_MENU}')
                self.device.click(MAIN_GOTO_MENU)
                continue

        # wait until IN_PROFILE stable
        for _ in self.loop(timeout=1.5):
            if self.appear(IN_PROFILE):
                if IN_PROFILE.is_offset_in(5, 5):
                    logger.info('IN_PROFILE stabled')
                    break
        else:
            logger.warning('Wait until IN_PROFILE stable timeout')

    def _get_reward(self, skip_first_screenshot=True):
        """
        Pages:
            in: PROFILE
            out: reward_appear()
        """
        logger.info('Getting reward')
        claimed = False
        empty = Timer(0.3, count=1).start()
        timeout = Timer(5).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if not claimed and empty.reached():
                logger.info('No reward')
                break
            if self.reward_appear():
                logger.info('Got reward')
                break
            if self.appear(REWARD_POPUP, similarity=0.75):
                logger.info('Got reward popup')
                break
            if timeout.reached():
                logger.warning('Get support reward timeout')
                break

            if self.appear_then_click(CAN_GET_REWARD, similarity=0.70, interval=2):
                claimed = True
                timeout.reset()
                continue

    def _goto_menu(self):
        """
        Pages:
            in: PROFILE or reward_appear
            out: MENU
        """
        skip_first_screenshot = False
        logger.info('Going to menu')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(MENU_CHECK):
                return True

            if self.appear_then_click(REWARD_POPUP, similarity=0.75, interval=2):
                logger.info(f'{REWARD_POPUP} - {CLOSE}')
                self.device.click(CLOSE)
                continue
            if self.handle_ui_close(IN_PROFILE, interval=2):
                continue
            if self.handle_reward(click_button=CAN_GET_REWARD):
                # Avoid clicking on some other buttons
                continue


if __name__ == '__main__':
    self = SupportReward('src')
    self.device.screenshot()
    self.run()
