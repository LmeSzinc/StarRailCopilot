import re

import numpy as np

from module.base.timer import Timer
from module.base.utils import Points, area_center
from module.logger import logger
from tasks.base.assets.assets_base_main_page import OCR_MAP_NAME
from tasks.base.main_page import OcrPlaneName
from tasks.base.page import page_rogue
from tasks.combat.interact import CombatInteract
from tasks.map.keywords import KEYWORDS_MAP_PLANE, MapPlane
from tasks.rogue.assets.assets_rogue_exit import OCR_DOMAIN_EXIT
from tasks.rogue.assets.assets_rogue_ui import BLESSING_CONFIRM
from tasks.rogue.assets.assets_rogue_weekly import ROGUE_REPORT


class OcrDomainExit(OcrPlaneName):
    merge_thres_x = 50

    def _match_result(
            self,
            result: str,
            keyword_classes,
            lang: str = None,
            ignore_punctuation=True,
            ignore_digit=True):
        matched = super()._match_result(result, keyword_classes, lang, ignore_punctuation, ignore_digit)

        # Name may be covered by minimap, "Domain - " is missing,
        # check keywords like "Combat"
        if matched is None:
            for domain in MapPlane.instances.values():
                domain: MapPlane = domain
                if not domain.rogue_domain:
                    continue

                name = domain._keywords_to_find(ignore_punctuation=False)[0]
                try:
                    name = re.split('[ \-—]', name)[-1]
                except IndexError:
                    pass
                if name in result:
                    return domain

        return matched


