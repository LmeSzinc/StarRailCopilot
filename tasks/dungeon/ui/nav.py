import cv2
import numpy as np

from module.base.base import ModuleBase
from module.base.timer import Timer
from module.base.utils import get_color
from module.logger import logger
from module.ocr.ocr import Ocr
from module.ui.draggable_list import DraggableList
from module.ui.switch import Switch
from tasks.base.page import page_guide
from tasks.base.ui import UI
from tasks.dungeon.assets.assets_dungeon_ui import *
from tasks.dungeon.assets.assets_dungeon_ui_rogue import *
from tasks.dungeon.keywords import (
    DungeonNav,
    DungeonTab,
    KEYWORDS_DUNGEON_NAV,
    KEYWORDS_DUNGEON_TAB
)
from tasks.map.interact.aim import inrange


class DungeonTabSwitch(Switch):
    SEARCH_BUTTON = TAB_SEARCH

    def add_state(self, state, check_button, click_button=None):
        # Load search
        if check_button is not None:
            check_button.load_search(self.__class__.SEARCH_BUTTON.area)
        if click_button is not None:
            click_button.load_search(self.__class__.SEARCH_BUTTON.area)
        return super().add_state(state, check_button, click_button)

    def click(self, state, main):
        """
        Args:
            state (str):
            main (ModuleBase):
        """
        button = self.get_data(state)['click_button']
        _ = main.appear(button)  # Search button to load offset
        main.device.click(button)


SWITCH_DUNGEON_TAB = DungeonTabSwitch('DungeonTab', is_selector=True)
SWITCH_DUNGEON_TAB.add_state(
    KEYWORDS_DUNGEON_TAB.Operation_Briefing,
    check_button=OPERATION_BRIEFING_CHECK,
    click_button=OPERATION_BRIEFING_CLICK
)
SWITCH_DUNGEON_TAB.add_state(
    KEYWORDS_DUNGEON_TAB.Daily_Training,
    check_button=DAILY_TRAINING_CHECK,
    click_button=DAILY_TRAINING_CLICK
)
SWITCH_DUNGEON_TAB.add_state(
    KEYWORDS_DUNGEON_TAB.Survival_Index,
    check_button=SURVIVAL_INDEX_CHECK,
    click_button=SURVIVAL_INDEX_CLICK
)
SWITCH_DUNGEON_TAB.add_state(
    KEYWORDS_DUNGEON_TAB.Simulated_Universe,
    check_button=SIMULATED_UNIVERSE_CHECK,
    click_button=SIMULATED_UNIVERSE_CLICK
)
SWITCH_DUNGEON_TAB.add_state(
    KEYWORDS_DUNGEON_TAB.Treasures_Lightward,
    check_button=TREASURES_LIGHTWARD_CHECK,
    click_button=TREASURES_LIGHTWARD_CLICK
)


class OcrDungeonNav(Ocr):
    def after_process(self, result):
        result = super().after_process(result)
        result = result.replace('#', '')
        if self.lang == 'cn':
            result = result.replace('萼喜', '萼')
            result = result.replace('带', '滞')  # 凝带虚影
        return result


class DraggableDungeonNav(DraggableList):
    # 0.5 is the magic number to reach bottom in 1 swipe
    # but relax we still have retires when magic doesn't work
    drag_vector = (0.50, 0.52)


DUNGEON_NAV_LIST = DraggableDungeonNav(
    'DungeonNavList', keyword_class=DungeonNav, ocr_class=OcrDungeonNav, search_button=OCR_DUNGEON_NAV)


