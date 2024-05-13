from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_ArtisanshipCommission
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_ArtisanshipCommission_F1_X385Y494(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((385.2, 494.6)), | 94.2      | 91       |
        | enemy    | Waypoint((444.2, 490.5)), | 94.2      | 91       |
        | reward   | Waypoint((448.6, 497.2)), | 149.7     | 91       |
        | exit_    | Waypoint((458.0, 483.7)), | 94.2      | 91       |
        """
        self.map_init(plane=Luofu_ArtisanshipCommission, floor="F1", position=(385.2, 494.6))
        enemy = Waypoint((444.2, 490.5))
        reward = Waypoint((448.6, 497.2))
        exit_ = Waypoint((458.0, 483.7))

        self.clear_elite(enemy)
        self.domain_reward(reward)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====

    def Luofu_ArtisanshipCommission_F1_X391Y493(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((385.2, 494.6)), | 94.2      | 91       |
        | enemy    | Waypoint((444.2, 490.5)), | 94.2      | 91       |
        | reward   | Waypoint((448.6, 497.2)), | 149.7     | 91       |
        | exit_    | Waypoint((458.0, 483.7)), | 94.2      | 91       |
        """
        self.map_init(plane=Luofu_ArtisanshipCommission, floor="F1", position=(391.1, 493.2))
        enemy = Waypoint((444.2, 490.5))
        reward = Waypoint((448.6, 497.2))
        exit_ = Waypoint((458.0, 483.7))

        self.clear_elite(enemy)
        self.domain_reward(reward)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====

        """
        Notes
        Luofu_ArtisanshipCommission_F1_X391Y493 is the same as Luofu_ArtisanshipCommission_F1_X385Y494
        but for wrong spawn point detected
        """
        # Best 3 predictions: [
        # ('Elite_Luofu_ArtisanshipCommission_F1_X385Y494', 0.182, (391.1, 493.2)),
        # ('Elite_Jarilo_CorridorofFadingEchoes_F1_X415Y933', 0.157, (364.0, 951.0)),
        # ('Elite_Jarilo_CorridorofFadingEchoes_F1_X415Y947', 0.157, (364.0, 951.0))
        # ]

    def Luofu_ArtisanshipCommission_F1_X504Y493(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((504.0, 493.4)), | 96.7      | 91       |
        | enemy    | Waypoint((554.0, 492.2)), | 96.7      | 91       |
        | reward   | Waypoint((564.8, 498.9)), | 134.2     | 128      |
        | exit_    | Waypoint((572.8, 486.4)), | 76.4      | 68       |
        """
        self.map_init(plane=Luofu_ArtisanshipCommission, floor="F1", position=(504.0, 493.4))
        enemy = Waypoint((554.0, 492.2))
        reward = Waypoint((564.8, 498.9))
        exit_ = Waypoint((572.8, 486.4))

        self.clear_elite(enemy)
        self.domain_reward(reward)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====
