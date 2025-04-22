from tasks.map.route.base import RouteBase as RouteBase_


class RouteBase(RouteBase_):
    def clear_enemy(self, *waypoints, poor_try=True):
        """
        Go along a list of position and enemy at last.
        In ornament extraction, walk ends at is_combat_executing
        and poor_try is default to True since there must be a boss there.

        Args:
            waypoints: position (x, y), a list of position to go along.
                or a list of Waypoint objects to go along.
            poor_try: True to call combat_poor_try() if didn't clear an enemy

        Returns:
            list[str]: A list of walk result
                containing 'enemy' if cleared an enemy

        Pages:
            in: page_main, in ornament extraction
            out: is_combat_executing
        """
        end_point = waypoints[-1]
        end_point.expected_end = [self.is_combat_executing]
        return super().clear_enemy(*waypoints, poor_try)
