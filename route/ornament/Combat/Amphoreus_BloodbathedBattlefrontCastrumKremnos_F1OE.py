from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Amphoreus_BloodbathedBattlefrontCastrumKremnos
from tasks.ornament.route_base import RouteBase


class Route(RouteBase):

    def Amphoreus_BloodbathedBattlefrontCastrumKremnos_F1OE_X155Y669(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((155.5, 669.3)), | 4.2       | 4        |
        | enemy    | Waypoint((155.9, 627.4)), | 278.1     | 1        |
        """
        self.map_init(plane=Amphoreus_BloodbathedBattlefrontCastrumKremnos, floor="F1OE", position=(155.5, 669.3))
        enemy = Waypoint((155.9, 627.4))
        # ===== End of generated waypoints =====

        self.minimap.lock_rotation(0)
        self.clear_enemy(enemy)
