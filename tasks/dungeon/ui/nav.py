import cv2
import numpy as np

from module.base.base import ModuleBase
from module.base.decorator import cached_property
from module.base.timer import Timer
from module.base.utils import get_color
from module.logger import logger
from module.ocr.ocr import Ocr
from module.ui.draggable_list import DraggableList
from module.ui.switch import Switch
from tasks.base.page import page_guide
from tasks.base.ui import UI
from tasks.dungeon.assets.assets_dungeon_nav import *
from tasks.dungeon.assets.assets_dungeon_tab import *
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
        if main.match_template_luma(button):  # Search button to load offset
            main.device.click(button)
            return True
        return False


class DungeonNavSwitch(DungeonTabSwitch):
    SEARCH_BUTTON = OCR_DUNGEON_NAV

    def state_appear(self, state, main):
        """
        Args:
            state:
            main (ModuleBase):

        Returns:
            bool:
        """
        data = self.get_data(state)
        if main.match_template_luma(data['check_button']):
            return True
        if main.match_template_luma(data['click_button']):
            return True
        return False

    def handle_swipe(self, state, main):
        if state in [
            KEYWORDS_DUNGEON_NAV.Build_Target,
            KEYWORDS_DUNGEON_NAV.Ornament_Extraction,
            KEYWORDS_DUNGEON_NAV.Calyx_Golden,
        ]:
            for below in [
                KEYWORDS_DUNGEON_NAV.Echo_of_War,
                KEYWORDS_DUNGEON_NAV.Cavern_of_Corrosion,
            ]:
                if self.state_appear(below, main=main):
                    main.device.swipe_vector((0, 200), box=OCR_DUNGEON_NAV.area)
                    main.device.sleep(0.3)  # poor sleep indeed
                    return True
        elif state in [
            KEYWORDS_DUNGEON_NAV.Cavern_of_Corrosion,
            KEYWORDS_DUNGEON_NAV.Echo_of_War,
        ]:
            for up in [
                KEYWORDS_DUNGEON_NAV.Build_Target,
                KEYWORDS_DUNGEON_NAV.Ornament_Extraction,
            ]:
                if self.state_appear(up, main=main):
                    main.device.swipe_vector((0, -200), box=OCR_DUNGEON_NAV.area)
                    main.device.sleep(0.3)  # poor sleep indeed
                    return True
        return False


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
    @cached_property
    def dungeon_tab(self):
        tab = DungeonTabSwitch('DungeonTab', is_selector=True)
        tab.add_state(
            KEYWORDS_DUNGEON_TAB.Operation_Briefing,
            check_button=TAB_OPERATION_BRIEFING_CHECK,
            click_button=TAB_OPERATION_BRIEFING_CLICK
        )
        tab.add_state(
            KEYWORDS_DUNGEON_TAB.Daily_Training,
            check_button=TAB_DAILY_TRAINING_CHECK,
            click_button=TAB_DAILY_TRAINING_CLICK
        )
        tab.add_state(
            KEYWORDS_DUNGEON_TAB.Survival_Index,
            check_button=TAB_SURVIVAL_INDEX_CHECK,
            click_button=TAB_SURVIVAL_INDEX_CLICK
        )
        tab.add_state(
            KEYWORDS_DUNGEON_TAB.Simulated_Universe,
            check_button=TAB_SIMULATED_UNIVERSE_CHECK,
            click_button=TAB_SIMULATED_UNIVERSE_CLICK
        )
        tab.add_state(
            KEYWORDS_DUNGEON_TAB.Trailblaze_Experience,
            check_button=TAB_TRAILBLAZE_EXPERIENCE_CHECK,
            click_button=TAB_TRAILBLAZE_EXPERIENCE_CLICK
        )
        return tab

    @cached_property
    def dungeon_nav(self):
        nav = DungeonNavSwitch('DungeonNav', is_selector=True)
        nav.add_state(
            KEYWORDS_DUNGEON_NAV.Build_Target,
            check_button=BUILD_TARGET_CHECK,
            click_button=BUILD_TARGET_CLICK
        )
        nav.add_state(
            KEYWORDS_DUNGEON_NAV.Ornament_Extraction,
            check_button=ORNAMENT_EXTRACTION_CHECK,
            click_button=ORNAMENT_EXTRACTION_CLICK
        )
        nav.add_state(
            KEYWORDS_DUNGEON_NAV.Calyx_Golden,
            check_button=CALYX_GOLDEN_CHECK,
            click_button=CALYX_GOLDEN_CLICK
        )
        nav.add_state(
            KEYWORDS_DUNGEON_NAV.Calyx_Crimson,
            check_button=CALYX_CRIMSON_CHECK,
            click_button=CALYX_CRIMSON_CLICK
        )
        nav.add_state(
            KEYWORDS_DUNGEON_NAV.Stagnant_Shadow,
            check_button=STAGNANT_SHADOW_CHECK,
            click_button=STAGNANT_SHADOW_CLICK
        )
        nav.add_state(
            KEYWORDS_DUNGEON_NAV.Cavern_of_Corrosion,
            check_button=CAVERN_OF_CORROSION_CHECK,
            click_button=CAVERN_OF_CORROSION_CLICK
        )
        nav.add_state(
            KEYWORDS_DUNGEON_NAV.Echo_of_War,
            check_button=ECHO_OF_WAR_CHECK,
            click_button=ECHO_OF_WAR_CLICK
        )
        nav.add_state(
            KEYWORDS_DUNGEON_NAV.Currency_Wars,
            check_button=CURRENCY_WAR_CHECK,
            click_button=CURRENCY_WAR_CLICK
        )
        nav.add_state(
            KEYWORDS_DUNGEON_NAV.Divergent_Universe,
            check_button=DIVERGENT_UNIVERSE_CHECK,
            click_button=DIVERGENT_UNIVERSE_CLICK
        )
        nav.add_state(
            KEYWORDS_DUNGEON_NAV.Simulated_Universe,
            check_button=SIMULATED_UNIVERSE_CHECK,
            click_button=SIMULATED_UNIVERSE_CLICK
        )
        return nav

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
        tab_switched = self.dungeon_tab.set(state, main=self)

        if ui_switched or tab_switched:
            if state == KEYWORDS_DUNGEON_TAB.Daily_Training:
                logger.info(f'Tab goto {state}, wait until loaded')
                self._dungeon_wait_daily_training_loaded()
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

    def dungeon_nav_goto(self, nav: DungeonNav):
        """
        Equivalent to `DUNGEON_NAV_LIST.select_row(dungeon.dungeon_nav, main=self)`
        but with tricks to be faster

        Args:
            nav:
        """
        logger.hr('Dungeon nav goto', level=2)
        logger.info(f'Dungeon nav goto {nav}')

        self.dungeon_nav.set(nav, main=self)