class DungeonUINav(UI):
    def dungeon_tab_goto(self, state: DungeonTab):
        """
        Args:
            state:

        Returns:
            bool: If UI switched

        Examples:
            self = DungeonUINav('src')
            self.device.screenshot()
            self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Operation_Briefing)
            self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Daily_Training)
            self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Survival_Index)
        """
        logger.hr('Dungeon tab goto', level=2)
        ui_switched = self.ui_ensure(page_guide)
        tab_switched = SWITCH_DUNGEON_TAB.set(state, main=self)

        if ui_switched or tab_switched:
            if state == KEYWORDS_DUNGEON_TAB.Daily_Training:
                logger.info(f'Tab goto {state}, wait until loaded')
                self._dungeon_wait_daily_training_loaded()
            elif state == KEYWORDS_DUNGEON_TAB.Survival_Index:
                logger.info(f'Tab goto {state}, wait until loaded')
                self._dungeon_wait_survival_index_loaded()
            elif state == KEYWORDS_DUNGEON_TAB.Treasures_Lightward:
                logger.info(f'Tab goto {state}, wait until loaded')
                self._dungeon_wait_treasures_lightward_loaded()
            return True
        else:
            return False

    def _dungeon_wait_daily_training_loaded(self, skip_first_screenshot=True):
        """
        Returns:
            bool: True if wait success, False if wait timeout.

        Pages:
            in: page_guide, Daily_Training
        """
        timeout = Timer(2, count=4).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Wait daily training loaded timeout')
                return False
            color = get_color(self.device.image, DAILY_TRAINING_LOADED.area)
            if np.mean(color) < 128:
                logger.info('Daily training loaded')
                return True

    def _dungeon_wait_survival_index_loaded(self, skip_first_screenshot=True):
        """
        Returns:
            bool: True if wait success, False if wait timeout.

        Pages:
            in: page_guide, Survival_Index
        """
        timeout = Timer(2, count=4).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Wait survival index loaded timeout')
                return False
            if self.appear(SURVIVAL_INDEX_SU_LOADED):
                logger.info('Survival index loaded, SURVIVAL_INDEX_SU_LOADED')
                return True
            if self.appear(SURVIVAL_INDEX_OE_LOADED):
                logger.info('Survival index loaded, SURVIVAL_INDEX_OE_LOADED')
                return True
            if self.appear(SURVIVAL_INDEX_BUILD_LOADED):
                logger.info('Survival index loaded, SURVIVAL_INDEX_BUILD_LOADED')
                return True

    def _dungeon_survival_index_top_appear(self):
        if self.appear(SURVIVAL_INDEX_SU_LOADED):
            return True
        if self.appear(SURVIVAL_INDEX_OE_LOADED):
            return True
        if self.appear(SURVIVAL_INDEX_BUILD_LOADED):
            return True
        return False

    def _dungeon_wait_treasures_lightward_loaded(self, skip_first_screenshot=True):
        """
        Returns:
            bool: True if wait success, False if wait timeout.

        Pages:
            in: page_guide, Survival_Index
        """
        timeout = Timer(2, count=4).start()
        TREASURES_LIGHTWARD_LOADED.set_search_offset((5, 5))
        TREASURES_LIGHTWARD_LOCKED.set_search_offset((5, 5))
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Wait treasures lightward loaded timeout')
                return False
            if self.appear(TREASURES_LIGHTWARD_LOADED):
                logger.info('Treasures lightward loaded (event unlocked)')
                return True
            if self.appear(TREASURES_LIGHTWARD_LOCKED):
                logger.info('Treasures lightward loaded (event locked)')
                return True

    def _dungeon_list_button_has_content(self):
        # Check if having any content
        # List background: 254, guild border: 225
        r, g, b = cv2.split(self.image_crop(LIST_LOADED_CHECK, copy=False))
        minimum = cv2.min(cv2.min(r, g), b)
        minimum = inrange(minimum, lower=0, upper=180)
        if minimum.size > 100:
            return True
        else:
            return False

    def _dungeon_wait_until_dungeon_list_loaded(self, skip_first_screenshot=True):
        timeout = Timer(1, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if timeout.reached():
                logger.warning('Wait until dungeon list loaded timeout')
                return False

            if self._dungeon_list_button_has_content():
                logger.info('Dungeon list loaded')
                return True

    def _dungeon_wait_until_echo_or_war_stabled(self, skip_first_screenshot=True):
        """
        Returns:
            bool: True if wait success, False if wait timeout.

        Pages:
            in: page_guide, Survival_Index
        """
        # Wait until Forgotten_Hall stabled
        timeout = Timer(2, count=4).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if timeout.reached():
                logger.warning('Wait until Echo_of_War stabled timeout')
                return False

            DUNGEON_NAV_LIST.load_rows(main=self)

            # End
            button = DUNGEON_NAV_LIST.keyword2button(KEYWORDS_DUNGEON_NAV.Echo_of_War, show_warning=False)
            if button:
                # 513 is the top of the last row of DungeonNav
                if button.area[1] > 513:
                    logger.info('DungeonNav row Echo_of_War stabled')
                    return True
            else:
                logger.info('No Echo_of_War in list skip waiting')
                return False

    def dungeon_nav_goto(self, nav: DungeonNav, skip_first_screenshot=True):
        """
        Equivalent to `DUNGEON_NAV_LIST.select_row(dungeon.dungeon_nav, main=self)`
        but with tricks to be faster

        Args:
            nav:
            skip_first_screenshot:
        """
        logger.hr('Dungeon nav goto', level=2)
        logger.info(f'Dungeon nav goto {nav}')

        # Wait rows
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            DUNGEON_NAV_LIST.load_rows(main=self)
            if DUNGEON_NAV_LIST.cur_buttons:
                break

        # Wait first row selected
        timeout = Timer(0.5, count=2).start()
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if timeout.reached():
                logger.info('DUNGEON_NAV_LIST not selected')
                break
            if button := DUNGEON_NAV_LIST.get_selected_row(main=self):
                logger.info(f'DUNGEON_NAV_LIST selected at {button}')
                break

        # Check if it's at the first page.
        if DUNGEON_NAV_LIST.keyword2button(KEYWORDS_DUNGEON_NAV.Simulated_Universe, show_warning=False) \
                or DUNGEON_NAV_LIST.keyword2button(KEYWORDS_DUNGEON_NAV.Ornament_Extraction, show_warning=False):
            # Going to use a faster method to navigate but can only start from list top
            logger.info('DUNGEON_NAV_LIST at top')
            # Update points if possible
            # 2.3, No longer weekly points after Divergent Universe unlocked
            # if DUNGEON_NAV_LIST.is_row_selected(button, main=self):
            #     self.dungeon_update_simuni()
        # Treasures lightward is always at top
        elif DUNGEON_NAV_LIST.keyword2button(KEYWORDS_DUNGEON_NAV.Forgotten_Hall, show_warning=False) \
                or DUNGEON_NAV_LIST.keyword2button(KEYWORDS_DUNGEON_NAV.Pure_Fiction, show_warning=False):
            logger.info('DUNGEON_NAV_LIST at top')
        else:
            # To start from any list states.
            logger.info('DUNGEON_NAV_LIST not at top')
            DUNGEON_NAV_LIST.select_row(nav, main=self)
            return True

        # Check the first page
        if nav in [
            KEYWORDS_DUNGEON_NAV.Simulated_Universe,
            KEYWORDS_DUNGEON_NAV.Divergent_Universe,
            KEYWORDS_DUNGEON_NAV.Ornament_Extraction,
            KEYWORDS_DUNGEON_NAV.Calyx_Golden,
            KEYWORDS_DUNGEON_NAV.Calyx_Crimson,
            KEYWORDS_DUNGEON_NAV.Stagnant_Shadow,
            KEYWORDS_DUNGEON_NAV.Cavern_of_Corrosion,
            KEYWORDS_DUNGEON_NAV.Forgotten_Hall,
            KEYWORDS_DUNGEON_NAV.Pure_Fiction,
        ]:
            button = DUNGEON_NAV_LIST.keyword2button(nav)
            if button:
                DUNGEON_NAV_LIST.select_row(nav, main=self, insight=False)
                return True

        # Check the second page
        while 1:
            DUNGEON_NAV_LIST.drag_page('down', main=self)
            # No skip_first_screenshot since drag_page is just called
            if self._dungeon_wait_until_echo_or_war_stabled(skip_first_screenshot=False):
                DUNGEON_NAV_LIST.select_row(nav, main=self, insight=False)
                return True
