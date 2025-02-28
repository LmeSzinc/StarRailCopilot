from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_StargazerNavalia
from tasks.map.route.base import locked_rotation
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    @locked_rotation(90)
    def Luofu_StargazerNavalia_F1_X617Y511(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((617.5, 511.5)), | 96.7      | 91       |
        | enemy    | Waypoint((664.6, 512.6)), | 96.8      | 94       |
        | reward   | Waypoint((677.1, 521.2)), | 212.8     | 108      |
        | exit_    | Waypoint((684.6, 505.0)), | 91.3      | 82       |
        """
        self.map_init(plane=Luofu_StargazerNavalia, floor="F1", position=(617.5, 511.5))
        enemy = Waypoint((664.6, 512.6))
        reward = Waypoint((677.1, 521.2))
        exit_ = Waypoint((684.6, 505.0))

        self.clear_elite(enemy)
        self.domain_reward(reward)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====

    @locked_rotation(90)
    def Luofu_StargazerNavalia_F1_X621Y507(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((617.5, 511.5)), | 96.7      | 91       |
        | enemy    | Waypoint((664.6, 512.6)), | 96.8      | 94       |
        | reward   | Waypoint((677.1, 521.2)), | 212.8     | 108      |
        | exit_    | Waypoint((684.6, 505.0)), | 91.3      | 82       |
        """
        self.map_init(plane=Luofu_StargazerNavalia, floor="F1", position=(621.0, 507.0))
        enemy = Waypoint((664.6, 512.6))
        reward = Waypoint((677.1, 521.2))
        exit_ = Waypoint((684.6, 505.0))

        self.clear_elite(enemy)
        self.domain_reward(reward)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====

        """
        Notes
        Luofu_StargazerNavalia_F1_X621Y507 is the same as Luofu_StargazerNavalia_F1_X617Y511
        but for wrong spawn point detected
        """
        # Best 3 predictions: [
        # ('Elite_Luofu_StargazerNavalia_F1_X617Y511', 0.338, (621.0, 507.0)),
        # ('Elite_Luofu_ArtisanshipCommission_F1_X385Y494', 0.203, (329.2, 492.8)),
        # ('Elite_Jarilo_SilvermaneGuardRestrictedZone_F1_X225Y425', 0.181, (224.8, 423.2))
        # ]
