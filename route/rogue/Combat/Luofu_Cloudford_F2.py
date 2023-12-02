from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_Cloudford
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_Cloudford_F2_X425Y111(self):
        """
        | Waypoint   | Position                  | Direction | Rotation |
        | ---------- | ------------------------- | --------- | -------- |
        | spawn      | Waypoint((425.4, 111.6)), | 190.1     | 184      |
        | enemy1     | Waypoint((424.9, 203.0)), | 189.0     | 186      |
        | node2left  | Waypoint((426.1, 222.3)), | 193.1     | 184      |
        | node2right | Waypoint((402.8, 252.8)), | 244.9     | 253      |
        | enemy3     | Waypoint((320.2, 266.4)), | 282.6     | 274      |
        | exit_      | Waypoint((320.2, 266.4)), | 282.6     | 274      |
        | exit1      | Waypoint((312.4, 272.6)), | 272.8     | 269      |
        | exit2      | Waypoint((312.4, 260.2)), | 272.8     | 269      |
        """
        self.map_init(plane=Luofu_Cloudford, floor="F2", position=(425.4, 111.6))
        self.register_domain_exit(
            Waypoint((320.2, 266.4)), end_rotation=274,
            left_door=Waypoint((312.4, 272.6)), right_door=Waypoint((312.4, 260.2)))
        enemy1 = Waypoint((424.9, 203.0))
        node2left = Waypoint((426.1, 222.3))
        node2right = Waypoint((402.8, 252.8))
        enemy3 = Waypoint((320.2, 266.4))
        # ===== End of generated waypoints =====

        # Look right
        self.rotation_set(210)
        self.clear_enemy(enemy1)
        # Enemy2
        self.clear_enemy(
            node2left,
            node2right.straight_run(),
            enemy3.straight_run(),
        )
        # Possible enemy 3
        if self.minimap.position_diff(enemy3.position) > 50:
            self.clear_enemy(
                node2right.straight_run(),
                enemy3.straight_run(),
            )

    def Luofu_Cloudford_F2_X425Y171(self):
        """
        | Waypoint    | Position                  | Direction | Rotation |
        | ----------- | ------------------------- | --------- | -------- |
        | spawn       | Waypoint((425.5, 171.6)), | 190.1     | 184      |
        | item1       | Waypoint((436.8, 203.6)), | 166.7     | 161      |
        | item2       | Waypoint((407.1, 205.3)), | 181.3     | 177      |
        | enemy2left  | Waypoint((426.6, 252.0)), | 237.2     | 234      |
        | enemy2right | Waypoint((407.2, 253.0)), | 311.8     | 274      |
        | item3       | Waypoint((382.4, 275.3)), | 250.8     | 251      |
        | enemy3      | Waypoint((318.8, 267.0)), | 279.8     | 281      |
        | exit_       | Waypoint((324.8, 268.5)), | 283.0     | 278      |
        | exit1       | Waypoint((312.6, 276.0)), | 284.8     | 283      |
        | exit2       | Waypoint((313.2, 259.0)), | 177.5     | 271      |
        """
        self.map_init(plane=Luofu_Cloudford, floor="F2", position=(425.5, 171.6))
        self.register_domain_exit(
            Waypoint((324.8, 268.5)), end_rotation=278,
            left_door=Waypoint((312.6, 276.0)), right_door=Waypoint((313.2, 259.0)))
        item1 = Waypoint((436.8, 203.6))
        item2 = Waypoint((407.1, 205.3))
        enemy2left = Waypoint((426.6, 252.0))
        enemy2right = Waypoint((407.2, 253.0))
        item3 = Waypoint((382.4, 275.3))
        enemy3 = Waypoint((318.8, 267.0))
        # ===== End of generated waypoints =====

        # Items are randomly generated in 4 position, ignore all
        # self.clear_item(item1)
        # self.clear_item(item2)

        # Look right
        self.rotation_set(210)
        self.minimap.lock_rotation(210)
        self.clear_enemy(
            enemy2left,
            enemy2right,
        )
        # 3
        self.rotation_set(270)
        self.minimap.lock_rotation(270)
        # self.clear_item(item3.straight_run())
        self.clear_enemy(
            enemy3
        )
