from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_StargazerNavalia
from tasks.map.route.base import locked_rotation
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    @locked_rotation(90)
    def Luofu_StargazerNavalia_F2_X579Y183(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((579.8, 183.5)), | 96.7      | 91       |
        | event    | Waypoint((615.3, 195.5)), | 105.6     | 66       |
        | exit_    | Waypoint((627.2, 183.5)), | 96.7      | 91       |
        | exit1    | Waypoint((629.2, 179.2)), | 98.9      | 89       |
        | exit2    | Waypoint((630.9, 191.7)), | 99.0      | 89       |
        """
        self.map_init(plane=Luofu_StargazerNavalia, floor="F2", position=(579.8, 183.5))
        self.register_domain_exit(
            Waypoint((627.2, 183.5)), end_rotation=91,
            left_door=Waypoint((629.2, 179.2)), right_door=Waypoint((630.9, 191.7)))
        event = Waypoint((615.3, 195.5))

        self.clear_event(event)
        # ===== End of generated waypoints =====
