from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Jarilo_CorridorofFadingEchoes
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Jarilo_CorridorofFadingEchoes_F1_X236Y903(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((236.6, 903.4)), | 274.2     | 274      |
        | event    | Waypoint((194.4, 898.0)), | 289.1     | 290      |
        | exit_    | Waypoint((175.0, 902.8)), | 12.8      | 274      |
        | exit1    | Waypoint((167.5, 909.4)), | 277.8     | 274      |
        | exit2    | Waypoint((164.6, 893.2)), | 275.9     | 276      |
        """
        self.map_init(plane=Jarilo_CorridorofFadingEchoes, floor="F1", position=(236.6, 903.4))
        self.register_domain_exit(
            Waypoint((175.0, 902.8)), end_rotation=274,
            left_door=Waypoint((167.5, 909.4)), right_door=Waypoint((164.6, 893.2)))
        event = Waypoint((194.4, 898.0))

        self.clear_event(event)
        # ===== End of generated waypoints =====

    def Jarilo_CorridorofFadingEchoes_F1_X265Y963(self):
        """
        | Waypoint | Position                   | Direction | Rotation |
        | -------- | -------------------------- | --------- | -------- |
        | spawn    | Waypoint((265.5, 963.6)),  | 233.8     | 230      |
        | item     | Waypoint((250.1, 970.4)),  | 157.2     | 244      |
        | event    | Waypoint((231.8, 991.0)),  | 233.9     | 230      |
        | exit_    | Waypoint((227.6, 1000.4)), | 229.9     | 228      |
        | exit1    | Waypoint((227.6, 1007.8)), | 223.8     | 223      |
        | exit2    | Waypoint((221.4, 999.5)),  | 223.8     | 223      |
        """
        self.map_init(plane=Jarilo_CorridorofFadingEchoes, floor="F1", position=(265.5, 963.6))
        self.register_domain_exit(
            Waypoint((227.6, 1000.4)), end_rotation=228,
            left_door=Waypoint((227.6, 1007.8)), right_door=Waypoint((221.4, 999.5)))
        item = Waypoint((250.1, 970.4))
        event = Waypoint((231.8, 991.0))

        self.clear_item(item)
        self.clear_event(event)
        # ===== End of generated waypoints =====

    def Jarilo_CorridorofFadingEchoes_F1_X309Y537(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((309.3, 537.8)), | 190.1     | 184      |
        | event    | Waypoint((302.6, 580.8)), | 193.1     | 191      |
        | exit_    | Waypoint((308.9, 591.0)), | 187.1     | 181      |
        | exit1    | Waypoint((315.4, 597.4)), | 191.8     | 181      |
        | exit2    | Waypoint((303.2, 597.2)), | 191.8     | 184      |
        """
        self.map_init(plane=Jarilo_CorridorofFadingEchoes, floor="F1", position=(309.3, 537.8))
        self.register_domain_exit(
            Waypoint((308.9, 591.0)), end_rotation=181,
            left_door=Waypoint((315.4, 597.4)), right_door=Waypoint((303.2, 597.2)))
        event = Waypoint((302.6, 580.8))

        self.clear_event(event)
        # ===== End of generated waypoints =====
