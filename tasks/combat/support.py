import cv2
import numpy as np

from module.base.button import ClickButton
from module.base.timer import Timer
from module.base.utils import area_offset, crop, image_size, load_image
from module.logger import logger
from module.ui.scroll import AdaptiveScroll
from tasks.base.assets.assets_base_popup import POPUP_CANCEL
from tasks.character.keywords import CharacterList
from tasks.combat.assets.assets_combat_support import *
from tasks.combat.assets.assets_combat_support_tab import SUPPORT_EMPTY
from tasks.combat.assets.assets_combat_team import COMBAT_TEAM_DISMISSSUPPORT, COMBAT_TEAM_SUPPORT
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
    _crop_area = COMBAT_SUPPORT_LIST_GRID.matched_button.area

    def __init__(self, name, screenshot, similarity=0.75):
        self.name = name
        self.image = self._scale_character()
        self.screenshot = crop(screenshot, SupportCharacter._crop_area, copy=False)
        self.similarity = similarity
        self.button = self._find_character()

    def __bool__(self):
        # __bool__ is called when use an object of the class in a boolean context
        return self.button is not None

    def __str__(self):
        return f'SupportCharacter({self.name})'

    __repr__ = __str__

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

    def _scale_character(self):
        """
        Returns:
            Image: Character image after scaled
        """

        if self.name in SupportCharacter._image_cache:
            logger.info(f"Using cached image of {self.name}")
            return SupportCharacter._image_cache[self.name]

        image = self.load_image(f"assets/character/{self.name}.png")
        SupportCharacter._image_cache[self.name] = image
        logger.info(f"Character {self.name} image cached")
        return image

    def _find_character(self):
        character = np.array(self.image)
        support_list_img = self.screenshot
        res = cv2.matchTemplate(
            character, support_list_img, cv2.TM_CCOEFF_NORMED)

        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        max_loc = get_position_in_original_image(
            max_loc, SupportCharacter._crop_area)
        character_width = character.shape[1]
        character_height = character.shape[0]

        return (max_loc[0], max_loc[1], max_loc[0] + character_width, max_loc[1] + character_height) \
            if max_val >= self.similarity else None

    def selected_icon_search(self):
        """
        Returns:
            tuple: (x1, y1, x2, y2) of selected icon search area
        """
        # Check the left of character avatar
        return 0, self.button[1], self.button[0], self.button[3]


class NextSupportCharacter:
    def __init__(self, screenshot):
        self.name = "NextSupportCharacter"
        self.button = self.get_next_support_character_button(screenshot)

    def __bool__(self):
        return self.button is not None

    def get_next_support_character_button(self, screenshot) -> ClickButton | None:
        if SUPPORT_SELECTED.match_template(screenshot, similarity=0.75):
            # Move area to the next character card center
            area = SUPPORT_SELECTED.button
            area = area_offset((105, 85, 255, 170), offset=area[:2])
            if area[3] < COMBAT_SUPPORT_LIST_GRID.area[3]:
                return ClickButton(area, name=self.name)
            else:
                # Out of list
                logger.info('Next character is out of list')
                return None
        else:
            return None

    def is_next_support_character_selected(self, screenshot) -> bool:
        if self.button is None:
            return False
        area = self.button.area
        # Move area from the card center to the left edge of the card
        area = area_offset(area, offset=(-120, 0))
        image = crop(screenshot, area, copy=False)
        return SUPPORT_SELECTED.match_template(image, similarity=0.75, direct_match=True)


