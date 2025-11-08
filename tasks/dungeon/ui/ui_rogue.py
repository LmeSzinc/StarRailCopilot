from module.base.timer import Timer
from module.base.utils import area_in_area, random_rectangle_vector
from module.logger import logger
from tasks.base.page import page_guide, page_rogue
from tasks.dungeon.assets.assets_dungeon_nav import *
from tasks.dungeon.assets.assets_dungeon_ui import *
from tasks.dungeon.assets.assets_dungeon_ui_list import OCR_DUNGEON_LIST
from tasks.dungeon.assets.assets_dungeon_ui_rogue import *
from tasks.dungeon.keywords import KEYWORDS_DUNGEON_TAB
from tasks.dungeon.ui.ui import DungeonUI
from tasks.forgotten_hall.assets.assets_forgotten_hall_ui import TELEPORT
from tasks.rogue.assets.assets_rogue_weekly import REWARD_CLOSE


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
        logger.hr('Dungeon goto rogue', level=1)
        self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Simulated_Universe)
        self._dungeon_wait_until_dungeon_list_loaded()

        # wait DIVERGENT_GOTO_SIMULATED or SIMULATED_UNIVERSE nav
        unlocked_oe = True
        for _ in self.loop():
            if self.match_template_luma(DIVERGENT_GOTO_SIMULATED):
                unlocked_oe = True
                break
            if self.appear(SIMULATED_UNIVERSE_CHECK):
                unlocked_oe = False
                break
            if self.appear_then_click(DIVERGENT_UNIVERSE_CLICK, interval=2):
                continue
            if self.appear_then_click(SIMULATED_UNIVERSE_CLICK, interval=2):
                continue
        logger.attr('unlocked_oe', True)

        if unlocked_oe:
            self._rogue_teleport()
        else:
            # No idea how to wait list loaded
            # List is not able to swipe without fully loaded
            self.wait_until_stable(LIST_LOADED_CHECK)
            # Swipe
            self._dungeon_rogue_swipe_down()
            self._rogue_teleport()

    def _rogue_teleport(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_guide, Simulated_Universe, Simulated_Universe
            out: page_rogue, is_page_rogue_main()
        """
        logger.info('Rogue teleport')
        self.interval_clear(page_guide.check_button)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.ui_page_appear(page_rogue):
                break

            # Additional
            if self.appear_then_click(REWARD_CLOSE, interval=2):
                continue
            # Popup that confirm character switch
            if self.handle_popup_confirm():
                continue
            # Click
            if self.match_template_luma(DIVERGENT_GOTO_SIMULATED, interval=2):
                self.device.click(DIVERGENT_GOTO_SIMULATED)
                continue
            if self.appear(page_guide.check_button, interval=2):
                buttons = TELEPORT.match_multi_template(self.device.image)
                if len(buttons):
                    # 2.3, classic rogue is always at bottom
                    buttons = sorted(buttons, key=lambda x: x.area[1], reverse=True)
                    self.device.click(buttons[0])
                    continue

        self.interval_clear(page_guide.check_button)

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
