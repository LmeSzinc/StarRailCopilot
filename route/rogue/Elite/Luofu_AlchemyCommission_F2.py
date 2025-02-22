from module.logger import logger
from tasks.map.control.waypoint import Waypoint, ensure_waypoints
from tasks.map.keywords.plane import Luofu_AlchemyCommission
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_AlchemyCommission_F2_X625Y590(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((623.1, 590.0)), | 282.2     | 274      |
        | enemy    | Waypoint((571.6, 589.5)), | 282.0     | 274      |
        | reward   | Waypoint((563.5, 581.4)), | 281.9     | 274      |
        | exit_    | Waypoint((555.5, 597.3)), | 267.8     | 264      |
        """
        self.map_init(plane=Luofu_AlchemyCommission, floor="F2", position=(623.1, 590.0))
        enemy = Waypoint((571.6, 589.5))
        reward = Waypoint((563.5, 581.4))
        exit_ = Waypoint((555.5, 597.3))

        self.clear_elite(enemy)
        self.domain_reward(reward)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====

    def Luofu_AlchemyCommission_F2_X664Y545(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((623.1, 590.0)), | 282.2     | 274      |
        | enemy    | Waypoint((571.6, 589.5)), | 282.0     | 274      |
        | reward   | Waypoint((563.5, 581.4)), | 281.9     | 274      |
        | exit_    | Waypoint((555.5, 597.3)), | 267.8     | 264      |
        """
        self.map_init(plane=Luofu_AlchemyCommission, floor="F2", position=(664.2, 546.8))
        enemy = Waypoint((571.6, 589.5))
        reward = Waypoint((563.5, 581.4))
        exit_ = Waypoint((555.5, 597.3))

        self.clear_elite(enemy)
        self.domain_reward(reward)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====

        """
        Notes
        Luofu_AlchemyCommission_F2_X664Y545 is the same as Luofu_AlchemyCommission_F2_X625Y590
        but for wrong spawn point detected

        Spawn point is too far from the correct result but should be fine in Boss room
        """

    def clear_elite(self, *waypoints):
        logger.hr('Clear elite', level=1)
        waypoints = ensure_waypoints(waypoints)
        # No running
        # end_point = waypoints[-1]
        # end_point.speed = 'run_2x'

        # TODO: Use techniques before BOSS
        pass

        result = super().clear_enemy(*waypoints)
        # logger.attr("result",result)
        self.after_elite(result)
        return result