class CombatSupport(CombatState):
    def support_set(self, support_character_name: str = "FirstCharacter"):
        """
        Args:
            support_character_name: Support character name

        Returns:
            bool: If clicked

        Pages:
            in: COMBAT_PREPARE
            mid: COMBAT_SUPPORT_LIST
            out: COMBAT_PREPARE or is_combat_executing
        """
        logger.hr("Combat support")
        if isinstance(support_character_name, CharacterList):
            support_character_name = support_character_name.name
        self.interval_clear(COMBAT_TEAM_SUPPORT)
        skip_first_screenshot = True
        selected_support = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(COMBAT_TEAM_DISMISSSUPPORT):
                return True
            if self.is_combat_executing():
                # Entered combat unexpectedly, probably double-clicked COMBAT_SUPPORT_ADD
                logger.warning('support_set ended at is_combat_executing')
                return True

            # Click
            if self.appear(COMBAT_TEAM_SUPPORT, interval=5):
                self.device.click(COMBAT_TEAM_SUPPORT)
                self.interval_reset(COMBAT_TEAM_SUPPORT)
                self.interval_clear(COMBAT_SUPPORT_LIST)
                continue
            if self.appear(POPUP_CANCEL, interval=1):
                logger.warning(
                    "selected identical character, trying select another")
                self._cancel_popup()
                self._select_next_support()
                self.interval_reset(POPUP_CANCEL)
                self.interval_clear(COMBAT_SUPPORT_LIST)
                continue
            if self.appear(COMBAT_SUPPORT_LIST, interval=5):
                # Search support
                if not selected_support:
                    self._search_support_with_fallback(support_character_name)
                    selected_support = True
                self.device.click(COMBAT_SUPPORT_ADD)
                self.interval_reset(COMBAT_SUPPORT_LIST)
                continue
            if self.match_template_luma(SUPPORT_EMPTY, interval=5):
                logger.info('Support empty')
                tab = support_tab()
                tab.set('Strangers', main=self)
                self.interval_reset(SUPPORT_EMPTY)
                continue

    def _get_character(self, support_character_name: str) -> SupportCharacter:
        if support_character_name.startswith("Trailblazer"):
            character = SupportCharacter(f"Stelle{support_character_name[11:]}", self.device.image)
            if character:
                return character
            character = SupportCharacter(f"Caelum{support_character_name[11:]}", self.device.image)
            # Should return something
            return character
        else:
            character = SupportCharacter(support_character_name, self.device.image)
            if character:
                return character
            # Search skin also
            dict_skin: "dict[str, list[str]]" = {
                'March7thPreservation': ['March7thPreservation.2']
            }
            if support_character_name in dict_skin:
                for skin in dict_skin[support_character_name]:
                    character = SupportCharacter(skin, self.device.image)
                    if character:
                        return character
            # Should return something
            return character

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

    def _search_support(self, support_character_name: str = "JingYuan"):
        """
        Args:
            support_character_name: Support character name

        Returns:
            bool: True if found support else False

        Pages:
            in: COMBAT_SUPPORT_LIST
            out: COMBAT_SUPPORT_LIST
        """
        logger.hr("Combat support search")
        # Search prioritize characters
        character = self._get_character(support_character_name)
        if character:
            logger.info("Support found in first page")
            if self._select_support(character):
                return True

        # Search in the following pages
        scroll = self._support_scroll()
        if scroll.appear(main=self):
            if not scroll.at_bottom(main=self):
                # Dropdown to load the entire support list, so large threshold is acceptable
                scroll.drag_threshold, backup = 0.2, scroll.drag_threshold
                scroll.set_bottom(main=self)
                scroll.drag_threshold = backup
                scroll.set_top(main=self)
        self.device.click_record_clear()

        logger.info("Searching support")
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            character = self._get_character(support_character_name)
            if character:
                logger.info("Support found")
                if self._select_support(character):
                    self.device.click_record_clear()
                    return True
                else:
                    logger.warning("Support not selected")
                    self.device.click_record_clear()
                    return False

            if not scroll.at_bottom(main=self):
                scroll.next_page(main=self)
                continue
            else:
                logger.info("Support not found")
                self.device.click_record_clear()
                return False

    def _search_support_with_fallback(self, support_character_name: str = "JingYuan"):
        """
        Args:
            support_character_name: Support character name

        Returns:
            bool: True if found support else False

        Pages:
            in: COMBAT_SUPPORT_LIST
            out: COMBAT_SUPPORT_LIST
        """
        if support_character_name == "FirstCharacter":
            # In normal dungeons first character is selected by default
            return True
        else:
            selected = self._search_support(support_character_name)
            if selected:
                return selected
            # Support not found, fallback to first character
            scroll = self._support_scroll()
            scroll.set_top(main=self)
            self._select_first()
            return True

    def _select_support(self, character: SupportCharacter):
        """
        Args:
            character: Support character

        Pages:
            in: COMBAT_SUPPORT_LIST
            out: COMBAT_SUPPORT_LIST
        """
        logger.hr("Combat support select")
        logger.info(f'Select: {character}')
        skip_first_screenshot = False
        interval = Timer(2)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            area = character.selected_icon_search()
            image = self.image_crop(area, copy=False)
            if SUPPORT_SELECTED.match_template(image, similarity=0.75, direct_match=True):
                logger.info('Character support selected')
                return True

            if interval.reached():
                self.device.click(character)
                interval.reset()
                continue

    def _select_first(self):
        logger.hr("Combat support select")
        logger.info(f'Select: first')
        skip_first_screenshot = False
        interval = Timer(2)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if SUPPORT_SELECTED.match_template(self.device.image, similarity=0.75):
                logger.info('Character support selected')
                return True

            if interval.reached():
                self.device.click(FIRST_CHARACTER)
                interval.reset()
                continue

    def _cancel_popup(self):
        """
        Pages:
            in: CANCEL_POPUP
            out: COMBAT_SUPPORT_LIST
        """
        logger.hr("Combat support cancel popup")
        skip_first_screenshot = True

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(COMBAT_SUPPORT_LIST):
                logger.info("Popup canceled")
                return

            if self.handle_popup_cancel():
                continue

    def _select_next_support(self, skip_first_screenshot=True):
        """
        Pages:
            in: COMBAT_SUPPORT_LIST
            out: COMBAT_SUPPORT_LIST
        """
        logger.hr("Next support select")
        # Wait support arrow
        # If selected identical character, popup may not disappear that fast
        timeout = Timer(1, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            next_support = NextSupportCharacter(self.device.image)
            if next_support:
                break
            if timeout.reached():
                logger.warning('Wait support arrow timeout')
                break

        # Select next
        scroll = AdaptiveScroll(area=COMBAT_SUPPORT_LIST_SCROLL.area,
                                name=COMBAT_SUPPORT_LIST_SCROLL.name)
        interval = Timer(1)
        next_support = None
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if next_support is not None and next_support.is_next_support_character_selected(self.device.image):
                logger.info('Next support selected')
                return

            if interval.reached():
                next_support = NextSupportCharacter(self.device.image)
                if next_support:
                    logger.info("Next support found, clicking")
                    self.device.click(next_support.button)
                elif not scroll.at_bottom(main=self):
                    scroll.next_page(main=self, page=0.4)
                else:
                    logger.warning("No more support")
                    return

                interval.reset()
                continue
