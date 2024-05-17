from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_CorridorofFadingEchoes
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_CorridorofFadingEchoes_F1_X415Y933(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((415.5, 947.9)), | 96.7      | 91       |
        | enemy    | Waypoint((464.0, 953.0)), | 96.8      | 94       |
        | reward   | Waypoint((472.7, 958.5)), | 214.6     | 114      |
        | exit_    | Waypoint((480.0, 944.0)), | 92.7      | 84       |
        """
        self.map_init(plane=Jarilo_CorridorofFadingEchoes, floor="F1", position=(415.5, 933))
        enemy = Waypoint((464.0, 953.0))
        reward = Waypoint((472.7, 958.5))
        exit_ = Waypoint((480.0, 944.0))

        self.clear_elite(enemy)
        self.domain_reward(reward)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====

        """
        Notes
        Jarilo_CorridorofFadingEchoes_F1_X415Y933 is the same as Jarilo_CorridorofFadingEchoes_F1_X415Y947
        but for wrong spawn point detected
        """

    def Jarilo_CorridorofFadingEchoes_F1_X415Y953(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((415.5, 947.9)), | 96.7      | 91       |
        | enemy    | Waypoint((464.0, 953.0)), | 96.8      | 94       |
        | reward   | Waypoint((472.7, 958.5)), | 214.6     | 114      |
        | exit_    | Waypoint((480.0, 944.0)), | 92.7      | 84       |
        """
        self.map_init(plane=Jarilo_CorridorofFadingEchoes, floor="F1", position=(415.4, 953.3))
        enemy = Waypoint((464.0, 953.0))
        reward = Waypoint((472.7, 958.5))
        exit_ = Waypoint((480.0, 944.0))

        self.clear_elite(enemy)
        self.domain_reward(reward)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====

        """
        Notes
        Jarilo_CorridorofFadingEchoes_F1_X415Y953 is the same as Jarilo_CorridorofFadingEchoes_F1_X415Y947
        but for wrong spawn point detected
        """
        # Best 3 predictions: [
        # ('Elite_Jarilo_CorridorofFadingEchoes_F1_X415Y933', 0.169, (415.4, 953.3)),
        # ('Elite_Jarilo_CorridorofFadingEchoes_F1_X415Y947', 0.169, (415.4, 953.3)),
        # ('Elite_Herta_SupplyZone_F2_X680Y247', 0.162, (738.4, 252.2))
        # ]

    def Jarilo_CorridorofFadingEchoes_F1_X415Y947(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((415.5, 947.9)), | 96.7      | 91       |
        | enemy    | Waypoint((464.0, 953.0)), | 96.8      | 94       |
        | reward   | Waypoint((472.7, 958.5)), | 214.6     | 114      |
        | exit_    | Waypoint((480.0, 944.0)), | 92.7      | 84       |
        """
        self.map_init(plane=Jarilo_CorridorofFadingEchoes, floor="F1", position=(415.5, 947.9))
        enemy = Waypoint((464.0, 953.0))
        reward = Waypoint((472.7, 958.5))
        exit_ = Waypoint((480.0, 944.0))

        self.clear_elite(enemy)
        self.domain_reward(reward)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====
