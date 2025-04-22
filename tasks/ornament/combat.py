from module.base.decorator import run_once
from module.device.platform.utils import cached_property
from module.exception import RequestHumanTakeover
from module.logger import logger
from module.ui.scroll import AdaptiveScroll
from tasks.base.assets.assets_base_page import MAP_EXIT
from tasks.base.assets.assets_base_popup import POPUP_CANCEL
from tasks.character.keywords import CharacterList
from tasks.combat.assets.assets_combat_prepare import COMBAT_PREPARE
from tasks.combat.assets.assets_combat_support import COMBAT_SUPPORT_LIST, COMBAT_SUPPORT_LIST_SCROLL_OE
from tasks.dungeon.dungeon import Dungeon
from tasks.ornament.assets.assets_ornament_combat import *
from tasks.ornament.assets.assets_ornament_ui import *
from tasks.rogue.route.loader import RouteLoader, model_from_json
from tasks.rogue.route.model import RogueRouteListModel, RogueRouteModel


class OrnamentCombat(Dungeon, RouteLoader):
    def combat_enter_from_map(self, skip_first_screenshot=True):
        # Don't enter from map, UI too deep inside
        # Enter from survival index instead
        pass

    def _combat_should_reenter(self):
        # Never re-enter, can only enter from Survival_Index
        return False

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

    @staticmethod
    def _support_scroll():
        """
        v3.2, Ornament has different support scroll so OrnamentCombat._support_scroll overrides
        """
        return AdaptiveScroll(area=COMBAT_SUPPORT_LIST_SCROLL_OE.area,
                              name=COMBAT_SUPPORT_LIST_SCROLL_OE.name)

    def _search_support_with_fallback(self, support_character_name: str = "JingYuan"):
        # In Ornament Extraction, first character isn't selected by default
        if support_character_name == "FirstCharacter":
            self._select_first()
            return True
        return super()._search_support_with_fallback(support_character_name)

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
        if isinstance(support_character_name, CharacterList):
            support_character_name = support_character_name.name
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
                    # Search support
                    if not selected_support:
                        self._search_support_with_fallback(support_character_name)
                        selected_support = True
                self.device.click(SUPPORT_ADD)
                self.interval_reset(COMBAT_SUPPORT_LIST)
                continue

    def get_equivalent_stamina(self):
        value = self.config.stored.Immersifier.value * 40
        if self.config.Ornament_UseStamina or self.config.stored.DungeonDouble.rogue > 0:
            value += self.config.stored.TrailblazePower.value
        return value

    def combat_get_trailblaze_power(self, expect_reduce=False, skip_first_screenshot=True) -> int:
        """
        Args:
            expect_reduce: Current value is supposed to be lower than the previous.
            skip_first_screenshot:

        Returns:
            int: Equivalent stamina

        Pages:
            in: COMBAT_PREPARE or COMBAT_REPEAT
        """
        logger.info(f'Ornament_UseStamina={self.config.Ornament_UseStamina}, '
                    f'DungeonDouble.rogue={self.config.stored.DungeonDouble.rogue}')
        before = self.get_equivalent_stamina()
        logger.info(f'equivalent_stamina: {before}')

        after = before
        for _ in range(3):
            self.update_stamina_status()
            after = self.get_equivalent_stamina()
            logger.info(f'equivalent_stamina: {after}')
            if expect_reduce:
                if before > after:
                    break
            else:
                break

        return after

    def _try_get_more_trablaize_power(self, cost):
        if self.config.Ornament_UseStamina or self.config.stored.DungeonDouble.rogue > 0:
            return super()._try_get_more_trablaize_power(cost)
        else:
            logger.info('Skip _try_get_more_trablaize_power')
            return False

    def is_trailblaze_power_exhausted(self):
        flag = self.get_equivalent_stamina() < self.combat_wave_cost
        logger.attr('TrailblazePowerExhausted', flag)
        return flag

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
        self.combat_wave_cost = 40

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
                logger.info('Combat map entered')
                self.device.screenshot_interval_set()
                break
            if self.is_combat_executing():
                self.device.screenshot_interval_set()
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
                self.device.screenshot_interval_set('combat')
                trial += 1
                continue
            if self.handle_popup_confirm():
                continue

        logger.hr('Route Ornament Extraction', level=1)
        self.route_run()
        return True

    @cached_property
    def all_route(self) -> "list[RogueRouteModel]":
        # Override to load route indexes from ornament
        routes = model_from_json(RogueRouteListModel, './route/ornament/route.json').root
        logger.attr('RouteLoaded', len(routes))
        return routes
