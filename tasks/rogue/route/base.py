from module.base.button import ClickButton
from module.base.timer import Timer
from module.base.utils import area_offset
from module.logger import logger
from tasks.base.page import page_rogue
from tasks.character.switch import CharacterSwitch
from tasks.daily.use_technique import UseTechniqueUI
from tasks.map.control.waypoint import Waypoint, ensure_waypoints
from tasks.map.route.base import RouteBase as RouteBase_
from tasks.rogue.assets.assets_rogue_ui import BLESSING_CONFIRM
from tasks.rogue.assets.assets_rogue_weekly import ROGUE_REPORT
from tasks.rogue.blessing.blessing import RogueBlessingSelector
from tasks.rogue.blessing.bonus import RogueBonusSelector
from tasks.rogue.blessing.curio import RogueCurioSelector
from tasks.rogue.event.event import RogueEvent
from tasks.rogue.event.reward import RogueReward
from tasks.rogue.route.exit import RogueExit


class RouteBase(RouteBase_, RogueExit, RogueEvent, RogueReward):
    registered_domain_exit = None

    def combat_expected_end(self):
        if self.is_page_choose_blessing():
            logger.info('Combat ended at is_page_choose_blessing()')
            return True
        if self.is_page_choose_curio():
            logger.info('Combat ended at is_page_choose_curio()')
            return True
        if self.is_page_choose_bonus():
            logger.info('Combat ended at is_page_choose_bonus()')
            return True

        return False

    def combat_execute(self, expected_end=None):
        return super().combat_execute(expected_end=self.combat_expected_end)

    def walk_additional(self) -> bool:
        if self.handle_blessing_popup():
            return True
        return super().walk_additional()

    def handle_blessing(self):
        """
        Returns:
            bool: If handled
        """
        if self.is_page_choose_blessing():
            logger.hr('Choose blessing', level=2)
            selector = RogueBlessingSelector(self)
            selector.recognize_and_select()
            return True
        if self.is_page_choose_curio():
            logger.hr('Choose curio', level=2)
            selector = RogueCurioSelector(self)
            selector.recognize_and_select()
            return True
        if self.is_page_choose_bonus():
            logger.hr('Choose bonus', level=2)
            selector = RogueBonusSelector(self)
            selector.recognize_and_select()
            return True
        if self.handle_blessing_popup():
            return True

        return False

    def clear_blessing(self, skip_first_screenshot=True):
        """
        Pages:
            in: combat_expected_end()
            out: is_in_main()

        Returns:
            bool: If cleared
        """
        logger.info('Clear blessing')
        cleared = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_in_main():
                logger.info(f'clear_blessing() ended at page_main')
                if cleared:
                    self.wait_until_minimap_stabled()
                return cleared

            if self.handle_blessing():
                cleared = True
                continue

    def clear_occurrence(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_rogue, occurrence
            out: is_in_main()
        """
        logger.info('Clear occurrence')
        self.event_title = None
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_in_main():
                logger.info(f'clear_occurrence() ended at page_main')
                break

            if self.handle_reward(interval=2):
                continue
            if self.is_combat_executing():
                logger.hr('Combat', level=2)
                self.combat_execute()
                continue
            if self.handle_blessing():
                continue
            if self.ui_page_appear(page_rogue):
                if self.handle_event_continue():
                    continue
                if self.handle_event_option():
                    continue

    def _goto(self, *args, **kwargs):
        result = super()._goto(*args, **kwargs)
        if 'enemy' in result:
            self.clear_blessing()
        return result

    def wait_until_minimap_stabled(self):
        logger.info('Wait until minimap stabled')
        radius = self.minimap.MINIMAP_RADIUS
        area = area_offset((-radius, -radius, radius, radius), offset=self.minimap.MINIMAP_CENTER)
        minimap = ClickButton(area, name='MINIMAP')
        self.wait_until_stable(minimap, timeout=Timer(1.5, count=5))

    def clear_enemy(self, *waypoints):
        waypoints = ensure_waypoints(waypoints)
        if self.plane.is_rogue_combat:
            for point in waypoints:
                if 'item' not in point.expected_enroute:
                    point.expected_enroute.append('item')

        # Use techniques before enemy
        logger.info('Trying to use technique')
        UseTechniqueUI(self.config, self.device).use_background_technique()

        return super().clear_enemy(*waypoints)

    def clear_item(self, *waypoints):
        """
        Shorten unexpected timer as items are randomly generated
        """
        waypoints = ensure_waypoints(waypoints)
        end_point = waypoints[-1]
        if self.plane.is_rogue_combat or self.plane.is_rogue_occurrence:
            end_point.unexpected_confirm = Timer(1, count=5)
        return super().clear_item(*waypoints)

    """
    Additional rogue methods
    """

    def clear_elite(self, *waypoints):
        # Use techniques before BOSS
        logger.info('Trying to use technique')
        if self.plane.is_rogue_boss:
            UseTechniqueUI(self.config, self.device).use_background_technique_deplete()
        else:
            UseTechniqueUI(self.config, self.device).use_background_technique()

        logger.hr('Clear elite', level=1)
        waypoints = ensure_waypoints(waypoints)
        end_point = waypoints[-1]
        end_point.speed = 'run_2x'

        result = super().clear_enemy(*waypoints)
        # logger.attr("result",result)

        if 'enemy' in result:
            # runs when one elite battle finishes, and decreases rogue farming count by 1
            if self.config.RogueWorld_WeeklyFarming and self.config.stored.SimulatedUniverseElite.farm_not_complete():
                self.config.stored.SimulatedUniverseElite.farm_dec()
                logger.info(
                    f"Cleared elite boss, decreasing farming count by 1, now {self.config.stored.SimulatedUniverseElite.farm_get_remain()}")
        return result

    def _domain_event_expected_end(self):
        """
        Returns:
            bool: If entered event
        """
        if self.ui_page_appear(page_rogue):
            return True
        return False

    def clear_event(self, *waypoints):
        """
        Handle an event in DomainOccurrence, DomainEncounter, DomainTransaction
        """
        logger.hr('Clear event', level=1)
        waypoints = ensure_waypoints(waypoints)
        end_point = waypoints[-1]
        end_point.endpoint_threshold = 1.5
        end_point.interact_radius = 7
        end_point.expected_end.append(self._domain_event_expected_end)
        if self.plane.is_rogue_occurrence:
            for point in waypoints:
                if 'item' not in point.expected_enroute:
                    point.expected_enroute.append('item')

        result = self.goto(*waypoints)
        self.clear_occurrence()
        return result

    def domain_reward(self, *waypoints):
        """
        Get reward of the DomainElite and DomainBoss
        """
        logger.hr('Clear reward', level=1)
        if self.can_claim_domain_reward(
                use_trailblaze_power=self.config.RogueWorld_UseStamina,
                use_immersifier=self.config.RogueWorld_UseImmersifier,
        ):
            result = self.goto(*waypoints)
            self.claim_domain_reward(
                use_trailblaze_power=self.config.RogueWorld_UseStamina,
                use_immersifier=self.config.RogueWorld_UseImmersifier,
            )
        else:
            result = []

        return result

    def domain_herta(self, *waypoints):
        """
        Most people don't buy herta shop, skip
        """
        pass

    def _domain_exit_expected_end(self):
        """
        Returns:
            bool: If domain exited
        """
        if self.is_map_loading():
            logger.info('domain exit: is_map_loading()')
            return True
        # No loading after elite
        if self.is_map_loading_black():
            logger.info('domain exit: is_map_loading_black()')
            return True
        # Rogue cleared
        if self.appear(ROGUE_REPORT, interval=2):
            logger.info(f'domain exit: {ROGUE_REPORT}')
            return True

        if self.handle_popup_confirm():
            return False

        return False

    def _domain_exit_wait_next(self, skip_first_screenshot=True):
        """
        Pages:
            in: is_map_loading()
            out: page_main
                or page_rogue if rogue cleared
        """
        logger.info('Wait next domain')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_in_main():
                logger.info('Entered another domain')
                self.wait_until_minimap_stabled()
                break
            if self.is_page_rogue_main():
                logger.info('Rogue cleared')
                break

            if self.match_template_color(ROGUE_REPORT, interval=2):
                logger.info(f'{ROGUE_REPORT} -> {BLESSING_CONFIRM}')
                self.device.click(BLESSING_CONFIRM)
                continue
            if self.handle_blessing():
                continue
            # Confirm that leave without getting rewards
            if self.handle_popup_confirm():
                continue
            # First-time cleared reward
            if self.handle_reward():
                continue
            # Get Herta
            if self.handle_get_character():
                continue

    def domain_single_exit(self, *waypoints):
        """
        Goto a single exit, exit current domain
        end_rotation is not required
        """
        logger.hr('Domain single exit', level=1)
        waypoints = ensure_waypoints(waypoints)

        for point in waypoints:
            if 'item' not in point.expected_enroute:
                point.expected_enroute.append('item')

        end_point = waypoints[-1]
        end_point.min_speed = 'run'
        end_point.interact_radius = 5
        end_point.expected_end.append(self._domain_exit_expected_end)

        result = self.goto(*waypoints)
        self._domain_exit_wait_next()
        return result

    def _domain_exit_old(self):
        """
        An old implementation that go along specific direction without retries
        """
        logger.info(f'Using old predict_door()')
        direction = self.predict_door_old()
        direction_limit = 55
        if direction is not None:
            if abs(direction) > direction_limit:
                logger.warning(f'Unexpected direction to go: {direction}, limited in {direction_limit}')
                if direction > 0:
                    direction = direction_limit
                elif direction < 0:
                    direction = -direction_limit

            point = Waypoint(
                position=(0, 0),
                min_speed='run',
                lock_direction=direction,
                interact_radius=10000,
                expected_end=[self._domain_exit_expected_end],
            )
            self.goto(point)
            self._domain_exit_wait_next()
        return True

    def domain_exit(
            self,
            *waypoints,
            end_rotation: int = None,
            left_door: Waypoint = None,
            right_door: Waypoint = None
    ):
        """
        Goto domain exit, choose one door, goto door
        """
        logger.hr('Domain exit', level=1)
        # Goto the front of the two doors
        waypoints = ensure_waypoints(waypoints)
        end_point = waypoints[-1]
        end_point.endpoint_threshold = 1.5
        self.goto(*waypoints)

        # Rotate camera to insight two doors
        logger.hr('End rotation', level=2)
        self.rotation_set(end_rotation, threshold=10)

        # Choose a door
        logger.hr('Find domain exit', level=2)
        logger.info(f'Migrate={self.config.RogueDebug_DebugMode}, left_door={left_door}, right_door={right_door}')
        if not self.config.RogueDebug_DebugMode and (not left_door and not right_door):
            return self._domain_exit_old()

        logger.info(f'Using new predict_door()')
        door = self.predict_door()
        if self.config.RogueDebug_DebugMode and self.exit_has_double_door and (not left_door or not right_door):
            logger.critical(f'Domain exit is not defined, please record it: {self.route_func}')
            exit(1)

        # Goto door
        if door == 'left_door':
            if not left_door:
                return self._domain_exit_old()
            if self.domain_single_exit(left_door):
                return True
            else:
                logger.error('Cannot goto either exit doors, try both')
                if self.domain_single_exit(right_door):
                    return True
                else:
                    return False
        elif door == 'right_door':
            if not right_door:
                return self._domain_exit_old()
            if self.domain_single_exit(right_door):
                return True
            else:
                logger.error('Cannot goto either exit doors, try both')
                if self.domain_single_exit(left_door):
                    return True
                else:
                    return False
        else:
            logger.error('Cannot goto either exit doors, try both')
            if not left_door:
                return self._domain_exit_old()
            if not right_door:
                return self._domain_exit_old()
            if self.domain_single_exit(left_door):
                return True
            elif self.domain_single_exit(right_door):
                return True
            else:
                return False

    """
    Route
    """

    def register_domain_exit(
            self,
            *waypoints,
            end_rotation: int = None,
            left_door: Waypoint = None,
            right_door: Waypoint = None
    ):
        """
        Register an exit, call `domain_exit()` at route end
        """
        self.registered_domain_exit = (waypoints, end_rotation, left_door, right_door)

    def before_route(self):
        self.registered_domain_exit = None

    def after_route(self):
        if self.registered_domain_exit is not None:
            waypoints, end_rotation, left_door, right_door = self.registered_domain_exit
            self.domain_exit(
                *waypoints,
                end_rotation=end_rotation,
                left_door=left_door,
                right_door=right_door,
            )
        else:
            logger.info('No domain exit registered')
