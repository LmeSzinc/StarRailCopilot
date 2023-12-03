from typing import Literal

from module.base.timer import Timer
from module.base.utils import area_offset
from module.logger import logger
from module.ocr.ocr import Ocr
from module.ui.scroll import Scroll
from module.ui.switch import Switch
from tasks.base.assets.assets_base_popup import POPUP_CONFIRM
from tasks.base.page import page_item
from tasks.base.ui import UI
from tasks.item.assets.assets_item_ui import *
from tasks.item.inventory import Inventory
from tasks.item.keywords import KEYWORD_ITEM_TAB
from tasks.item.keywords.classes import SortType

SWITCH_ITEM_TAB = Switch('ItemTab', is_selector=True)
SWITCH_ITEM_TAB.add_state(
    KEYWORD_ITEM_TAB.UpgradeMaterials,
    check_button=UPGRADE_MATERIAL_CHECK,
    click_button=UPGRADE_MATERIAL_CLICK
)
SWITCH_ITEM_TAB.add_state(
    KEYWORD_ITEM_TAB.LightCone,
    check_button=LIGHT_CONE_CHECK,
    click_button=LIGHT_CONE_CLICK
)
SWITCH_ITEM_TAB.add_state(
    KEYWORD_ITEM_TAB.Relics,
    check_button=RELICS_CHECK,
    click_button=RELICS_CLICK
)
SWITCH_ITEM_TAB.add_state(
    KEYWORD_ITEM_TAB.OtherMaterials,
    check_button=OTHER_MATERIALS_CHECK,
    click_button=OTHER_MATERIALS_CLICK
)
SWITCH_ITEM_TAB.add_state(
    KEYWORD_ITEM_TAB.Consumables,
    check_button=CONSUMABLE_CHECK,
    click_button=CONSUMABLE_CLICK,
)
SWITCH_ITEM_TAB.add_state(
    KEYWORD_ITEM_TAB.Missions,
    check_button=MISSIONS_CHECK,
    click_button=MISSIONS_CLICK
)
SWITCH_ITEM_TAB.add_state(
    KEYWORD_ITEM_TAB.Valuables,
    check_button=VALUABLES_CHECK,
    click_button=VALUABLES_CLICK
)


class ItemUI(UI):
    def item_goto(self, state: KEYWORD_ITEM_TAB, wait_until_stable=True):
        """
        Args:
            state:
            wait_until_stable: if subsequent actions are manipulating items, or any other thing that needs to load
                inside the tab, wait_until_stable should set to True

        Returns:
            self = ItemUI('alas')
            self.device.screenshot()
            self.item_goto(KEYWORD_ITEM_TAB.Relics)
            self.item_goto(KEYWORD_ITEM_TAB.Consumables)
        """
        logger.hr('Item tab goto', level=2)
        self.ui_ensure(page_item)
        SWITCH_ITEM_TAB.set(state, main=self)
        if wait_until_stable:
            logger.info(f'Tab goto {state}, wait until loaded')
            Inventory(ITEM_PAGE_INVENTORY, 6 * 4).wait_until_inventory_stable(main=self)
        else:
            logger.info(f'Tab goto {state}')

    def _get_sort_order_button(self, key: SortType):
        ocr = Ocr(OCR_SORT_TYPE)
        scroll = Scroll(SORT_SCROLL, (80, 81, 84))
        scroll.edge_threshold = 0.15
        scroll.drag_threshold = 0.15

        sort_types = ocr.matched_ocr(self.device.image, SortType)
        button = None
        while not button:
            for sort_type in sort_types:
                if sort_type.matched_keyword == key:
                    button = sort_type

            if not button and scroll.appear(main=self):
                scroll.next_page(main=self)

            if not scroll.appear(main=self) or scroll.at_bottom(main=self):
                break

        if not button:
            logger.warning(f"Sort type {key} not found")

        return button

    def _sort_type_button_selected(self, button):
        return self.image_color_count(area_offset(button, (230, 0)), (236, 154, 54))

    def _toggle_sort_order(self, search, skip_first_screenshot=True):
        ORDER_ASCENDING.matched_button.search = search
        ORDER_DESCENDING.matched_button.search = search
        if self.appear(ORDER_ASCENDING):
            click_button = ORDER_DESCENDING
            logger.info("Ascending -> Descending")
        else:
            click_button = ORDER_ASCENDING
            logger.info("Descending -> Ascending")

        interval = Timer(1)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(click_button):
                return

            if interval.reached():
                self.device.click(click_button)
                interval.reset()

    def ensure_sort_order(self, search, order: Literal['ascending', 'descending'],
                          skip_first_screenshot=True):
        ORDER_ASCENDING.matched_button.search = search
        ORDER_DESCENDING.matched_button.search = search
        if (self.appear(ORDER_ASCENDING) and order == 'ascending'
                or self.appear(ORDER_DESCENDING) and order == 'descending'):
            return
        else:
            self._toggle_sort_order(search, skip_first_screenshot=skip_first_screenshot)

    def ensure_sort_type(self, button: ButtonWrapper, key: SortType, skip_first_screenshot=True) -> bool:
        """

        Args:
            button: button that opens sort type selection popup, which should not include sort order button
            key:
            skip_first_screenshot:

        Returns:
            ensured or not
        """
        ocr = Ocr(button)
        results = ocr.matched_ocr(self.device.image, SortType)
        for result in results:
            if result.matched_keyword == key:
                return True

        interval = Timer(1)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(POPUP_CONFIRM):
                break
            if interval.reached():  # click too fast will open then close tab immediately
                if self.image_color_count(button, (221, 223, 223), count=6000):
                    self.device.click(button)
                    interval.reset()

        type_button = self._get_sort_order_button(key=key)

        interval = Timer(1)
        if type_button:  # select the type. If ocr failed then use the default one
            skip_first_screenshot = True
            while 1:
                if skip_first_screenshot:
                    skip_first_screenshot = False
                else:
                    self.device.screenshot()

                if self._sort_type_button_selected(type_button.button):
                    logger.info(f"Type selected: {key}")
                    break

                if interval.reached():
                    self.device.click(type_button)
                    interval.reset()

        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.image_color_count(button, (225, 226, 229)):
                break

            if interval.reached():
                self.device.click(POPUP_CONFIRM)
                interval.reset()

        return bool(type_button)
