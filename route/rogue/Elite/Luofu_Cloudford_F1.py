from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_Cloudford
from tasks.map.route.base import locked_rotation
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    @locked_rotation(0)
    def Luofu_Cloudford_F1_X337Y1003(self):
        """
        | Waypoint | Position                   | Direction | Rotation |
        | -------- | -------------------------- | --------- | -------- |
        | spawn    | Waypoint((337.3, 1003.4)), | 6.7       | 4        |
        | enemy    | Waypoint((336.2, 962.2)),  | 6.7       | 4        |
        | reward   | Waypoint((342.9, 950.8)),  | 44.2      | 31       |
        | exit_    | Waypoint((328.8, 942.8)),  | 316.1     | 331      |
        """
        self.map_init(plane=Luofu_Cloudford, floor="F1", position=(337.3, 1003.4))
        enemy = Waypoint((336.2, 962.2))
        reward = Waypoint((342.9, 950.8))
        exit_ = Waypoint((328.8, 942.8))

        self.clear_elite(enemy)
        self.domain_reward(reward)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====

    @locked_rotation(0)
    def Luofu_Cloudford_F1_X342Y1003(self):
        """
        | Waypoint | Position                   | Direction | Rotation |
        | -------- | -------------------------- | --------- | -------- |
        | spawn    | Waypoint((337.3, 1003.4)), | 6.7       | 4        |
        | enemy    | Waypoint((336.2, 962.2)),  | 6.7       | 4        |
        | reward   | Waypoint((342.9, 950.8)),  | 44.2      | 31       |
        | exit_    | Waypoint((328.8, 942.8)),  | 316.1     | 331      |
        """
        self.map_init(plane=Luofu_Cloudford, floor="F1", position=(342.3, 1003.4))
        enemy = Waypoint((336.2, 962.2))
        reward = Waypoint((342.9, 950.8))
        exit_ = Waypoint((328.8, 942.8))

        self.clear_elite(enemy)
        self.domain_reward(reward)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====

        """
        Notes
        Luofu_Cloudford_F1_X342Y1003 is the same as Luofu_Cloudford_F1_X337Y1003
        but for wrong spawn point detected
        """
        # Best 3 predictions: [
        # ('Elite_Luofu_Cloudford_F1_X337Y1003', 0.169, (342.3, 1002.7)),
        # ('Elite_Luofu_ArtisanshipCommission_F1_X504Y493', 0.106, (519.3, 452.7)),
        # ('Elite_Jarilo_CorridorofFadingEchoes_F1_X415Y933', 0.104, (433.8, 982.0))
        # ]
