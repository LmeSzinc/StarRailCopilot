from module.base.decorator import run_once
from module.exception import RequestHumanTakeover
from module.logger import logger
from tasks.base.assets.assets_base_page import MAP_EXIT
from tasks.base.assets.assets_base_popup import POPUP_CANCEL
from tasks.combat.assets.assets_combat_prepare import COMBAT_PREPARE
from tasks.combat.assets.assets_combat_support import COMBAT_SUPPORT_LIST
from tasks.combat.combat import Combat
from tasks.dungeon.event import DungeonEvent
from tasks.ornament.assets.assets_ornament_combat import *
from tasks.ornament.assets.assets_ornament_ui import *


class OrnamentCombat(DungeonEvent, Combat):
    def combat_enter_from_map(self, skip_first_screenshot=True):
        # Don't enter from map, UI too deep inside
        # Enter from survival index instead
        pass

    def get_double_event_remain_at_combat(self, button=OCR_DOUBLE_EVENT_REMAIN_AT_OE):
        # Different position to OCR
        return super().get_double_event_remain_at_combat(button)

    def oe_leave(self, skip_first_screenshot=True):
        self.interval_clear([COMBAT_PREPARE, MAP_EXIT])
        logger.hr('OE leave')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            exit_ = self.is_in_map_exit()
            if not exit_ and self.is_in_main():
                logger.info('OE left')
                break

            # Click
            if self.handle_ui_back(DU_OE_SELECT_CHECK, interval=2):
                continue
            if self.handle_ui_back(DU_MODE_CHECK, interval=2):
                continue
            if self.handle_ui_back(DU_MAIN_CHECK, interval=2):
                continue
            if self.handle_ui_back(COMBAT_PREPARE, interval=2):
                continue
            if exit_ and self.is_in_map_exit(interval=3):
                self.device.click(MAP_EXIT)
                continue
            if self.handle_popup_confirm():
                continue

    def support_set(self, support_character_name: str = "FirstCharacter"):
        """
        Args:
            support_character_name: Support character name

        Returns:
            bool: If clicked

        Pages:
            in: COMBAT_PREPARE
            mid: COMBAT_SUPPORT_LIST
            out: COMBAT_PREPARE
        """
        logger.hr("Combat support")
        self.interval_clear(SUPPORT_ADD)
        skip_first_screenshot = True
        selected_support = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(SUPPORT_DISMISS):
                return True

            # Click
            if self.appear(SUPPORT_ADD, interval=2):
                self.device.click(SUPPORT_ADD)
                self.interval_reset(SUPPORT_ADD)
                continue
            if self.appear(POPUP_CANCEL, interval=1):
                logger.warning(
                    "selected identical character, trying select another")
                self._cancel_popup()
                self._select_next_support()
                self.interval_reset(POPUP_CANCEL)
                continue
            if self.appear(COMBAT_SUPPORT_LIST, interval=2):
                if not selected_support:
                    # In Ornament Extraction, first character isn't selected by default
                    if support_character_name == "FirstCharacter":
                        self._select_first()
                    else:
                        self._search_support(support_character_name)  # Search support
                    selected_support = True
                self.device.click(OCR_DOUBLE_EVENT_REMAIN_AT_OE)
                self.interval_reset(COMBAT_SUPPORT_LIST)
                continue

    def is_team_prepared(self) -> bool:
        """
        Pages:
            in: COMBAT_PREPARE
        """
        slots = CHARACTER_EMPTY_OE.match_multi_template(self.device.image)
        slots = 4 - len(slots)
        logger.attr('TeamSlotsPrepared', slots)
        return slots > 0

    def combat_prepare(self, team=1, support_character: str = None):
        """
        Args:
            team: 1 to 6.
            support_character: Support character name

        Returns:
            bool: True

        Pages:
            in: COMBAT_PREPARE
            out: is_in_main
        """

        @run_once
        def check_team_prepare():
            if not self.is_team_prepared():
                logger.error(f'Please prepare your team in Ornament Extraction')
                raise RequestHumanTakeover

        logger.hr('Combat prepare')
        skip_first_screenshot = True
        if support_character:
            # Block COMBAT_TEAM_PREPARE before support set
            support_set = False
        else:
            support_set = True
        logger.info([support_character, support_set])
        trial = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_in_main():
                logger.info('Combat entered')
                return True
            # Relics full
            # Clicking between COMBAT_PREPARE and COMBAT_TEAM_PREPARE
            if trial > 5:
                logger.critical('Failed to enter dungeon after 5 trial, probably because relics are full')
                raise RequestHumanTakeover
            if self.appear(SUPPORT_ADD):
                check_team_prepare()

            # Click
            if support_character and self.appear(SUPPORT_ADD, interval=2):
                self.support_set(support_character)
                self.interval_reset(SUPPORT_ADD)
                support_set = True
                continue
            if support_set and self.appear(COMBAT_PREPARE, interval=5):
                # Long loading after COMBAT_PREPARE
                self.device.click(COMBAT_PREPARE)
                trial += 1
                continue
            if self.handle_popup_confirm():
                continue
