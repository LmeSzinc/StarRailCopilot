from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Herta_StorageZone
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Herta_StorageZone_F2_X363Y166(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((363.4, 166.9)), | 274.2     | 274      |
        | item     | Waypoint((332.8, 172.0)), | 263.8     | 260      |
        | event    | Waypoint((318.9, 155.2)), | 290.1     | 285      |
        | exit_    | Waypoint((314.3, 164.1)), | 276.0     | 271      |
        | exit1    | Waypoint((305.2, 169.2)), | 275.9     | 274      |
        | exit2    | Waypoint((304.6, 160.8)), | 277.8     | 276      |
        """
        self.map_init(plane=Herta_StorageZone, floor="F2", position=(363.4, 166.9))
        self.register_domain_exit(
            Waypoint((314.3, 164.1)), end_rotation=271,
            left_door=Waypoint((305.2, 169.2)), right_door=Waypoint((304.6, 160.8)))
        item = Waypoint((332.8, 172.0))
        event = Waypoint((318.9, 155.2))

        self.clear_item(item)
        self.clear_event(event)
        # ===== End of generated waypoints =====
