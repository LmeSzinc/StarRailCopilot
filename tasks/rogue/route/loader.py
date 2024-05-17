from typing import Optional

import numpy as np

from module.base.decorator import cached_property
from module.base.timer import Timer
from module.logger import logger
from tasks.character.switch import CharacterSwitch
from tasks.map.keywords import MapPlane
from tasks.map.keywords.plane import (
    Herta_MasterControlZone,
    Herta_ParlorCar,
    Jarilo_AdministrativeDistrict,
    Luofu_AurumAlley,
    Luofu_ExaltingSanctum
)
from tasks.map.minimap.minimap import Minimap
from tasks.map.resource.resource import SPECIAL_PLANES
from tasks.map.route.loader import RouteLoader as RouteLoader_
from tasks.rogue.blessing.ui import RogueUI
from tasks.rogue.route.base import RouteBase
from tasks.rogue.route.model import RogueRouteListModel, RogueRouteModel


def model_from_json(model, file: str):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    data = model.model_validate_json(content)
    return data


class MinimapWrapper:
    @cached_property
    def all_minimap(self) -> dict[str, Minimap]:
        """
        Returns:
            dict: Key: {world}_{plane}_{floor}, e.g. Jarilo_SilvermaneGuardRestrictedZone_F1
                Value: Minimap object
        """
        # No enemy spawn at the followings
        blacklist = [
            Herta_ParlorCar,
            Herta_MasterControlZone,
            Jarilo_AdministrativeDistrict,
            Luofu_ExaltingSanctum,
            Luofu_AurumAlley,
        ]
        maps = {}

        for plane, floor in SPECIAL_PLANES:
            minimap = Minimap()
            minimap.set_plane(plane=plane, floor=floor)
            maps[f'{plane}_{floor}'] = minimap

        for plane in MapPlane.instances.values():
            if plane in blacklist:
                continue
            if not plane.world:
                continue
            for floor in plane.floors:
                minimap = Minimap()
                minimap.set_plane(plane=plane, floor=floor)
                maps[f'{plane.name}_{floor}'] = minimap

        logger.attr('MinimapLoaded', len(maps))
        return maps

    @cached_property
    def all_route(self) -> list[RogueRouteModel]:
        routes = model_from_json(RogueRouteListModel, './route/rogue/route.json').root
        logger.attr('RouteLoaded', len(routes))
        return routes

    def get_minimap(self, route: RogueRouteModel):
        return self.all_minimap[route.plane_floor]


