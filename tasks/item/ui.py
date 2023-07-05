from module.logger import logger
from module.ui.switch import Switch
from tasks.base.page import page_item
from tasks.base.ui import UI
from tasks.item.assets.assets_item_ui import *
from tasks.item.keywords import KEYWORD_ITEM_TAB

SWITCH_ITEM_TAB = Switch('ItemTab', is_selector=True)
SWITCH_ITEM_TAB.add_state(
    KEYWORD_ITEM_TAB.Upgrade_Materials,
    check_button=UPGRADE_MATERIAL_CHECK,
    click_button=UPGRADE_MATERIAL_CLICK
)
SWITCH_ITEM_TAB.add_state(
    KEYWORD_ITEM_TAB.Relics,
    check_button=RELICS_CHECK,
    click_button=RELICS_CLICK
)
SWITCH_ITEM_TAB.add_state(
    KEYWORD_ITEM_TAB.Consumables,
    check_button=CONSUMABLE_CHECK,
    click_button=CONSUMABLE_CLICK,
)


class ItemUI(UI):
    def item_goto(self, state: KEYWORD_ITEM_TAB):
        """
        Args:
            state:

        Returns:
            self = ItemUI('alas')
            self.device.screenshot()
            self.item_goto(KEYWORD_ITEM_TAB.Relics)
            self.item_goto(KEYWORD_ITEM_TAB.Consumables)
        """
        self.ui_ensure(page_item)
        if SWITCH_ITEM_TAB.set(state, main=self):
            logger.info(f'Tab goto {state}, wait until loaded')
