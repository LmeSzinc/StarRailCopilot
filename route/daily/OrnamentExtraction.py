from module.logger import logger
from tasks.combat.combat import Combat
from tasks.map.control.waypoint import Waypoint
from tasks.map.keywords.plane import Amphoreus_StrifeRuinsCastrumKremnos
from tasks.map.route.base import RouteBase


# Ornament Extraction in 2.1
# class Route(RouteBase, Combat):
#     def route(self):
#         """
#         Pages:
#             in: Any
#             out: page_forgotten_hall
#         """
#         logger.hr('Route Ornament Extraction', level=1)
#         self.map_init(plane=Penacony_TheReverieReality, position=(245.3, 233.3))
#         boss = Waypoint((245.2, 193.6))
#         boss.expected_end = [self.is_combat_executing]
#         self.clear_enemy(
#             boss,
#             poor_try=True
#         )

class Route(RouteBase, Combat):
    def route(self):
        """
        Pages:
            in: Any
            out: page_forgotten_hall
        """
        logger.hr('Route Ornament Extraction', level=1)
        self.map_init(plane=Amphoreus_StrifeRuinsCastrumKremnos, floor='F1OE', position=(155.5, 669.3))
        boss = Waypoint((155.5, 627.5))
        boss.expected_end = [self.is_combat_executing]
        self.clear_enemy(
            boss,
            poor_try=True
        )
