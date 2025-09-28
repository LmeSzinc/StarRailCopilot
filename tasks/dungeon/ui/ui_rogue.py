from module.base.timer import Timer
from module.base.utils import area_in_area, random_rectangle_vector
from module.logger import logger
from tasks.base.page import page_guide
from tasks.dungeon.assets.assets_dungeon_ui import *
from tasks.dungeon.assets.assets_dungeon_ui_list import OCR_DUNGEON_LIST
from tasks.dungeon.assets.assets_dungeon_ui_rogue import *
from tasks.dungeon.keywords import KEYWORDS_DUNGEON_NAV, KEYWORDS_DUNGEON_TAB
from tasks.dungeon.ui.nav import SWITCH_DUNGEON_TAB
from tasks.dungeon.ui.ui import DungeonUI
from tasks.forgotten_hall.assets.assets_forgotten_hall_ui import TELEPORT


class DungeonRogueUI(DungeonUI):
    def _is_oe_unlocked(self):
        """
        Check if Ornament Extraction unlocked

        Returns:
            bool:

        Pages:
            in: page_guide
        """
        for check_button in [SURVIVAL_INDEX_OE_LOADED, SIMULATED_UNIVERSE_CLICK, SIMULATED_UNIVERSE_CHECK]:
            if self.appear(check_button):
                logger.info(f'Having rogue tab ({check_button})')
                return True
        return False

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

        # Wait until any SWITCH_DUNGEON_TAB appears
        # If Ornament Extraction unlocked, Simulated Universe moves to a separate tab
        timeout = Timer(5, count=15).start()
        unlocked_oe = True
        for _ in self.loop():
            # Timeout
            if timeout.reached():
                logger.warning('Wait DungeonTab timeout, assume OE unlocked')
                unlocked_oe = True
                break
            # End with OE unlocked
            if self._is_oe_unlocked():
                unlocked_oe = True
                break
            # End with other dungeon tabs
            current = SWITCH_DUNGEON_TAB.get(main=self)
            logger.attr(SWITCH_DUNGEON_TAB.name, current)
            if current != 'unknown':
                logger.info('No rogue tab')
                unlocked_oe = False
                break

        if not unlocked_oe:
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
                self.dungeon_nav_goto(KEYWORDS_DUNGEON_NAV.Simulated_Universe)
            # check oe again, probably some random mis-detection
            if self._is_oe_unlocked():
                # already unlocked, but mis-detected just now
                pass
            else:
                return

        # switch when OE unlocked
        state = KEYWORDS_DUNGEON_TAB.Simulated_Universe
        # Switch tab
        tab_switched = SWITCH_DUNGEON_TAB.set(state, main=self)
        if ui_switched or tab_switched:
            logger.info(f'Tab goto {state}, wait until loaded')
            self._dungeon_wait_until_rogue_loaded()
        # Switch nav
        self.dungeon_nav_goto(KEYWORDS_DUNGEON_NAV.Simulated_Universe)
        # No idea how to wait list loaded
        # List is not able to swipe without fully loaded
        self.wait_until_stable(LIST_LOADED_CHECK)
        # Swipe
        self._dungeon_rogue_swipe_down()

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
        logger.info('Dungeon rogue swipe down')
        interval = Timer(2, count=4)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(SIMULATED_UNIVERSE_LOADED_CLASSIC, interval=3):
                logger.info('Found rogue icon')
                # Search teleport button on the right
                _, y1, _, y2 = SIMULATED_UNIVERSE_LOADED_CLASSIC.button
                x1, _, x2, _ = TELEPORT.area
                search = (x1 - 50, y1 - 120, x2 + 50, y2 + 120)
                # Check if button in search area
                for button in TELEPORT.match_multi_template(self.device.image):
                    if area_in_area(button.button, search, threshold=0):
                        logger.info('Found rogue TELEPORT')
                        self.device.click(button)
                        return True
                # TELEPORT not found
                self.interval_clear(SIMULATED_UNIVERSE_LOADED_CLASSIC)

            # Swipe
            if interval.reached():
                p1, p2 = random_rectangle_vector(
                    (0, -450), box=OCR_DUNGEON_LIST.button, random_range=(-20, -20, 20, 20), padding=5)
                # Drag, simulated universe can be at the middle, with locked rogue theme at bottom
                self.device.drag(p1, p2)
                interval.reset()


if __name__ == '__main__':
    self = DungeonRogueUI('src')
    self.device.screenshot()
    self.dungeon_goto_rogue()
