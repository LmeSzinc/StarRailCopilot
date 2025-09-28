from module.ui.switch import Switch
from tasks.combat.assets.assets_combat_support_tab import *


class SupportTab(Switch):
    def add_state(self, state, check_button, click_button=None):
        # Load search
        if check_button is not None:
            check_button.load_search(TAB_SEARCH.area)
        if click_button is not None:
            click_button.load_search(TAB_SEARCH.area)
        return super().add_state(state, check_button, click_button)

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
        _ = button.match_template_luma(main.device.image)  # Search button to load offset
        main.device.click(button)


def support_tab() -> SupportTab:
    tab = SupportTab('SupportTab', is_selector=True)
    tab.add_state('Friends', check_button=FRIENDS_CHECK, click_button=FRIENDS_CLICK)
    tab.add_state('Strangers', check_button=STRANGER_CHECK, click_button=STRANGER_CLICK)
    return tab