class RouteLoader(RogueUI, MinimapWrapper, RouteLoader_, CharacterSwitch):
    def position_find_known(self, image, force_return=False) -> Optional[RogueRouteModel]:
        """
        Try to find from known route spawn point
        """
        logger.info('position_find_known')
        plane = self.update_plane()
        if plane is None:
            logger.warning('Unknown rogue domain')
            return

        visited = []
        for route in self.all_route:
            if plane.rogue_domain and plane.rogue_domain != route.domain:
                if plane.is_rogue_occurrence and route.is_DomainOccurrence:
                    # Treat as "Occurrence"
                    pass
                elif plane.is_rogue_elite and route.is_DomainElite:
                    # Treat as "Elite"
                    pass
                else:
                    continue
            minimap = self.get_minimap(route)
            minimap.init_position(route.position, show_log=False)
            try:
                minimap.update_position(image)
            except FileNotFoundError as e:
                logger.warning(e)
                continue
            visited.append((route, minimap.position_similarity, minimap.position))

        if len(visited) < 3:
            logger.warning('Too few routes to search from, not enough to make a prediction')
            return

        visited = sorted(visited, key=lambda x: x[1], reverse=True)
        logger.info(f'Best 3 predictions: {[(r.name, s, p) for r, s, p in visited[:3]]}')
        nearby = [
            (r, s, p) for r, s, p in visited if np.linalg.norm(np.subtract(r.position, p)) < 5
        ]
        logger.info(f'Best 3 nearby predictions: {[(r.name, s, p) for r, s, p in nearby[:3]]}')
        # Check special
        for r, s, p in nearby:
            if self._position_match_special(r, s, p):
                logger.info(f'Route match special: {r.name}')
                return r
        # Check nearby
        if len(nearby) == 1:
            if nearby[0][1] > 0.05:
                logger.attr('RoutePredict', nearby[0][0].name)
                return nearby[0][0]
        elif len(nearby) >= 2:
            if nearby[0][1] / nearby[1][1] > 0.55:
                logger.attr('RoutePredict', nearby[0][0].name)
                return nearby[0][0]

        # logger.info(f'Best 3 prediction: {[(r.name, s, p) for r, s, p in visited[:3]]}')
        # if visited[0][1] / visited[1][1] > 0.75:
        #     logger.attr('RoutePredict', visited[0][0].name)
        #     return visited[0][0]

        if force_return:
            if len(nearby) >= 1:
                route = nearby[0][0]
            else:
                route = visited[0][0]
            logger.attr('RoutePredict', route.name)
            return route
        else:
            logger.warning('Similarity too close, not enough to make a prediction')
            return None

    def _position_match_special(
            self,
            route: RogueRouteModel,
            similarity: float,
            position: tuple[float, float]
    ) -> bool:
        # 2023-11-13 23:50:00.470 | INFO | Best 3 predictions: [
        # ('Occurrence_Luofu_Cloudford_F1_X241Y947', 0.119, (272.6, 948.5)),
        # ('Occurrence_Jarilo_GreatMine_F1_X277Y605', 0.107, (264.4, 645.0)),
        # ('Occurrence_Luofu_ArtisanshipCommission_F1_X521Y63', 0.106, (569.8, 34.8))]
        # 2023-11-13 23:50:00.472 | INFO | Best 3 nearby predictions: [
        # ('Occurrence_Herta_SupplyZone_F2Rogue_X397Y223', 0.102, (393.2, 222.8)),
        # ('Occurrence_Herta_StorageZone_F2_X365Y167', 0.094, (363.0, 166.8)),
        # ('Occurrence_Herta_StorageZone_F2_X363Y166', 0.094, (363.0, 166.8))]
        # if route.name == 'Occurrence_Herta_StorageZone_F2_X363Y166' and similarity > 0.05:
        #     return True

        # Before Combat_Herta_SupplyZone_F2_X45Y369
        if route.name in [
            'Combat_Herta_SupplyZone_F2_X543Y255',  # 0.462, (543.3, 255.4)
            'Combat_Luofu_DivinationCommission_F1_X737Y237',
            # ('Occurrence_Luofu_Cloudford_F1_X241Y947', 0.307, (236.5, 949.6)),
            # ('Occurrence_Luofu_Cloudford_F1_X244Y951', 0.307, (236.5, 949.6)),
            # ('Occurrence_Jarilo_SilvermaneGuardRestrictedZone_F1_X509Y541', 0.154, (507.8, 515.2))
            'Occurrence_Luofu_Cloudford_F1_X241Y947',
            'Occurrence_Luofu_Cloudford_F1_X244Y951',
        ] and similarity > 0.25:
            return True
        # Before Combat_Luofu_Cloudford_F1_X281Y873
        if route.name in [
            # ('Combat_Jarilo_BackwaterPass_F1_X507Y733', 0.26, (503.2, 736.9)),
            # ('Combat_Herta_SupplyZone_F2_X45Y369', 0.168, (46.5, 370.0))
            'Jarilo_BackwaterPass_F1_X507Y733',
            'Jarilo_BackwaterPass_F1_X555Y643',
            'Occurrence_Jarilo_BackwaterPass_F1_X553Y643',
            'Combat_Jarilo_GreatMine_F1_X545Y513',
            'Combat_Herta_SupplyZone_F2_X45Y369',
        ] and similarity > 0.20:
            return True
        # Before Occurrence_Luofu_DivinationCommission_F2_X425Y791
        if route.name in [
            'Occurrence_Jarilo_RivetTown_F1_X157Y435',
            # ('Occurrence_Luofu_DivinationCommission_F2_X149Y659', 0.237, (148.9, 658.8)),
            # ('Occurrence_Luofu_DivinationCommission_F2_X425Y791', 0.11, (425.2, 793.8))
            'Occurrence_Luofu_DivinationCommission_F2_X149Y659',
            # ('Combat_Luofu_DivinationCommission_F1_X97Y457', 0.222, (97.8, 456.9)),
            # ('Combat_Luofu_ScalegorgeWaterscape_F1_X415Y261', 0.112, (371.8, 289.4)),
            # ('Combat_Herta_SupplyZone_F2_X45Y369', 0.104, (11.7, 367.6))
            'Combat_Luofu_DivinationCommission_F1_X97Y457',
            # ('Occurrence_Jarilo_BackwaterPass_F1_X613Y755', 0.206, (611.3, 759.0)),
            # ('Occurrence_Jarilo_BackwaterPass_F1_X611Y761', 0.206, (611.3, 759.0)),
            # ('Occurrence_Luofu_DivinationCommission_F2_X425Y791', 0.105, (429.7, 791.6))
            'Occurrence_Jarilo_BackwaterPass_F1_X613Y755',
            'Occurrence_Jarilo_BackwaterPass_F1_X611Y761',
        ] and similarity > 0.15:
            return True
        if route.name in [
            'Combat_Herta_StorageZone_F1_X273Y92',
            'Occurrence_Herta_StorageZone_F1_X273Y93',
            'Occurrence_Jarilo_RivetTown_F1_X289Y97',
            'Occurrence_Luofu_DivinationCommission_F2_X425Y791',
            'Occurrence_Luofu_ArtisanshipCommission_F1_X169Y491',
        ] and similarity > 0.1:
            return True
        # Luofu_Cloudford_F1_X283Y865 and its equivalents
        # INFO     21:27:00.816 │ Best 3 nearby predictions: [
        # ('Combat_Herta_SupplyZone_F2_X45Y369', 0.184, (41.0, 369.1)),
        # ('Combat_Luofu_Cloudford_F1_X281Y873', 0.149, (281.8, 869.6)),
        # ('Combat_Luofu_Cloudford_F1_X283Y865', 0.149, (281.8, 869.6))]
        # INFO | Best 3 predictions: [('Combat_Herta_SupplyZone_F2_X45Y369', 0.149, (43.4, 369.3)),
        # ('Combat_Luofu_Cloudford_F1_X241Y947', 0.138, (198.6, 956.8)),
        # ('Combat_Luofu_Cloudford_F1Rogue_X59Y405', 0.134, (81.0, 397.4))]
        if route.name in [
            'Combat_Luofu_Cloudford_F1_X283Y865',
            'Occurrence_Luofu_Cloudford_F1_X283Y865',
            'Combat_Luofu_Cloudford_F1_X281Y873',
            'Occurrence_Luofu_Cloudford_F1_X281Y873',
        ] and similarity > 0.05:
            return True
        return False

    def position_find_bruteforce(self, image) -> Minimap:
        """
        Fallback method to find from all planes and floors
        """
        logger.warning('position_find_bruteforce, this may take a while')
        for name, minimap in self.all_minimap.items():
            if minimap.is_special_plane:
                continue

            minimap.init_position((0, 0), show_log=False)
            try:
                minimap.update_position(image)
            except FileNotFoundError:
                pass

        def get_name(minimap_: Minimap) -> str:
            return f'{minimap_.plane.name}_{minimap_.floor}_X{int(minimap_.position[0])}Y{int(minimap_.position[1])}'

        visited = sorted(self.all_minimap.values(), key=lambda x: x.position_similarity, reverse=True)
        logger.info(f'Best 5 prediction: {[(get_name(m), m.position_similarity) for m in visited[:50]]}')
        if visited[1].position_similarity / visited[0].position_similarity > 0.75:
            logger.warning('Similarity too close, predictions may go wrong')

        logger.attr('RoutePredict', get_name(visited[0]))
        return visited[0]

    def position_find(self, skip_first_screenshot=True):
        timeout = Timer(1, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                self.position_find_bruteforce(self.device.image)
                logger.warning('Find position timeout, force return route')
                return self.position_find_known(self.device.screenshot(), force_return=True)

            route = self.position_find_known(self.device.image)
            if route is not None:
                return route

    def route_run(self, route=None):
        """
        Run a rogue domain

        Returns:
            bool: True if success, False if route unknown

        Pages:
            in: page_main
            out: page_main, at another domain
                or page_rogue if rogue cleared
        """
        # To have a newer image, since previous loadings took some time
        route = self.position_find(skip_first_screenshot=False)
        self.screenshot_tracking_add()
        super().route_run(route)

    def rogue_run(self, skip_first_screenshot=True):
        """
        Do a complete rogue run, no error handle yet.

        Pages:
            in: page_rogue, is_page_rogue_launch()
            out: page_rogue, is_page_rogue_main()
        """
        base = RouteBase(config=self.config, device=self.device, task=self.config.task.command)
        count = 1
        self.character_is_ranged = None
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            logger.hr(f'Route run: {count}', level=1)
            base.clear_blessing()
            self.character_switch_to_ranged(update=True)

            self.route_run()
            # if not success:
            #     self.device.image_save()
            #     continue

            # End
            if self.is_page_rogue_main():
                break

            count += 1


if __name__ == '__main__':
    self = RouteLoader('src', task='Rogue')
    # self.image_file = r''
    self.device.screenshot()
    self.position_find()
    self.position_find_bruteforce(self.device.image)

    # self.device.screenshot()
    # self.rogue_run()
