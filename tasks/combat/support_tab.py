from module.ui.switch import Switch
from tasks.combat.assets.assets_combat_support_tab import *


class SupportTab(Switch):
    def get(self, main):
        """
        Args:
            main (ModuleBase):

        Returns:
            str: state name or 'unknown'.
        """
        for data in self.state_list:
            button = data['check_button']
            if button.match_template_luma(main.device.image):
                return data['state']

        return 'unknown'

    def click(self, state, main):
        """
        Args:
            state (str):
            main (ModuleBase):
        """
        button = self.get_data(state)['click_button']
        if button.match_template_luma(main.device.image):  # Search button to load offset
            main.device.click(button)
            return True
        return False


def support_tab() -> SupportTab:
    tab = SupportTab('SupportTab', is_selector=True)
    tab.add_state('Catalog', check_button=CATALOG_CHECK, click_button=CATALOG_CLICK)
    tab.add_state('Support', check_button=SUPPORT_CHECK, click_button=SUPPORT_CLICK)
    tab.add_state('Team', check_button=TEAM_CHECK, click_button=TEAM_CLICK)
    return tab
