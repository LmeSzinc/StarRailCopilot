import module.config.server as server
from module.device.platform.utils import cached_property
from module.exception import RequestHumanTakeover
from module.logger import logger
from tasks.base.assets.assets_base_page import MAP_EXIT
from tasks.combat.assets.assets_combat_prepare import COMBAT_PREPARE, WAVE_CHECK, WAVE_CHECK_SEARCH
from tasks.combat.prepare import WaveDigit
from tasks.dungeon.dungeon import Dungeon
from tasks.dungeon.keywords import DungeonList
from tasks.item.slider import Slider
from tasks.map.keywords import MapPlane
from tasks.ornament.assets.assets_ornament_combat import *
from tasks.ornament.assets.assets_ornament_prepare import *
from tasks.ornament.assets.assets_ornament_special import *
from tasks.ornament.assets.assets_ornament_ui import *
from tasks.ornament.team import OrnamentTeam
from tasks.rogue.route.loader import RouteLoader, model_from_json
from tasks.rogue.route.model import RogueRouteListModel, RogueRouteModel


class OrnamentTeamNotPrepared(Exception):
    pass


class OrnamentCombat(Dungeon, RouteLoader, OrnamentTeam):
    def combat_enter_from_map(self, skip_first_screenshot=True):
        # Don't enter from map, UI too deep inside
        # Enter from survival index instead
        pass

    def _combat_should_reenter(self):
        # Never re-enter, can only enter from Survival_Index
        return False

    def _dungeon_run(self, dungeon: DungeonList, team: int = None, wave_limit: int = 0, support_character: str = None,
                     skip_ui_switch: bool = False):

        # Always skip_ui_switch = False
        # because you can't easily enter ornament from map, it's better enter from page_quest
        skip_ui_switch = False
        return super()._dungeon_run(
            dungeon=dungeon, team=team, wave_limit=wave_limit,
            support_character=support_character, skip_ui_switch=skip_ui_switch)

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
            if self.ui_additional():
                continue

    def route_error_postprocess(self):
        """
        When having route error, leave for now and re-enter
        May be another trial would fix it
        """
        self.oe_leave()
        return True

    @cached_property
    def _dict_character_slot(self):
        return {
            1: OE_SLOT_1,
            2: OE_SLOT_2,
            3: OE_SLOT_3,
            4: OE_SLOT_4,
        }

    def _on_enter_support(self):
        # ornament support has not tab
        self._support_disable_friend_only()

    def support_set(
            self,
            name: str = "FirstCharacter",
            replace=4,
            support_button=SUPPORT_ADD,
            dismiss_button=SUPPORT_DISMISS,
            confirm_button=PREPARE_CLOSE,
    ):
        super().support_set(
            name, replace=replace,
            support_button=support_button, dismiss_button=dismiss_button, confirm_button=confirm_button)

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

    def combat_set_wave(self, count=6, total=6):
        """
        Args:
            count: 1 to 6
            total: 3 or 6 or 24

        Pages:
            in: COMBAT_PREPARE
        """
        slider = Slider(main=self, slider=WAVE_SLIDER_OE)
        # fixed total at 6
        slider.set(count, 6)
        self.ui_ensure_index(
            count, letter=WaveDigit(OCR_WAVE_COUNT_OE, lang=server.lang),
            next_button=WAVE_PLUS_OE, prev_button=WAVE_MINUS_OE,
            skip_first_screenshot=True
        )

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
        logger.hr('Combat prepare')

        # wait WAVE_SLIDER_OE
        WAVE_CHECK.load_search(WAVE_CHECK_SEARCH)
        for _ in self.loop():
            if self.match_template_luma(WAVE_CHECK):
                break

        # set wave, a simplified handle_combat_prepare()
        self.combat_get_trailblaze_power()
        current = self.get_equivalent_stamina()
        total = 6
        cost = 40
        logger.attr('CombatWaveTotal', total)
        self.combat_waves = min(current // cost, total)
        if self.combat_wave_limit:
            self.combat_waves = min(self.combat_waves, self.combat_wave_limit - self.combat_wave_done)
            logger.info(
                f'Current has {current}, combat costs {cost}, '
                f'wave={self.combat_wave_done}/{self.combat_wave_limit}, '
                f'able to do {self.combat_waves} waves')
        else:
            logger.info(f'Current has {current}, combat costs {cost}, '
                        f'able to do {self.combat_waves} waves')
        if self.combat_waves > 0:
            self.combat_set_wave(self.combat_waves, total)
        else:
            logger.error('Not enough stamina to run ornament, we should not enter ornament at the first place')
            self.oe_leave()
            return False

        # select team
        team = self.config.Ornament_Team40
        team_set = False
        if team > 0:
            if self.ornament_team_set(team):
                team_set = True
        if not team_set:
            slots = 4 - len(self._get_empty_slot())
            logger.attr('TeamSlotsPrepared', slots)
            if slots <= 0:
                logger.error(f'Please prepare your team in Ornament Extraction')
                raise OrnamentTeamNotPrepared

        # select support
        if support_character:
            # Block COMBAT_TEAM_PREPARE before support set
            support_set = False
        else:
            support_set = True
        replace = self.config.DungeonSupport_Replace
        logger.info([support_character, support_set, replace])
        if support_character:
            self.support_set(support_character, replace=replace)

        # enter combat
        trial = 0
        for _ in self.loop():
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

            # Click
            if self.appear(COMBAT_PREPARE, interval=5):
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

    def route_special_match(self, plane: MapPlane):
        # No black floors loaded
        if self.appear(Amphoreus_StrifeRuinsCastrumKremnos_F1OE_X373Y317):
            return 'Combat_Amphoreus_StrifeRuinsCastrumKremnos_F1OE_X373Y317'
        super().route_special_match(plane)
