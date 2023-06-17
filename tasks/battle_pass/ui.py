import numpy as np

from module.base.timer import Timer
from module.base.utils import get_color
from module.logger.logger import logger
from module.ui.switch import Switch
from tasks.base.page import page_battle_pass
from tasks.base.ui import UI
from tasks.battle_pass.assets.assets_battle_pass import *
from tasks.battle_pass.keywords import KEYWORD_BATTLE_PASS_TAB

SWITCH_BATTLE_PASS_TAB = Switch('BattlePassTab', is_selector=True)
SWITCH_BATTLE_PASS_TAB.add_state(
    KEYWORD_BATTLE_PASS_TAB.Rewards,
    check_button=REWARDS_CHECK,
    click_button=REWARDS_CLICK
)
SWITCH_BATTLE_PASS_TAB.add_state(
    KEYWORD_BATTLE_PASS_TAB.Missions,
    check_button=MISSIONS_CHECK,
    click_button=MISSIONS_CLICK
)


class BattlePassUI(UI):
    def _battle_pass_wait_rewards_loaded(self, skip_first_screenshot=True):
        timeout = Timer(2, count=4).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Wait rewards tab loaded timeout')
                break
            if self.appear(REWARDS_LOADED):
                logger.info('Rewards tab loaded')
                break

    def _battle_pass_wait_missions_loaded(self, skip_first_screenshot=True):
        timeout = Timer(2, count=4).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Wait missions tab loaded timeout')
                break
            color = get_color(self.device.image, MISSIONS_LOADED.area)
            if np.mean(color) > 128:
                logger.info('Missions tab loaded')
                break

    def battle_pass_goto(self, state: KEYWORD_BATTLE_PASS_TAB):
        """
        Args:
            state:

        Examples:
            self = BattlePassUI('alas')
            self.device.screenshot()
            self.battle_pass_goto(KEYWORDS_DUNGEON_TAB.Missions)
            self.battle_pass_goto(KEYWORDS_DUNGEON_TAB.Rewards)
        """
        logger.hr('Battle pass tab goto', level=2)
        self.ui_ensure(page_battle_pass)
        if SWITCH_BATTLE_PASS_TAB.set(state, main=self):
            logger.info(f'Tab goto {state}, wait until loaded')
            if state == KEYWORD_BATTLE_PASS_TAB.Missions:
                self._battle_pass_wait_missions_loaded()
            if state == KEYWORD_BATTLE_PASS_TAB.Rewards:
                self._battle_pass_wait_rewards_loaded()

    def handle_choose_gifts(self, interval=5):
        """
        Popup when you have purchase Nameless Glory

        Args:
            interval:

        Returns:
            If handled
        """
        if self.appear_then_click(CLOSE_CHOOSE_GIFT, interval=interval):
            return True

        return False

    def claim_rewards(self, skip_first_screenshot=True):
        """

        Args:
            skip_first_screenshot:

        Examples:
            self = BattlePassUI('alas')
            self.device.screenshot()
            self.claim_rewards()
        """
        # claim exp
        self.battle_pass_goto(KEYWORD_BATTLE_PASS_TAB.Missions)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if not self.appear(EXP_CLAIM_ALL):
                break
            if self.appear_then_click(EXP_CLAIM_ALL):
                logger.info("All EXP claimed")
                continue

        # claim rewards
        self.battle_pass_goto(KEYWORD_BATTLE_PASS_TAB.Rewards)
        skip_first_screenshot = True
        choose_gifts_handled = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.ui_page_appear(page_battle_pass) and (not self.appear(REWARDS_CLAIM_ALL) or choose_gifts_handled):
                logger.info("Complete")
                break
            if self.appear_then_click(REWARDS_CLAIM_ALL):
                continue
            if self.handle_choose_gifts():
                choose_gifts_handled = True
                logger.info("You have unclaimed gift to choose")
                continue
            if self.handle_reward():
                continue
