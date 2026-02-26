import cv2
import numpy as np

from module.base.decorator import cached_property, del_cached_property
from module.base.timer import Timer
from module.base.utils import crop, image_size, load_image, color_similarity_2d, random_rectangle_vector_opted
from module.exception import ScriptError
from module.logger import logger
from module.ui.scroll import AdaptiveScroll
from tasks.character.keywords import CharacterList
from tasks.combat.assets.assets_combat_support import *
from tasks.combat.assets.assets_combat_support_dev import LIST_REFRESHED, LIST_REFRESH
from tasks.combat.assets.assets_combat_support_tab import FRIEND_ONLY
from tasks.combat.state import CombatState
from tasks.combat.support_tab import support_tab


def get_position_in_original_image(position_in_croped_image, crop_area):
    """
    Returns:
        tuple: (x, y) of position in original image
    """
    return (
        position_in_croped_image[0] + crop_area[0],
        position_in_croped_image[1] + crop_area[1]) if position_in_croped_image else None


class SupportCharacter:
    _image_cache = {}

    def __init__(self, name, screenshot, similarity=0.75):
        self.name = name
        self.screenshot = screenshot
        self.similarity = similarity
        # warmup cache
        _ = self.button

    def __bool__(self):
        # __bool__ is called when use an object of the class in a boolean context
        return self.button is not None

    def __str__(self):
        return f'SupportCharacter({self.name})'

    __repr__ = __str__

    @classmethod
    def new(cls, name, screenshot) -> "SupportCharacter":
        if name.startswith("Trailblazer"):
            character = cls(f"Stelle{name[11:]}", screenshot)
            if character:
                return character
            character = cls(f"Caelum{name[11:]}", screenshot)
            # Should return something
            return character
        else:
            character = cls(name, screenshot)
            if character:
                return character
            # Search skin also
            dict_skin: "dict[str, list[str]]" = {
                'March7thPreservation': ['March7thPreservation.2'],
                'Firefly': ['Firefly.2'],
                'RuanMei': ['RuanMei.2'],
            }
            if name in dict_skin:
                for skin in dict_skin[name]:
                    character = cls(skin, screenshot)
                    if character:
                        return character
            # Should return something
            return character

    @classmethod
    def load_image(cls, file):
        image = load_image(file)
        size = image_size(image)
        # Template from support page
        if size == (86, 81):
            return image
        # Template from character list page
        if size == (95, 89):
            image = cv2.resize(image, (86, 81))
            return image
        # Unexpected size, resize anyway
        logger.warning(f'Unexpected shape from support template {file}, image size: {size}')
        cv2.resize(image, (86, 81))
        return image

    @cached_property
    def template(self):
        """
        Returns:
            np.ndarray: Character image after scaled
        """
        if self.name in SupportCharacter._image_cache:
            logger.info(f"Using cached image of {self.name}")
            return SupportCharacter._image_cache[self.name]

        image = self.load_image(f"assets/character/{self.name}.png")
        SupportCharacter._image_cache[self.name] = image
        logger.info(f"Character {self.name} image cached")
        return image

    @cached_property
    def button(self) -> "tuple[int, int, int, int] | None":
        template = self.template
        area = COMBAT_SUPPORT_LIST_GRID.matched_button.area

        image = crop(self.screenshot, area, copy=False)
        res = cv2.matchTemplate(template, image, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val < self.similarity:
            return None

        max_loc = get_position_in_original_image(max_loc, area)
        character_width, character_height = image_size(template)
        return max_loc[0], max_loc[1], max_loc[0] + character_width, max_loc[1] + character_height

    @cached_property
    def is_selected(self):
        if self.button is None:
            return False
        # check if having white lines on left edge
        left = COMBAT_SUPPORT_LIST_GRID.matched_button.area[0]
        area = self.button
        if left >= area[0]:
            return False
        area = (left, area[1], area[0], area[3])
        mask = crop(self.screenshot, area, copy=False)
        mask = color_similarity_2d(mask, color=(255, 255, 255))
        cv2.inRange(mask, 221, 255, dst=mask)
        sum_ = cv2.countNonZero(mask)
        return sum_ > 150

    @cached_property
    def has_replace_icon(self):
        if self.button is None:
            return False
        # check if having replace icon on upper-left
        area = self.button
        area = [area[2] - 30, area[1] - 30, area[2] + 30, area[1] + 30]
        image = crop(self.screenshot, area, copy=False)
        return REPLACE_ICON.match_template(image, direct_match=True)


class FirstCharacter(SupportCharacter):
    @classmethod
    def first(cls, screenshot):
        return cls.new('FirstCharacter', screenshot)

    @cached_property
    def button(self):
        return FIRST_CHARACTER.button


class CombatSupport(CombatState):
    def _on_enter_support(self):
        # abstract, so ornament can override
        tab = support_tab()
        tab.set('Support', main=self)
        self._support_disable_friend_only()

    def support_set(
            self,
            name: str = "FirstCharacter",
            replace=4,
            support_button=COMBAT_TEAM_SUPPORT,
            dismiss_button=COMBAT_TEAM_DISMISSSUPPORT,
            confirm_button=COMBAT_SUPPORT_ADD,
    ):
        """
        Args:
            name: Support character name
            replace (int): 1 to 4
            support_button:
            dismiss_button:
            confirm_button:

        Returns:
            bool: If clicked

        Pages:
            in: COMBAT_PREPARE
            mid: COMBAT_SUPPORT_LIST
            out: COMBAT_PREPARE or is_combat_executing
        """
        logger.hr("Combat support", level=2)
        if isinstance(name, CharacterList):
            name = name.name
        self.interval_clear(support_button)

        # COMBAT_PREPARE -> COMBAT_SUPPORT_LIST
        for _ in self.loop():
            if self.match_template_luma(dismiss_button):
                return True
            if self.appear(COMBAT_SUPPORT_LIST):
                # check refresh also, because ornament team page has COMBAT_SUPPORT_LIST too
                if self.match_template_color(LIST_REFRESH) or self.match_template_color(LIST_REFRESHED):
                    break
            if self.appear_then_click(support_button, interval=5):
                continue

        # select support
        self._on_enter_support()
        self._search_support_with_fallback(name, replace=replace)

        # COMBAT_SUPPORT_LIST -> COMBAT_PREPARE
        for _ in self.loop():
            if self.match_template_luma(dismiss_button):
                logger.info('Combat support ended')
                return True
            if self.is_combat_executing():
                # Entered combat unexpectedly, probably double-clicked COMBAT_SUPPORT_ADD
                logger.warning('support_set ended at is_combat_executing')
                return True
            if self.appear(COMBAT_SUPPORT_LIST, interval=5):
                self.device.click(confirm_button)
                self.interval_reset(COMBAT_SUPPORT_LIST)
                continue

    def _support_disable_friend_only(self):
        logger.info('Support disable friend only')
        interval = Timer.from_seconds(3)
        for _ in self.loop():
            appear = self.image_color_count(FRIEND_ONLY, color=(255, 200, 112), threshold=221, count=400)
            if appear:
                if interval.reached():
                    self.device.click(FRIEND_ONLY)
                    interval.reset()
                    continue
            else:
                break

    @staticmethod
    def _support_scroll():
        """
        v3.2, Ornament has different support scroll so OrnamentCombat._support_scroll will override this
        """
        return AdaptiveScroll(area=COMBAT_SUPPORT_LIST_SCROLL.area,
                              name=COMBAT_SUPPORT_LIST_SCROLL.name)

    def support_refresh_wait_top(self):
        """
        Wait until scroll at top after refresh support list

        Pages:
            in: LIST_REFRESH
        """
        scroll = self._support_scroll()
        timeout = Timer(1, count=3).start()
        for _ in self.loop():
            if timeout.reached():
                logger.warning('Wait support list at top timeout')
                break
            if scroll.at_top(main=self):
                break

    def _search_support(self, name: str = "JingYuan", replace=4):
        """
        Args:
            name: Support character name
            replace (int): 1 to 4

        Returns:
            bool: True if found support else False

        Pages:
            in: COMBAT_SUPPORT_LIST
            out: COMBAT_SUPPORT_LIST
        """
        logger.hr("Combat support search", level=2)
        scroll = self._support_scroll()
        count = 0
        while 1:
            character = SupportCharacter.new(name, self.device.image)
            if character:
                if self._select_support(character, replace=replace):
                    return True
                else:
                    # wait selected timeout, retry
                    continue

            # no character, scroll
            if scroll.at_bottom(main=self):
                logger.info("Support not found (scroll at bottom)")
                self.device.click_record_clear()
                return False
            # scroll
            count += 1
            if count >= 100:
                logger.info("Support not found (too many drags)")
            p1, p2 = random_rectangle_vector_opted(
                (0, -320), box=COMBAT_SUPPORT_LIST_GRID.button, random_range=(-20, -30, 20, 30), padding=0)
            self.device.drag(p1, p2, name=f'SUPPORT_DRAG_{count}')
            self.device.screenshot()
            continue
        return False

    def _select_first(self, replace=4):
        """
        Args:
            replace (int): 1 to 4

        Returns:
            bool: True if found support else False

        Pages:
            in: COMBAT_SUPPORT_LIST
            out: COMBAT_SUPPORT_LIST
        """
        logger.hr("Combat support first", level=2)

        while 1:
            character = FirstCharacter.first(self.device.image)
            if self._select_support(character, replace=replace):
                return True
            else:
                # wait selected timeout, retry
                continue

    def _search_support_with_fallback(self, name: str = "JingYuan", replace=4):
        """
        Args:
            name: Support character name
            replace (int): 1 to 4

        Returns:
            bool: True if found support else False

        Pages:
            in: COMBAT_SUPPORT_LIST
            out: COMBAT_SUPPORT_LIST
        """
        if name == "FirstCharacter":
            self._select_first(replace=replace)
            return True
        else:
            selected = self._search_support(name, replace=replace)
            if selected:
                return selected
            # Support not found, fallback to first character
            scroll = self._support_scroll()
            scroll.set_top(main=self)
            self._select_first(replace=replace)
            return True

    @cached_property
    def _dict_character_slot(self):
        return {
            1: CHARACTER_SLOT_1,
            2: CHARACTER_SLOT_2,
            3: CHARACTER_SLOT_3,
            4: CHARACTER_SLOT_4,
        }

    def _remove_character(self, index):
        """
        Args:
            index (int): 1 to 4
        """
        button = self._dict_character_slot.get(index)
        if button is None:
            raise ScriptError(f'Invalid character slot index: {index}')
        interval = Timer.from_seconds(2)
        for _ in self.loop():
            # End
            if self.match_template_luma(button):
                logger.info(f'Character slot #{index} freed')
                break
            if interval.reached():
                button.clear_offset()
                self.device.click(button)
                interval.reset()
                continue

    def _get_empty_slot(self) -> "list[int]":
        slots = []
        for index, button in self._dict_character_slot.items():
            if self.match_template_luma(button):
                slots.append(index)
        return slots

    def _select_support(self, character: SupportCharacter, replace=4):
        """
        Note that this function has no retry, callers should handle retries

        Returns:
            bool: If character selected
        """
        logger.hr("Combat support select", level=2)
        if character.has_replace_icon:
            logger.info('Support character will replace existing character')
        elif self._get_empty_slot():
            logger.info('Support character will be added to empty slot')
        else:
            logger.info(f'Support character will remove slot #{replace}')
            self._remove_character(replace)

        self.device.click(character)
        for _ in self.loop(timeout=2, skip_first=False):
            # End
            del_cached_property(character, 'is_selected')
            character.screenshot = self.device.image
            if character.is_selected:
                logger.info('Character support selected')
                return True
        logger.info('Character support not selected')
        return False


if __name__ == '__main__':
    self = CombatSupport('src')

    # self.image_file = r'C:\Users\LmeSzinc\Documents\MuMu共享文件夹\Screenshots\src4.0\2026-02-18_06-49-21-471270.png'
    # self.image_file = r'C:\Users\LmeSzinc\Documents\MuMu共享文件夹\Screenshots\src4.0\2026-02-18_06-47-50-932699.png'
    # self.image_file = r'C:\Users\LmeSzinc\Documents\MuMu共享文件夹\Screenshots\src4.0\2026-02-18_07-12-35-934232.png'
    # c = SupportCharacter.new('Firefly', self.device.image)
    # print(c, c.button, c.is_selected, c.has_replace_icon)
    self.device.screenshot()
    # self._search_support('Firefly')
    self.support_set('Firefly')
