from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Penacony_TheReverieReality
from tasks.ornament.route_base import RouteBase


class Route(RouteBase):

    def Penacony_TheReverieReality_F1_X245Y233(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((245.3, 233.3)), | 4.2       | 1        |
        | enemy    | Waypoint((245.4, 197.6)), | 11.1      | 1        |
        """
        self.map_init(plane=Penacony_TheReverieReality, floor="F1", position=(245.3, 233.3))
        enemy = Waypoint((245.4, 197.6))
        # ===== End of generated waypoints =====

        self.minimap.lock_rotation(0)
        self.clear_enemy(enemy)
