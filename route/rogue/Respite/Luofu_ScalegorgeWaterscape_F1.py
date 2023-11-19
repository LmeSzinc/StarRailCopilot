from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_ScalegorgeWaterscape
from tasks.map.route.base import locked_position, locked_rotation
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    @locked_position
    @locked_rotation(270)
    def Luofu_ScalegorgeWaterscape_F1_X701Y321(self):
        """
        | Waypoint      | Position                  | Direction | Rotation |
        | ------------- | ------------------------- | --------- | -------- |
        | spawn         | Waypoint((701.5, 320.8)), | 274.2     | 274      |
        | item_X691Y314 | Waypoint((691.4, 314.9)), | 315.9     | 301      |
        | herta         | Waypoint((673.0, 314.9)), | 300.1     | 297      |
        | exit_         | Waypoint((664.2, 319.4)), | 256.9     | 264      |
        """
        self.map_init(plane=Luofu_ScalegorgeWaterscape, floor="F1", position=(701.5, 320.8))
        item_X691Y314 = Waypoint((691.4, 314.9))
        herta = Waypoint((673.0, 314.9))
        exit_ = Waypoint((664.2, 319.4))

        self.clear_item(item_X691Y314)
        self.domain_herta(herta)
        self.domain_single_exit(exit_)
        # ===== End of generated waypoints =====
