import os
import time

from module.base.button import match_template
from module.base.decorator import cached_property
from module.base.utils import area_offset, area_pad, load_image
from module.config.utils import iter_folder, random_id
from module.logger import logger
from module.ui.switch import Switch
from tasks.base.ui import UI
from tasks.combat.assets.assets_combat_support_dev import *
from tasks.combat.support import SupportCharacter
from PIL import Image


class SupportTab(Switch):
    def add_state(self, state, check_button, click_button=None):
        # Load search
        if check_button is not None:
            check_button.load_search(TAB_SEARCH.area)
        if click_button is not None:
            click_button.load_search(TAB_SEARCH.area)
        return super().add_state(state, check_button, click_button)

    def click(self, state, main):
        """
        Args:
            state (str):
            main (ModuleBase):
        """
        button = self.get_data(state)['click_button']
        _ = button.match_template_luma(main.device.image)  # Search button to load offset
        main.device.click(button)


class SupportDev(UI):
    def support_tab(self) -> SupportTab:
        tab = SupportTab('SupportTab', is_selector=True)
        tab.add_state('Friends', check_button=FRIENDS_CHECK, click_button=FRIENDS_CLICK)
        tab.add_state('Strangers', check_button=STRANGER_CHECK, click_button=STRANGER_CLICK)
        return tab

    def iter_character_image(self):
        op_x, op_y, _, _ = CHARACTER_OPERATE.area
        _, limit_y1, _, limit_y2 = CHARACTER_OPERATE.search
        relative = area_offset(CHARACTER_AVATAR.area, offset=(-op_x, -op_y))
        # Find CHARACTER_OPERATE and move to CHARACTER_AVATAR
        for button in CHARACTER_OPERATE.match_multi_template(self.device.image):
            area = area_offset(relative, button.area[:2])
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
            if match_template(search_image, template):
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
