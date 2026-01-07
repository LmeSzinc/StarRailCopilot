from module.logger import logger
from tasks.combat.combat import Combat
from tasks.daily.assets.assets_daily_trial import INFO_CLOSE, START_TRIAL
from tasks.daily.trail import CharacterTrial
from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_BackwaterPass
from tasks.map.route.base import RouteBase


class Route(RouteBase, Combat, CharacterTrial):
    def trial_combat_end(self):
        # Ended at START_TRIAL
        if self.match_template_color(START_TRIAL):
            logger.info('Trial ended at START_TRIAL')
            return True
        if self.is_in_main():
            logger.warning('Trial ended at is_in_main()')
            return True
        return False

    def wait_next_skill(self, expected_end=None, skip_first_screenshot=True):
        return super().wait_next_skill(expected_end=self.trial_combat_end, skip_first_screenshot=skip_first_screenshot)

    def walk_additional(self) -> bool:
        if self.appear_then_click(INFO_CLOSE, interval=2):
            return True
        return super().walk_additional()

    def combat_execute(self, expected_end=None):
        return super().combat_execute(expected_end=self.trial_combat_end)

    def route_item_enemy(self):
        self.enter_himeko_trial()
        self.map_init(plane=Jarilo_BackwaterPass, position=(519.9, 361.5))

        # Visit 3 items
        self.clear_item(
            Waypoint((587.6, 366.9)).run_2x(),
        )
        self.clear_item(
            Waypoint((575.5, 377.4)).straight_run(),
        )
        self.clear_item(
            # Go through arched door
            Waypoint((581.5, 383.3)).set_threshold(3),
            Waypoint((575.7, 417.2)),
        )
        # Goto boss
        self.clear_enemy(
            Waypoint((613.5, 427.3)).straight_run(),
        )

    def route_item(self):
        self.enter_himeko_trial()
        self.map_init(plane=Jarilo_BackwaterPass, position=(519.9, 361.5))

        # Visit 3 items
        self.clear_item(
            Waypoint((587.6, 366.9)).run_2x(),
        )
        self.clear_item(
            Waypoint((575.5, 377.4)).straight_run(),
        )
        self.clear_item(
            # Go through arched door
            Waypoint((581.5, 383.3)).set_threshold(3),
            Waypoint((575.7, 417.2)),
        )
        # Exit
        self.exit_trial()

    def route_enemy(self):
        self.enter_himeko_trial()
        self.map_init(plane=Jarilo_BackwaterPass, position=(519.9, 361.5))

        # Goto boss
        self.clear_enemy(
            # Before the corner, turn right
            Waypoint((571.7, 371.3)),
            # Go through arched door
            Waypoint((581.5, 383.3)),
            # Boss
            Waypoint((613.5, 427.3)).straight_run(),
        )

    def exit(self):
        # Fake map_init to expose this method
        # self.map_init(plane=Jarilo_BackwaterPass, position=(519.9, 361.5))
        self.exit_trial_to_main()
