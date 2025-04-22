from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Amphoreus_StrifeRuinsCastrumKremnos
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Amphoreus_StrifeRuinsCastrumKremnos_F1OE_X373Y317(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((373.2, 317.4)), | 4.2       | 1        |
        | enemy    | Waypoint((368.4, 281.3)), | 11.2      | 4        |
        | exit_    | Waypoint((368.4, 281.3)), | 11.2      | 4        |
        """
        self.map_init(plane=Amphoreus_StrifeRuinsCastrumKremnos, floor="F1OE", position=(373.2, 317.4))
        self.register_domain_exit(Waypoint((368.4, 281.3)), end_rotation=4)
        enemy = Waypoint((368.4, 281.3))
        # ===== End of generated waypoints =====

        self.clear_enemy(enemy)