class RogueExit(CombatInteract):
    def domain_exit_interact(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_main, DUNGEON_COMBAT_INTERACT
            out: page_main
                or page_rogue if rogue cleared
        """
        logger.info(f'Domain exit interact')
        clicked = False
        confirm = Timer(1.5, count=5)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if clicked and not self.is_in_main():
                break

            if self.handle_combat_interact():
                clicked = True
                continue
            if self.handle_popup_confirm():
                confirm.reset()
                continue

        logger.info(f'Interact loading')
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_in_main():
                if confirm.reached():
                    logger.info('Entered another domain')
                    break
            if self.ui_page_appear(page_rogue):
                logger.info('Rogue cleared')
                break

            if self.appear(ROGUE_REPORT, interval=2):
                self.device.click(BLESSING_CONFIRM)
                continue
            if self.handle_popup_confirm():
                confirm.reset()
                continue

    @staticmethod
    def screen2direction(point):
        """
        Args:
            point: Coordinate on screenshot

        Returns:
            float: Direction to move, -180~180
        """
        screen_middle = (640.0, 360.0)
        vanish_point = np.array((640.0, 247.34))
        distant_point = np.array((1509.46, 247.34))
        name_y = 77.60
        foot_y = 621.82
        if point[1] < 80:
            logger.warning(f'screen2direction: Point {point} to high')
            point = (point[0], 80)

        door_projection_bottom = (
            Points([point]).link(vanish_point).get_x(name_y)[0],
            foot_y,
        )
        door_bottom = (
            point[0],
            Points([door_projection_bottom]).link(vanish_point).get_y(point[0])[0],
        )
        door_distant = (
            Points([door_bottom]).link(distant_point).get_x(foot_y)[0],
            foot_y,
        )
        planar_door = (
            door_projection_bottom[0] - screen_middle[0],
            door_projection_bottom[0] - door_distant[0],
        )
        if planar_door[1] < 0:
            logger.warning('screen2direction: planer_door at back')
        if abs(planar_door[0]) < 5:
            direction = 0
        else:
            direction = np.rad2deg(np.arctan(planar_door[0] / planar_door[1]))

        planar_door = (round(planar_door[0], 1), round(planar_door[1], 1))
        direction = round(direction, 1)
        logger.info(f'PlanarDoor: {planar_door}, direction: {direction}')
        return direction

    def predict_door_by_name_old(self, image) -> float | None:
        # Paint current name black
        x1, y1, x2, y2 = OCR_MAP_NAME.area
        image[y1:y2, x1:x2] = (0, 0, 0)

        ocr = OcrDomainExit(OCR_DOMAIN_EXIT)
        results = ocr.matched_ocr(image, keyword_classes=MapPlane)
        centers = [area_center(result.area) for result in results]
        logger.info(f'DomainDoor: {centers}')
        directions = [self.screen2direction(center) for center in centers]

        count = len(centers)
        if count == 0:
            logger.warning('No domain exit found')
            return None
        if count == 1:
            logger.info(f'Goto next domain: {results[0]}')
            return directions[0]

        # Doors >= 2
        for expect in [
            KEYWORDS_MAP_PLANE.Rogue_DomainBoss,
            KEYWORDS_MAP_PLANE.Rogue_DomainElite,
            KEYWORDS_MAP_PLANE.Rogue_DomainRespite,
        ]:
            for domain, direction in zip(results, directions):
                if domain == expect:
                    logger.warning('Found multiple doors but has unique domain in it')
                    logger.info(f'Goto next domain: {domain}')
                    return direction

        logger.attr('DomainStrategy', self.config.RogueWorld_DomainStrategy)
        if self.config.RogueWorld_DomainStrategy == 'occurrence':
            for expect in [
                KEYWORDS_MAP_PLANE.Rogue_DomainTransaction,
                KEYWORDS_MAP_PLANE.Rogue_DomainOccurrence,
                KEYWORDS_MAP_PLANE.Rogue_DomainEncounter,
                KEYWORDS_MAP_PLANE.Rogue_DomainCombat,
            ]:
                for domain, direction in zip(results, directions):
                    if domain == expect:
                        logger.info(f'Goto next domain: {domain}')
                        return direction
        elif self.config.RogueWorld_DomainStrategy == 'combat':
            for expect in [
                KEYWORDS_MAP_PLANE.Rogue_DomainCombat,
                KEYWORDS_MAP_PLANE.Rogue_DomainEncounter,
                KEYWORDS_MAP_PLANE.Rogue_DomainOccurrence,
                KEYWORDS_MAP_PLANE.Rogue_DomainTransaction,
            ]:
                for domain, direction in zip(results, directions):
                    if domain == expect:
                        logger.info(f'Goto next domain: {domain}')
                        return direction
        else:
            logger.error(f'Unknown domain strategy: {self.config.RogueWorld_DomainStrategy}')

        logger.error('No domain was selected, return the first instead')
        logger.info(f'Goto next domain: {results[0]}')
        return directions[0]

    def predict_door_old(self, skip_first_screenshot=True) -> float | None:
        timeout = Timer(3, count=6).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.error('Predict door timeout')
                return None

            direction = self.predict_door_by_name_old(self.device.image)
            if direction is not None:
                return direction

    def predict_door_by_name(self, image) -> tuple[MapPlane | None, MapPlane | None]:
        """
        Args:
            image:

        Returns:
            left_door, right_door:
        """
        # Paint current name black
        x1, y1, x2, y2 = OCR_MAP_NAME.area
        image[y1:y2, x1:x2] = (0, 0, 0)

        ocr = OcrDomainExit(OCR_DOMAIN_EXIT)
        results = ocr.matched_ocr(image, keyword_classes=MapPlane)
        # Try without preprocess
        if not len(results):
            ocr.white_preprocess = False
            results = ocr.matched_ocr(image, keyword_classes=MapPlane)
        centers = [area_center(result.area) for result in results]
        logger.info(f'DomainDoor: {centers}')
        directions = [self.screen2direction(center) for center in centers]

        count = len(directions)
        if count == 0:
            logger.warning('No domain exit found')
            return None, None
        elif count == 1:
            if directions[0] < 0:
                return results[0].matched_keyword, None
            else:
                return None, results[0].matched_keyword
        else:
            left = [r for d, r in sorted(zip(directions, results)) if d < 0]
            right = [r for d, r in sorted(zip(directions, results)) if d >= 0]
            if len(left):
                left = left[0].matched_keyword
            else:
                left = None
            if len(right):
                right = right[-1].matched_keyword
            else:
                right = None
            return left, right

    def choose_door(self, left_door: MapPlane | None, right_door: MapPlane | None) -> str | None:
        """
        Args:
            left_door:
            right_door:

        Returns:
            str: 'left_door' or 'right_door' or None
        """
        # Unique domains
        for expect in [
            KEYWORDS_MAP_PLANE.Rogue_DomainBoss,
            KEYWORDS_MAP_PLANE.Rogue_DomainElite,
            KEYWORDS_MAP_PLANE.Rogue_DomainRespite,
        ]:
            if left_door == expect:
                logger.info(f'Goto next domain: left_door={left_door}')
                return 'left_door'
            if right_door == expect:
                logger.info(f'Goto next domain: right_door={right_door}')
                return 'right_door'

        logger.attr('DomainStrategy', self.config.RogueWorld_DomainStrategy)
        if self.config.RogueWorld_DomainStrategy == 'occurrence':
            for expect in [
                KEYWORDS_MAP_PLANE.Rogue_DomainTransaction,
                KEYWORDS_MAP_PLANE.Rogue_DomainOccurrence,
                KEYWORDS_MAP_PLANE.Rogue_DomainEncounter,
                KEYWORDS_MAP_PLANE.Rogue_DomainCombat,
            ]:
                if left_door == expect:
                    logger.info(f'Goto next domain: left_door={left_door}')
                    return 'left_door'
                if right_door == expect:
                    logger.info(f'Goto next domain: right_door={right_door}')
                    return 'right_door'
        elif self.config.RogueWorld_DomainStrategy == 'combat':
            for expect in [
                KEYWORDS_MAP_PLANE.Rogue_DomainCombat,
                KEYWORDS_MAP_PLANE.Rogue_DomainEncounter,
                KEYWORDS_MAP_PLANE.Rogue_DomainOccurrence,
                KEYWORDS_MAP_PLANE.Rogue_DomainTransaction,
            ]:
                if left_door == expect:
                    logger.info(f'Goto next domain: left_door={left_door}')
                    return 'left_door'
                if right_door == expect:
                    logger.info(f'Goto next domain: right_door={right_door}')
                    return 'right_door'
        else:
            logger.error(f'Unknown domain strategy: {self.config.RogueWorld_DomainStrategy}')

        logger.error('No domain was selected, return the first instead')
        if left_door:
            logger.info(f'Goto next domain: left_door={left_door}')
            return 'left_door'
        elif right_door:
            logger.info(f'Goto next domain: right_door={right_door}')
            return 'right_door'
        else:
            logger.error(f'No domain door')
            return None

    exit_has_double_door = False

    def predict_door(self, skip_first_screenshot=True) -> str | None:
        """
        Args:
            skip_first_screenshot:

        Returns:
            str: 'left_door' or 'right_door' or None
        """
        timeout = Timer(3, count=6).start()
        self.exit_has_double_door = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if timeout.reached():
                logger.error('Predict door timeout')
                return None

            left_door, right_door = self.predict_door_by_name(self.device.image)
            logger.info(f'DomainExit: left_door={left_door}, right_door={right_door}')
            if not left_door and not right_door:
                continue

            # End
            self.exit_has_double_door = left_door and right_door
            door = self.choose_door(left_door, right_door)
            if door is not None:
                return door
