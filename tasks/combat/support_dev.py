import os
import time

from PIL import Image

from module.base.button import match_template
from module.base.decorator import cached_property
from module.base.utils import area_offset, area_pad
from module.config.utils import iter_folder, random_id
from module.logger import logger
from tasks.base.ui import UI
from tasks.combat.assets.assets_combat_support_dev import *
from tasks.combat.support import SupportCharacter


class SupportDev(UI):
    def support_refresh_list(self):
        """
        Pages:
            in: LIST_REFRESH
            out: LIST_REFRESHED
        """
        logger.info('Support refresh list')
        # Wait until LIST_REFRESH appear
        for _ in self.loop():
            if self.match_template_color(LIST_REFRESH, threshold=10):
                break

        # LIST_REFRESH -> LIST_REFRESHED
        self.interval_clear(LIST_REFRESH)
        for _ in self.loop():
            if self.match_template_color(LIST_REFRESHED, threshold=10):
                break
            if self.match_template_color(LIST_REFRESH, threshold=10, interval=2):
                self.device.click(LIST_REFRESH)
                continue

    def iter_character_image(self):
        op_x, op_y, _, _ = CHARACTER_OPERATE.area
        _, limit_y1, _, limit_y2 = CHARACTER_OPERATE.search
        x1, y1, x2, y2 = CHARACTER_AVATAR.area
        relative = area_offset(CHARACTER_AVATAR.area, offset=(-op_x, -op_y))
        # Find CHARACTER_OPERATE and move to CHARACTER_AVATAR
        for button in CHARACTER_OPERATE.match_multi_template(self.device.image):
            area = area_offset(relative, button.area[:2])
            # CHARACTER_OPERATE has different relative to CHARACTER_AVATAR in ornament and dungeon
            # use static x coordinate
            area = (x1, area[1], x2, area[3])
            # Limit in height of CHARACTER_OPERATE.search
            if limit_y1 <= area[1] and area[3] <= limit_y2:
                yield area

    @cached_property
    def all_support_templates(self):
        """
        Returns:
            dict: Key: filename, value: image
        """
        data = {}
        for file in iter_folder('assets/character', ext='.png'):
            image = SupportCharacter.load_image(file)
            data[file] = image
        os.makedirs('screenshots/support_dev', exist_ok=True)
        for file in iter_folder('screenshots/support_dev', ext='.png'):
            image = SupportCharacter.load_image(file)
            data[file] = image
        return data

    def gen_support_template_from_area(self, area):
        """
        if match existing templates, do nothing
        otherwise create new template
        """
        search = area_pad(area, pad=5)
        search_image = self.image_crop(search, copy=False)

        # Test if match existing templates
        for template in self.all_support_templates.values():
            if match_template(search_image, template, similarity=0.75):
                return False

        # No match, create new template
        image = self.image_crop(area, copy=False)
        now = int(time.time() * 1000)
        file = f'screenshots/support_dev/{now}_{random_id(length=6)}.png'
        logger.info(f'New support template: {file}')
        Image.fromarray(image).save(file)
        _ = self.all_support_templates
        self.all_support_templates[file] = image
        return True

    def gen_support_templates(self):
        """
        Generate support templates from image
        """
        for area in self.iter_character_image():
            self.gen_support_template_from_area(area)
