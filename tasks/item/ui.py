from module.logger import logger
from module.ui.switch import Switch
from tasks.base.ui import UI
from tasks.item.assets.assets_item_consumable_usage import SIMPLE_PROTECTIVE_GEAR
from tasks.item.assets.assets_item_ui import *
from tasks.item.keywords import KEYWORDS_ITEM_TAB


class SwitchItemTab(Switch):
    def add_state(self, state, check_button, click_button=None):
        # Load search
        if check_button is not None:
            check_button.load_search(SWITCH_SEARCH.area)
        if click_button is not None:
            click_button.load_search(SWITCH_SEARCH.area)
            # Limit click_button.button
            left = SWITCH_CLICK.area[0]
            for button in click_button.buttons:
                button._button = (left, button._button[1], button._button[2], button._button[3])
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


SWITCH_ITEM_TAB = SwitchItemTab('ItemTab', is_selector=True)
SWITCH_ITEM_TAB.add_state(
    KEYWORDS_ITEM_TAB.UpgradeMaterials,
    check_button=UPGRADE_MATERIAL_CHECK,
    click_button=UPGRADE_MATERIAL_CLICK
)
SWITCH_ITEM_TAB.add_state(
    KEYWORDS_ITEM_TAB.LightCones,
    check_button=LIGHT_CONE_CHECK,
    click_button=LIGHT_CONE_CLICK
)
SWITCH_ITEM_TAB.add_state(
    KEYWORDS_ITEM_TAB.Relics,
    check_button=RELICS_CHECK,
    click_button=RELICS_CLICK
)
SWITCH_ITEM_TAB.add_state(
    KEYWORDS_ITEM_TAB.OtherMaterials,
    check_button=OTHER_MATERIALS_CHECK,
    click_button=OTHER_MATERIALS_CLICK
)
SWITCH_ITEM_TAB.add_state(
    KEYWORDS_ITEM_TAB.Consumables,
    check_button=CONSUMABLE_CHECK,
    click_button=CONSUMABLE_CLICK,
)
SWITCH_ITEM_TAB.add_state(
    KEYWORDS_ITEM_TAB.Missions,
    check_button=MISSIONS_CHECK,
    click_button=MISSIONS_CLICK
)
SWITCH_ITEM_TAB.add_state(
    KEYWORDS_ITEM_TAB.Valuables,
    check_button=VALUABLES_CHECK,
    click_button=VALUABLES_CLICK
)
SWITCH_ITEM_TAB.add_state(
    KEYWORDS_ITEM_TAB.MaterialExchange,
    check_button=MATERIAL_EXCHANGE_CHECK,
    click_button=MATERIAL_EXCHANGE_CLICK
)


class ItemUI(UI):
    def item_goto(self, state: KEYWORDS_ITEM_TAB, wait_until_stable=True):
        """
        Args:
            state:
            wait_until_stable: if subsequent actions are manipulating items, or any other thing that needs to load
                inside the tab, wait_until_stable should set to True

        Returns:
            bool: If switched

        Examples:
            self = ItemUI('alas')
            self.device.screenshot()
            self.item_goto(KEYWORDS_ITEM_TAB.Relics)
            self.item_goto(KEYWORDS_ITEM_TAB.Consumables)
        """
        if SWITCH_ITEM_TAB.set(state, main=self):
            if wait_until_stable:
                logger.info(f'Tab goto {state}, wait until loaded')
                self.wait_until_stable(SIMPLE_PROTECTIVE_GEAR)
            else:
                logger.info(f'Tab goto {state}')
            return True
        else:
            return False
