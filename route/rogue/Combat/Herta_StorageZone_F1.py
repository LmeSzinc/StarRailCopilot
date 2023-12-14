from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Herta_StorageZone
from tasks.rogue.route.base import RouteBase


class Route(RouteBase):

    def Herta_StorageZone_F1_X225Y258(self):
        """
        | Waypoint       | Position                  | Direction | Rotation |
        | -------------- | ------------------------- | --------- | -------- |
        | spawn          | Waypoint((225.8, 258.8)), | 96.7      | 91       |
        | item1          | Waypoint((240.8, 270.0)), | 135.8     | 131      |
        | enemy1         | Waypoint((270.6, 258.8)), | 76.4      | 73       |
        | node2          | Waypoint((273.2, 269.2)), | 157.2     | 156      |
        | node3          | Waypoint((284.6, 283.0)), | 157.2     | 154      |
        | item3          | Waypoint((293.2, 288.6)), | 105.5     | 103      |
        | node4          | Waypoint((307.2, 305.2)), | 126.2     | 124      |
        | item5          | Waypoint((332.8, 304.8)), | 96.8      | 96       |
        | node5          | Waypoint((336.2, 312.0)), | 102.9     | 98       |
        | enemy5         | Waypoint((392.5, 312.4)), | 4.1       | 91       |
        | exit_          | Waypoint((392.5, 312.4)), | 4.1       | 91       |
        | exit1_X400Y318 | Waypoint((411.2, 301.8)), | 101.1     | 91       |
        | exit2_X400Y318 | Waypoint((400.8, 318.9)), | 101.1     | 91       |
        """
        self.map_init(plane=Herta_StorageZone, floor="F1", position=(225.8, 258.8))
        self.register_domain_exit(
            Waypoint((392.5, 312.4)), end_rotation=91,
            left_door=Waypoint((411.2, 301.8)), right_door=Waypoint((400.8, 318.9)))
        item1 = Waypoint((240.8, 270.0))
        enemy1 = Waypoint((270.6, 258.8))
        node2 = Waypoint((273.2, 269.2))
        node3 = Waypoint((284.6, 283.0))
        item3 = Waypoint((293.2, 288.6))
        node4 = Waypoint((307.2, 305.2))
        item5 = Waypoint((332.8, 304.8))
        node5 = Waypoint((336.2, 312.0))
        enemy5 = Waypoint((392.5, 312.4))
        # ===== End of generated waypoints =====

        self.register_domain_exit(
            Waypoint((392.5, 312.4)), end_rotation=91,
            left_door=Waypoint((406.2, 307.8)), right_door=Waypoint((406.8, 318.9)))
        # 1
        self.clear_item(item1.straight_run())
        self.clear_enemy(enemy1.straight_run())
        # 2
        self.rotation_set(135)
        self.clear_enemy(
            enemy1,
            node2.set_threshold(3),
            node3,
            node4,
        )
        # 5
        self.clear_enemy(
            node5.straight_run(),
            enemy5.straight_run(),
        )

    def Herta_StorageZone_F1_X257Y85(self):
        """
        | Waypoint | Position                 | Direction | Rotation |
        | -------- | ------------------------ | --------- | -------- |
        | spawn    | Waypoint((257.3, 85.5)), | 308.0     | 304      |
        | item     | Waypoint((244.2, 66.3)), | 334.7     | 331      |
        | door     | Waypoint((215.4, 65.1)), | 303.8     | 301      |
        | enemy    | Waypoint((202.7, 57.9)), | 297.8     | 294      |
        | exit_    | Waypoint((202.4, 58.1)), | 302.9     | 301      |
        | exit1    | Waypoint((195.0, 61.2)), | 306.4     | 304      |
        | exit2    | Waypoint((199.4, 49.4)), | 306.4     | 304      |
        """
        self.map_init(plane=Herta_StorageZone, floor="F1", position=(257.3, 85.5))
        self.register_domain_exit(
            Waypoint((202.4, 58.1)), end_rotation=301,
            left_door=Waypoint((195.0, 61.2)), right_door=Waypoint((199.4, 49.4)))
        item = Waypoint((244.2, 66.3))
        door = Waypoint((215.4, 65.1))
        enemy = Waypoint((202.7, 57.9))
        # ===== End of generated waypoints =====

        self.clear_item(item)
        self.clear_enemy(door, enemy)

    def Herta_StorageZone_F1_X273Y92(self):
        """
        | Waypoint | Position                 | Direction | Rotation |
        | -------- | ------------------------ | --------- | -------- |
        | spawn    | Waypoint((273.4, 92.2)), | 308.0     | 304      |
        | item     | Waypoint((248.4, 59.4)), | 334.8     | 331      |
        | enemy    | Waypoint((227.8, 69.5)), | 30.2      | 299      |
        | exit_    | Waypoint((227.8, 69.5)), | 30.2      | 299      |
        | exit1    | Waypoint((216.0, 74.4)), | 302.9     | 304      |
        | exit2    | Waypoint((224.9, 59.4)), | 306.3     | 306      |
        """
        self.map_init(plane=Herta_StorageZone, floor="F1", position=(273.4, 92.2))
        self.register_domain_exit(
            Waypoint((227.8, 69.5)), end_rotation=299,
            left_door=Waypoint((216.0, 74.4)), right_door=Waypoint((224.9, 59.4)))
        item = Waypoint((248.4, 59.4))
        enemy = Waypoint((227.8, 69.5))
        # ===== End of generated waypoints =====

        # Ignore item, bad way
        self.clear_enemy(enemy)

    def Herta_StorageZone_F1_X692Y61(self):
        """
        | Waypoint | Position                  | Direction | Rotation |
        | -------- | ------------------------- | --------- | -------- |
        | spawn    | Waypoint((692.0, 62.0)),  | 263.8     | 260      |
        | item1    | Waypoint((676.1, 98.5)),  | 222.6     | 218      |
        | enemy2   | Waypoint((649.3, 68.7)),  | 354.1     | 350      |
        | enemy1   | Waypoint((654.7, 84.5)),  | 282.9     | 288      |
        | item2    | Waypoint((642.2, 66.1)),  | 290.2     | 285      |
        | door     | Waypoint((636.8, 81.9)),  | 263.8     | 262      |
        | node     | Waypoint((599.2, 91.0)),  | 256.7     | 255      |
        | item3    | Waypoint((588.6, 102.2)), | 245.0     | 246      |
        | enemy3   | Waypoint((598.3, 129.1)), | 181.3     | 174      |
        | exit_    | Waypoint((598.3, 129.1)), | 181.3     | 174      |
        | exit1    | Waypoint((605.4, 137.2)), | 185.7     | 179      |
        | exit2    | Waypoint((591.5, 137.0)), | 185.8     | 179      |
        """
        self.map_init(plane=Herta_StorageZone, floor="F1", position=(692.0, 62.0))
        self.register_domain_exit(
            Waypoint((598.3, 129.1)), end_rotation=174,
            left_door=Waypoint((605.4, 137.2)), right_door=Waypoint((591.5, 137.0)))
        item1 = Waypoint((676.1, 98.5))
        enemy2 = Waypoint((649.3, 68.7))
        enemy1 = Waypoint((654.7, 84.5))
        item2 = Waypoint((642.2, 66.1))
        door = Waypoint((636.8, 81.9))
        node = Waypoint((599.2, 91.0))
        item3 = Waypoint((588.6, 102.2))
        enemy3 = Waypoint((598.3, 129.1))
        # ===== End of generated waypoints =====

        # item1
        self.clear_item(
            item1.straight_run(),
        )
        # enemy12
        self.clear_enemy(
            enemy1.straight_run(),
            enemy2.straight_run().set_threshold(9),
        )
        self.clear_item(item2)
        # 3
        self.rotation_set(255)
        self.clear_item(
            door.set_threshold(2),
            node,
            item3,
        )
        self.clear_enemy(
            enemy3.straight_run(),
        )

    def Herta_StorageZone_F1_X749Y45(self):
        """
        | Waypoint    | Position                  | Direction | Rotation |
        | ----------- | ------------------------- | --------- | -------- |
        | spawn       | Waypoint((749.5, 45.6)),  | 263.8     | 260      |
        | item1       | Waypoint((728.9, 48.8)),  | 263.8     | 264      |
        | enemy1      | Waypoint((686.2, 64.4)),  | 256.8     | 260      |
        | item2       | Waypoint((674.0, 99.1)),  | 212.9     | 204      |
        | enemy2right | Waypoint((649.5, 65.6)),  | 302.7     | 71       |
        | enemy2left  | Waypoint((653.4, 85.0)),  | 326.7     | 103      |
        | node2       | Waypoint((636.8, 81.9)),  | 263.8     | 262      |
        | node3       | Waypoint((598.6, 93.9)),  | 256.7     | 253      |
        | item3       | Waypoint((588.6, 102.2)), | 245.0     | 246      |
        | enemy3      | Waypoint((597.2, 131.0)), | 282.9     | 179      |
        | exit_       | Waypoint((597.2, 131.0)), | 282.9     | 179      |
        | exit1       | Waypoint((604.3, 133.1)), | 179.5     | 193      |
        | exit2       | Waypoint((590.2, 137.0)), | 185.7     | 177      |
        """
        self.map_init(plane=Herta_StorageZone, floor="F1", position=(749.5, 45.6))
        self.register_domain_exit(
            Waypoint((597.2, 131.0)), end_rotation=179,
            left_door=Waypoint((604.3, 133.1)), right_door=Waypoint((590.2, 137.0)))
        item1 = Waypoint((728.9, 48.8))
        enemy1 = Waypoint((686.2, 64.4))
        item2 = Waypoint((674.0, 99.1))
        enemy2right = Waypoint((649.5, 65.6))
        enemy2left = Waypoint((653.4, 85.0))
        node2 = Waypoint((636.8, 81.9))
        node3 = Waypoint((598.6, 93.9))
        item3 = Waypoint((588.6, 102.2))
        enemy3 = Waypoint((597.2, 131.0))
        # ===== End of generated waypoints =====

        # 1
        self.clear_item(item1)
        self.clear_enemy(
            enemy1.set_threshold(5)
        )
        # 2
        self.clear_item(
            item2.straight_run().set_threshold(5),
        )
        self.clear_enemy(
            enemy2left.straight_run(),
            enemy2right.straight_run().set_threshold(9),
        )
        # 3
        self.clear_item(
            node2.straight_run().set_threshold(5),
            node3.straight_run(),
            item3,
        )
        self.clear_enemy(enemy3.straight_run())
