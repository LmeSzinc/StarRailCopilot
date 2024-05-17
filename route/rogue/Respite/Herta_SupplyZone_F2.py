from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Herta_SupplyZone
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Herta_SupplyZone_F2_X554Y245(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((554.6, 245.0)), | 274.2     | 274      |
        | item     | Waypoint((541.9, 238.4)), | 308.0     | 301      |
        | herta    | Waypoint((506.8, 238.4)), | 283.0     | 281      |
        | exit_    | Waypoint((495.0, 244.8)), | 283.0     | 274      |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2", position=(554.6, 245.0))
        item = Waypoint((541.9, 238.4))
        herta = Waypoint((506.8, 238.4))
        exit_ = Waypoint((495.0, 244.8))

        self.clear_item(item)
        self.domain_herta(herta)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====

    def Herta_SupplyZone_F2_X550Y248(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((554.6, 245.0)), | 274.2     | 274      |
        | item     | Waypoint((541.9, 238.4)), | 308.0     | 301      |
        | herta    | Waypoint((506.8, 238.4)), | 283.0     | 281      |
        | exit_    | Waypoint((495.0, 244.8)), | 283.0     | 274      |
        """
        self.map_init(plane=Herta_SupplyZone, floor="F2", position=(550.7, 248.7))
        item = Waypoint((541.9, 238.4))
        herta = Waypoint((506.8, 238.4))
        exit_ = Waypoint((495.0, 244.8))

        self.clear_item(item)
        self.domain_herta(herta)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====

        # Best 3 predictions: [('Respite_Herta_SupplyZone_F2_X554Y245', 0.257, (550.7, 248.7)),
        """
        Notes
        Herta_SupplyZone_F2_X550Y248 is the same as Herta_SupplyZone_F2_X554Y245
        but for wrong spawn point detected
        """
