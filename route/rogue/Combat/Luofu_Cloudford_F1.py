from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Luofu_Cloudford
from tasks.map.route.base import locked_position, locked_rotation
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Luofu_Cloudford_F1_X241Y947(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((240.4, 947.6)), | 274.2     | 274      |
        | node     | Waypoint((218.8, 948.8)), | 282.9     | 278      |
        | item     | Waypoint((222.4, 934.6)), | 311.8     | 306      |
        | enemy    | Waypoint((197.2, 947.4)), | 282.6     | 260      |
        | exit_    | Waypoint((193.1, 947.2)), | 12.8      | 274      |
        | exit1    | Waypoint((183.6, 957.4)), | 275.8     | 267      |
        | exit2    | Waypoint((183.4, 939.2)), | 284.6     | 258      |
        """
        self.map_init(plane=Luofu_Cloudford, floor="F1", position=(240.4, 947.6))
        self.register_domain_exit(
            Waypoint((193.1, 947.2)), end_rotation=274,
            left_door=Waypoint((183.6, 957.4)), right_door=Waypoint((183.4, 939.2)))
        node = Waypoint((218.8, 948.8))
        item = Waypoint((222.4, 934.6))
        enemy = Waypoint((197.2, 947.4))
        # ===== End of generated waypoints =====

        self.minimap.lock_rotation(270)
        # ignore item
        # self.clear_item(item)
        self.clear_enemy(
            enemy,
        )

    def Luofu_Cloudford_F1_X257Y947(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((257.3, 951.2)), | 274.2     | 274      |
        | item     | Waypoint((236.8, 934.2)), | 302.7     | 299      |
        | node     | Waypoint((221.6, 946.2)), | 272.8     | 269      |
        | enemy    | Waypoint((193.7, 949.5)), | 143.8     | 269      |
        | exit_    | Waypoint((194.4, 947.2)), | 4.2       | 274      |
        """
        self.map_init(plane=Luofu_Cloudford, floor="F1", position=(257.3, 947))
        self.register_domain_exit(
            Waypoint((194.4, 947.2)), end_rotation=274,
            left_door=Waypoint((183.9, 954.4)), right_door=Waypoint((183.0, 942.4)))
        item = Waypoint((236.8, 934.2))
        node = Waypoint((221.6, 946.2))
        enemy = Waypoint((193.7, 949.5))
        # ===== End of generated waypoints =====

        """
        Notes
        Luofu_Cloudford_F1_X257Y947 is the same as Luofu_Cloudford_F1_X257Y951
        but for wrong spawn point detected
        """

        self.minimap.lock_rotation(270)
        self.clear_item(item)
        self.clear_enemy(
            node,
            enemy
        )

    def Luofu_Cloudford_F1_X257Y951(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((257.3, 951.2)), | 274.2     | 274      |
        | item     | Waypoint((236.8, 934.2)), | 302.7     | 299      |
        | node     | Waypoint((221.6, 946.2)), | 272.8     | 269      |
        | enemy    | Waypoint((193.7, 949.5)), | 143.8     | 269      |
        | exit_    | Waypoint((194.4, 947.2)), | 4.2       | 274      |
        | exit1    | Waypoint((183.9, 954.4)), | 261.9     | 262      |
        | exit2    | Waypoint((183.0, 942.4)), | 290.2     | 283      |
        """
        self.map_init(plane=Luofu_Cloudford, floor="F1", position=(257.3, 951.2))
        self.register_domain_exit(
            Waypoint((194.4, 947.2)), end_rotation=274,
            left_door=Waypoint((183.9, 954.4)), right_door=Waypoint((183.0, 942.4)))
        item = Waypoint((236.8, 934.2))
        node = Waypoint((221.6, 946.2))
        enemy = Waypoint((193.7, 949.5))
        # ===== End of generated waypoints =====

        self.minimap.lock_rotation(270)
        self.clear_item(item)
        self.clear_enemy(
            node,
            enemy
        )

    @locked_position
    @locked_rotation(0)
    def Luofu_Cloudford_F1_X281Y873(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((283.4, 865.3)), | 6.7       | 4        |
        | item     | Waypoint((297.0, 841.4)), | 36.1      | 31       |
        | enemy    | Waypoint((282.4, 814.2)), | 8.1       | 1        |
        | exit_    | Waypoint((284.5, 816.8)), | 5.7       | 1        |
        | exit1    | Waypoint((276.2, 807.8)), | 4.4       | 4        |
        | exit2    | Waypoint((290.4, 810.2)), | 4.3       | 4        |
        """
        self.map_init(plane=Luofu_Cloudford, floor="F1", position=(281, 873))
        self.register_domain_exit(
            Waypoint((284.5, 816.8)), end_rotation=1,
            left_door=Waypoint((276.2, 807.8)), right_door=Waypoint((290.4, 810.2)))
        item = Waypoint((297.0, 841.4))
        enemy = Waypoint((282.4, 814.2))
        # ===== End of generated waypoints =====

        """
        Notes
        Luofu_Cloudford_F1_X281Y873 is the same as Luofu_Cloudford_F1_X283Y865
        but for wrong spawn point detected
        """
        self.clear_enemy(enemy)

    @locked_position
    @locked_rotation(0)
    def Luofu_Cloudford_F1_X283Y865(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((283.4, 865.3)), | 6.7       | 4        |
        | item     | Waypoint((297.0, 841.4)), | 36.1      | 31       |
        | enemy    | Waypoint((282.4, 814.2)), | 8.1       | 1        |
        | exit_    | Waypoint((284.5, 816.8)), | 5.7       | 1        |
        | exit1    | Waypoint((276.2, 807.8)), | 4.4       | 4        |
        | exit2    | Waypoint((290.4, 810.2)), | 4.3       | 4        |
        """
        self.map_init(plane=Luofu_Cloudford, floor="F1", position=(283.4, 865.3))
        self.register_domain_exit(
            Waypoint((284.5, 816.8)), end_rotation=1,
            left_door=Waypoint((276.2, 807.8)), right_door=Waypoint((290.4, 810.2)))
        item = Waypoint((297.0, 841.4))
        enemy = Waypoint((282.4, 814.2))
        # ===== End of generated waypoints =====

        # Ignore random item
        # self.clear_item(item)
        self.clear_enemy(enemy)

    def Luofu_Cloudford_F1_X431Y593(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((431.5, 593.4)), | 2.7       | 357      |
        | item1    | Waypoint((371.8, 592.8)), | 263.8     | 267      |
        | enemy1   | Waypoint((341.2, 586.8)), | 274.2     | 274      |
        | item2    | Waypoint((310.4, 582.2)), | 289.0     | 288      |
        | enemy2   | Waypoint((273.9, 584.9)), | 274.1     | 271      |
        | exit_    | Waypoint((273.9, 584.9)), | 274.1     | 271      |
        """
        self.map_init(plane=Luofu_Cloudford, floor="F1", position=(431.5, 593.4))
        self.register_domain_exit(Waypoint((273.9, 584.9)), end_rotation=271)
        item1 = Waypoint((371.8, 592.8))
        enemy1 = Waypoint((341.2, 586.8))
        item2 = Waypoint((310.4, 582.2))
        enemy2 = Waypoint((273.9, 584.9))
        # ===== End of generated waypoints =====

        # 1
        self.clear_item(
            item1.straight_run(),
        )
        self.clear_enemy(
            enemy1.straight_run(),
        )
        # 2
        self.clear_item(item2)
        self.clear_enemy(enemy2)

    def Luofu_Cloudford_F1_X435Y669(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((435.4, 669.2)), | 6.7       | 4        |
        | item1    | Waypoint((432.2, 628.3)), | 2.7       | 357      |
        | enemy1   | Waypoint((428.6, 598.8)), | 8.0       | 177      |
        | node2    | Waypoint((421.2, 590.8)), | 44.2      | 285      |
        | node3    | Waypoint((366.6, 588.2)), | 274.2     | 274      |
        | enemy3   | Waypoint((344.9, 590.4)), | 191.8     | 357      |
        | item4    | Waypoint((309.6, 580.2)), | 290.1     | 281      |
        | enemy4   | Waypoint((271.3, 585.5)), | 285.0     | 274      |
        | exit_    | Waypoint((271.3, 585.5)), | 285.0     | 274      |
        | exit1    | Waypoint((267.9, 592.3)), | 275.9     | 274      |
        | exit2    | Waypoint((267.8, 580.0)), | 275.8     | 274      |
        """
        self.map_init(plane=Luofu_Cloudford, floor="F1", position=(435.4, 669.2))
        self.register_domain_exit(
            Waypoint((271.3, 585.5)), end_rotation=274,
            left_door=Waypoint((267.9, 592.3)), right_door=Waypoint((267.8, 580.0)))
        item1 = Waypoint((432.2, 628.3))
        enemy1 = Waypoint((428.6, 598.8))
        node2 = Waypoint((421.2, 590.8))
        node3 = Waypoint((366.6, 588.2))
        enemy3 = Waypoint((344.9, 590.4))
        item4 = Waypoint((309.6, 580.2))
        enemy4 = Waypoint((271.3, 585.5))
        # ===== End of generated waypoints =====

        self.clear_item(item1)
        self.clear_enemy(enemy1)
        # Go through bridges
        self.rotation_set(270)
        self.minimap.lock_rotation(270)
        self.clear_enemy(
            node2.set_threshold(3),
            node3.set_threshold(3),
            enemy3,
        )
        self.clear_item(item4)
        self.clear_enemy(enemy4)
