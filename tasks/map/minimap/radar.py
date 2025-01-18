import cv2
import numpy as np

from module.base.decorator import cached_property
from module.base.timer import Timer
from module.base.utils import Points, color_similarity_2d
from module.logger import logger
from tasks.base.page import page_main
from tasks.combat.assets.assets_combat_interact import DUNGEON_COMBAT_INTERACT
from tasks.map.control.control import MapControl
from tasks.map.control.joystick import JoystickContact
from tasks.map.resource.const import diff_to_180_180
from tasks.map.resource.resource import MapResource


class Radar(MapResource):
    def predict_mission(self, image):
        """
        Predict orange mission icon on minimap

        Returns:
            float: Map direction to goto (0~360)
                None if no mission found or multiple mission found
        """
        radius = self.MINIMAP_RADIUS * 1.2
        image = self.get_minimap(image, radius=radius)
        image = color_similarity_2d(image, color=(217, 177, 61))
        cv2.inRange(image, 180, 255, dst=image)
        try:
            points = np.array(cv2.findNonZero(image))[:, 0, :]
        except IndexError:
            # Empty result
            # IndexError: too many indices for array: array is 0-dimensional, but 3 were indexed
            return None

        points = Points(points).group(32)
        points = points - radius

        if len(points) == 1:
            point = points[0]
            direction = self.position2direction(point)
            direction = diff_to_180_180(direction)
            logger.info(f'Mission target at {point}, {direction}')

            # Near current character, stick to previous direction
            if np.linalg.norm(point) < 32:
                return None
            return direction
        else:
            logger.info('Multiple mission point')
            return None


class RadarMixin(MapControl):
    @cached_property
    def radar(self):
        return Radar()

    @cached_property
    def radar_contact(self):
        return JoystickContact(self)

    radar_lost_timout = Timer(1.5, count=5)
    radar_direction_timer = Timer(1, count=3)
    radar_rotation_timer = Timer(1.5, count=5)
    radar_target: float = None

    def handle_radar_rotation_update(self):
        if self.radar_rotation_timer.reached():
            self.minimap.update_rotation(self.device.image)
            self.radar_rotation_timer.reset()

    def handle_mission_interact(self):
        if self.radar_lost_timout.started():
            if self.appear_then_click(DUNGEON_COMBAT_INTERACT, interval=1):
                return True

    def handle_mission_goto(self):
        if not self.ui_page_appear(page_main):
            self.radar_lost_timout.clear()
            self.radar_contact.up()
            return

        self.handle_mission_interact()

        # Limit frequency to set direction
        if not self.radar_direction_timer.reached():
            return
        self.radar_direction_timer.reset()

        # Update target
        direction = self.radar.predict_mission(self.device.image)
        if direction is None:
            if self.radar_lost_timout.started():
                if self.radar_lost_timout.reached():
                    logger.info('Lost radar target')
                    self.radar_lost_timout.clear()
                    self.radar_contact.up()
                    return
                else:
                    # Continue previous direction
                    direction = self.radar_target
            else:
                self.radar_contact.up()
                return

        self.handle_radar_rotation_update()

        # Goto direction
        contact_direction = diff_to_180_180(direction - self.minimap.rotation)
        self.radar_contact.set(contact_direction)
        self.radar_target = direction
        self.radar_lost_timout.reset()
        return
