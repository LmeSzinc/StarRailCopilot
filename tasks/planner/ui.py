from module.base.decorator import cached_property
from module.logger import logger
from module.ui.switch import Switch
from tasks.base.assets.assets_base_page import MENU_SCROLL
from tasks.base.page import page_planner, page_menu
from tasks.base.ui import UI
from tasks.planner.assets import assets_planner_selectpath as assets_path, assets_planner_selecttype as assets_type
from tasks.planner.assets.assets_planner_enter import *


class SwitchPath(Switch):
    def get(self, main):
        """
        Args:
            main (ModuleBase):

        Returns:
            str: state name or 'unknown'.
        """
        for data in self.state_list:
            if main.match_template_color(data['check_button']):
                return data['state']

        return 'unknown'


class SwitchType(SwitchPath):
    def add_state(self, state, check_button, click_button=None):
        # Load search
        if check_button is not None:
            check_button.load_search(assets_type.TYPE_SEARCH.area)
        if click_button is not None:
            click_button.load_search(assets_type.TYPE_SEARCH.area)
        return super().add_state(state, check_button, click_button)


class PlannerUI(UI):
    def handle_planner_aside_close(self, interval=3):
        """
        Returns:
            bool: If clicked
        """
        if self.match_template_luma(ASIDE_CLOSE, interval=interval):
            self.device.click(ASIDE_CLOSE)
            return True
        return False

    def ui_ensure_planner(self):
        """
        Pages:
            in: any
            out: page_planner, MATERIAL_CALCULATION_CHECK
        """
        logger.info('UI ensure planner')
        page = self.ui_get_current_page()
        if page is page_planner:
            pass
        else:
            self.ui_goto(page_menu)

        for _ in self.loop():
            if self.match_template_color(MATERIAL_CALCULATION_CHECK, threshold=20):
                logger.info('At MATERIAL_CALCULATION_CHECK')
                break

            # switch to nav MATERIAL_CALCULATION_CHECK
            if self.match_template_luma(MATERIAL_CALCULATION_CLICK, interval=3):
                self.device.click(MATERIAL_CALCULATION_CLICK)
                continue
            # from page_menu to page_planner
            if self.match_template_luma(MENU_GOTO_PLANNER, interval=3):
                self.device.click(MENU_GOTO_PLANNER)
                continue
            # swipe down page_menu
            if self.ui_page_appear(page_menu, interval=3):
                # swipe directly, as player might have random menu skin
                self.device.swipe_vector(
                    vector=(0, 200), box=MENU_SCROLL.area, random_range=(0, -20, 0, 20), padding=0)
                self.interval_reset(page_menu, interval=3)
                continue
            # skip tons of tutorials
            for button in [
                TUTOTIAL_CHARACTER,
                TUTOTIAL_CHARACTER_LINEUP,
                TUTOTIAL_AUTO_MATCH,
                TUTOTIAL_CHANGE_CONFIGURATION,
                TUTOTIAL_RECOMMEND_LINEUP,
                TUTOTIAL_RECOMMEND_LINEUP_AUTO_MATCH,
                # ASIDE_CLOSE,
            ]:
                if self.match_template_luma(button, interval=2):
                    self.device.click(button)
                    continue
            if self.handle_planner_aside_close():
                continue

    @cached_property
    def planner_calculate_target(self):
        switch = Switch('CalculateTarget', is_selector=True)
        switch.add_state(CHARACTER_MATERIAL_CHECK,
                         check_button=CHARACTER_MATERIAL_CHECK, click_button=CHARACTER_MATERIAL_CLICK)
        switch.add_state(CONE_MATERIAL_CHECK,
                         check_button=CONE_MATERIAL_CHECK, click_button=CONE_MATERIAL_CLICK)
        return switch

    @cached_property
    def planner_character_path(self):
        switch = SwitchPath('CharacterPath', is_selector=True)
        switch.add_state(assets_path.All_CHECK, check_button=assets_path.All_CHECK)
        switch.add_state(assets_path.Destruction_CHECK, check_button=assets_path.Destruction_CHECK)
        switch.add_state(assets_path.The_Hunt_CHECK, check_button=assets_path.The_Hunt_CHECK)
        switch.add_state(assets_path.Erudition_CHECK, check_button=assets_path.Erudition_CHECK)
        switch.add_state(assets_path.Harmony_CHECK, check_button=assets_path.Harmony_CHECK)
        switch.add_state(assets_path.Nihility_CHECK, check_button=assets_path.Nihility_CHECK)
        switch.add_state(assets_path.Preservation_CHECK, check_button=assets_path.Preservation_CHECK)
        switch.add_state(assets_path.Abundance_CHECK, check_button=assets_path.Abundance_CHECK)
        switch.add_state(assets_path.Remembrance_CHECK, check_button=assets_path.Remembrance_CHECK)
        return switch

    @cached_property
    def planner_character_type(self):
        switch = SwitchType('CharacterType', is_selector=True)
        switch.add_state(assets_type.All_CHECK,
                         check_button=assets_type.All_CHECK, click_button=assets_type.All_CLICK)
        switch.add_state(assets_type.Physical_CHECK,
                         check_button=assets_type.Physical_CHECK, click_button=assets_type.Physical_CLICK)
        switch.add_state(assets_type.Fire_CHECK,
                         check_button=assets_type.Fire_CHECK, click_button=assets_type.Fire_CLICK)
        switch.add_state(assets_type.Ice_CHECK,
                         check_button=assets_type.Ice_CHECK, click_button=assets_type.Ice_CLICK)
        switch.add_state(assets_type.Lightning_CHECK,
                         check_button=assets_type.Lightning_CHECK, click_button=assets_type.Lightning_CLICK)
        switch.add_state(assets_type.Wind_CHECK,
                         check_button=assets_type.Wind_CHECK, click_button=assets_type.Wind_CLICK)
        switch.add_state(assets_type.Quantum_CHECK,
                         check_button=assets_type.Quantum_CHECK, click_button=assets_type.Quantum_CLICK)
        switch.add_state(assets_type.Imaginary_CHECK,
                         check_button=assets_type.Imaginary_CHECK, click_button=assets_type.Imaginary_CLICK)
        return switch
