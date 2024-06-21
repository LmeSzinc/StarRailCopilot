from module.base.timer import Timer
from module.base.utils import random_rectangle_vector
from module.logger import logger
from tasks.base.page import page_guide
from tasks.dungeon.assets.assets_dungeon_ui import *
from tasks.dungeon.assets.assets_dungeon_ui_rogue import *
from tasks.dungeon.keywords import KEYWORDS_DUNGEON_NAV, KEYWORDS_DUNGEON_TAB
from tasks.dungeon.ui import DungeonUI, SWITCH_DUNGEON_TAB
from tasks.forgotten_hall.assets.assets_forgotten_hall_ui import TELEPORT


class DungeonRogueUI(DungeonUI):
    def dungeon_goto_rogue(self):
        """
        Goto Simulated Universe page but not pressing the TELEPORT button

        Pages:
            in: Any
            out: page_guide, Survival_Index, Simulated_Universe

        Examples:
            self = DungeonUI('src')
            self.device.screenshot()
            self.dungeon_goto_rogue()
            self._rogue_teleport()
        """
        logger.hr('Dungeon tab goto', level=2)
        ui_switched = self.ui_ensure(page_guide)
        SWITCH_DUNGEON_TAB.wait(main=self)

        if (
                self.appear(SIMULATED_UNIVERSE_CLICK)
                or self.appear(SIMULATED_UNIVERSE_CHECK)
                or self.appear(SURVIVAL_INDEX_OE_LOADED)
        ):
            logger.info('Having rogue tab')
            state = KEYWORDS_DUNGEON_TAB.Simulated_Universe
            # Switch tab
            tab_switched = SWITCH_DUNGEON_TAB.set(state, main=self)
            if ui_switched or tab_switched:
                logger.info(f'Tab goto {state}, wait until loaded')
                self._dungeon_wait_until_rogue_loaded()
            # Switch nav
            self._dungeon_nav_goto(KEYWORDS_DUNGEON_NAV.Simulated_Universe)
            # No idea how to wait list loaded
            # List is not able to swipe without fully loaded
            self.wait_until_stable(LIST_LOADED_CHECK)
            # Swipe
            self._dungeon_rogue_swipe_down()
        else:
            logger.info('No rogue tab')
            state = KEYWORDS_DUNGEON_TAB.Survival_Index
            # Switch tab
            tab_switched = SWITCH_DUNGEON_TAB.set(state, main=self)
            if ui_switched or tab_switched:
                logger.info(f'Tab goto {state}, wait until loaded')
                self._dungeon_wait_survival_index_loaded()
            # Switch nav
            if self.appear(SURVIVAL_INDEX_SU_LOADED):
                logger.info('Already at nav Simulated_Universe')
            else:
                self._dungeon_nav_goto(KEYWORDS_DUNGEON_NAV.Simulated_Universe)

    def _dungeon_wait_until_rogue_loaded(self, skip_first_screenshot=True):
        """
        Returns:
            bool: True if wait success, False if wait timeout.

        Pages:
            in: page_guide, Simulated_Universe
        """
        timeout = Timer(2, count=4).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Wait rogue tab loaded timeout')
                return False
            if self.appear(DIVERGENT_UNIVERSE_LOADED):
                logger.info('Rogue tab loaded, DIVERGENT_UNIVERSE_LOADED')
                return True
            # No LAST_TELEPORT, may hit teleport button of old screenshots from Ornament Extraction
            # if self.appear(LAST_TELEPORT):
            #     logger.info('Rogue tab loaded, LAST_TELEPORT')
            #     return True

    def _dungeon_rogue_swipe_down(self, skip_first_screenshot=True):
        """
        Swipe down to find teleport button of classic rogue
        Note that this method will change SIMULATED_UNIVERSE_LOADED_CLASSIC.search, original value should have a backup
        """
        # Already having classic rogue entry insight
        SIMULATED_UNIVERSE_LOADED_CLASSIC.load_search(OCR_DUNGEON_LIST.button)
        if self.appear(SIMULATED_UNIVERSE_LOADED_CLASSIC):
            buttons = TELEPORT.match_multi_template(self.device.image)
            y = SIMULATED_UNIVERSE_LOADED_CLASSIC.button[1]
            for button in buttons:
                # And having a teleport button below
                if button.button[1] > y:
                    logger.info('Classic rogue teleport already in sight')
                    return True

        logger.info('Dungeon rogue swipe down')
        interval = Timer(2, count=4)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(SIMULATED_UNIVERSE_LOADED_CLASSIC):
                if self.appear(LAST_TELEPORT):
                    logger.info('Classic rogue teleport at end')
                    return True

            # Swipe
            if interval.reached():
                p1, p2 = random_rectangle_vector(
                    (0, -450), box=OCR_DUNGEON_LIST.button, random_range=(-20, -20, 20, 20), padding=5)
                self.device.swipe(p1, p2)
                interval.reset()


if __name__ == '__main__':
    self = DungeonRogueUI('src')
    self.device.screenshot()
    self.dungeon_goto_rogue()
