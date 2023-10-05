import math
import re

from module.base.timer import Timer
from module.base.utils import area_offset, area_pad
from module.logger import logger
from module.ocr.ocr import Ocr, DigitCounter
from tasks.base.assets.assets_base_page import CLOSE
from tasks.base.assets.assets_base_popup import GET_REWARD
from tasks.item.assets.assets_item_relics import *
from tasks.item.assets.assets_item_relics_enhance import *
from tasks.item.assets.assets_item_relics_salvage import *
from tasks.item.assets.assets_item_ui import ORDER_ASCENDING, ORDER_DESCENDING, ITEM_PAGE_INVENTORY
from tasks.item.inventory import Item, Inventory
from tasks.item.keywords import KEYWORD_ITEM_TAB, KEYWORD_SORT_TYPE
from tasks.item.ui import ItemUI


def offset_to_sort_order_area(sort_type_button):
    return area_offset(sort_type_button.button, (200, 0))


class RelicEXPCounter(DigitCounter):
    def format_result(self, result) -> tuple[int, int, int]:
        result = super().after_process(result)
        logger.attr(name=self.name, text=str(result))

        res = re.search(r'(?:\+(\d+))?\D*(\d+)/(\d+)', result)
        if res:
            groups = [int(s) if s else 0 for s in res.groups()]
            [added, current, total] = groups
            current += added
            return current, total - current, total
        else:
            logger.warning(f'No digit counter found in {result}')
            return 0, 0, 0


class RelicsUI(ItemUI):
    def _is_in_salvage(self) -> bool:
        return self.appear(ORDER_ASCENDING) or self.appear(ORDER_DESCENDING)

    def _select_salvage_relic(self, skip_first_screenshot=True):
        interval = Timer(1)
        timeout = Timer(5, count=3).start()
        self.ensure_sort_type(SALVAGE_SORT_TYPE_BUTTON, KEYWORD_SORT_TYPE.Rarity)
        self.ensure_sort_order(offset_to_sort_order_area(SALVAGE_SORT_TYPE_BUTTON), "ascending")
        inventory = Inventory(SALVAGE_INVENTORY)
        items = iter(inventory.recognize_single_page_items(main=self))

        item = next(items)

        while item and item.is_item_locked(main=self):
            logger.info(f"{item} locked, choose next one")
            item = next(items)

        while 1:  # salvage -> first relic selected
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Timeout when selecting relic')
                return False
            # The first frame entering relic page, SALVAGE is a white button as it's the default state.
            # At the second frame, SALVAGE is disabled since no items are selected.
            # So here uses the minus button on the first relic.
            if item.is_item_selected(main=self):
                logger.info(f'Relic {item} selected')
                break
            if interval.reached():
                self.device.click(item)
                interval.reset()
                continue

    def salvage_relic(self, skip_first_screenshot=True) -> bool:
        logger.hr('Salvage Relic', level=2)
        self.item_goto(KEYWORD_ITEM_TAB.Relics, wait_until_stable=False)
        while 1:  # relic tab -> salvage
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._is_in_salvage():
                logger.info('_is_in_salvage')
                break
            if self.appear_then_click(GOTO_SALVAGE, interval=2):
                continue

        self._select_salvage_relic()  # salvage -> first relic selected

        skip_first_screenshot = True
        while 1:  # selected -> rewards claimed
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(GET_REWARD):
                logger.info("Relic salvaged")
                break
            if self.appear_then_click(SALVAGE, interval=2):
                continue
            if self.handle_popup_confirm():
                continue

        skip_first_screenshot = True
        interval = Timer(1)
        while 1:  # rewards claimed -> relic tab page
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(GOTO_SALVAGE):
                logger.info("Salvage page exited")
                break
            if self.handle_reward(interval=2):
                continue
            if interval.reached() and self._is_in_salvage():
                logger.info(f'_is_in_salvage -> {CLOSE}')
                self.device.click(CLOSE)
                interval.reset()
                continue
        return True

    def get_exp_remain(self):
        counter = RelicEXPCounter(ENHANCE_RELIC_EXP_OCR)
        _, remain, _ = counter.ocr_single_line(self.device.image)
        return remain

    def _does_level_up(self):
        ocr = Ocr(ENHANCE_RELIC_LEVEL_OCR)
        result = ocr.ocr_single_line(self.device.image)
        result = re.sub(r'^\+\d*', "", result)
        return "+" in result

    def _add_item(self, item: Item, stackable: bool, count=1, skip_first_screenshot=True) -> bool:
        if stackable:
            logger.info(f"Add {count} items")
            current, _, _ = item.get_stackable_item_count(main=self)
            add_button = area_pad(item.button)  # avoid clicking minus button
            minus_button = item.get_minus_button()

            retry = Timer(1, count=2)
            while 1:
                if skip_first_screenshot:
                    skip_first_screenshot = False
                else:
                    self.device.screenshot()

                new_current, _, _ = item.get_stackable_item_count(main=self)
                count_needed = count - new_current + current

                logger.info(f"{count_needed} needed")

                if count_needed == 0:
                    logger.info(f"{count} {item} added")
                    return True

                if retry.reached():
                    item.button = add_button if count_needed > 0 else minus_button
                    self.device.multi_click(item, count_needed)
                    retry.reset()

        else:
            interval = Timer(.5).start()
            while 1:
                if skip_first_screenshot:
                    skip_first_screenshot = False
                else:
                    self.device.screenshot()

                if item.is_item_selected(main=self):
                    logger.info(f"{item} added")
                    return True
                if interval.reached():
                    self.device.click(item)
                    interval.reset()

    def _feed_one_level(self, inventory: Inventory, skip_first_screenshot=True):
        exp_list = [0, 100, 500, 1000, 1500]

        items = iter(sorted(inventory.recognize_single_page_items(main=self), key=lambda i: i.get_rarity(main=self)))
        item = next(items)
        added_item = 0
        slot_num = 8

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._does_level_up():
                logger.info("Enough materials fed, able to level up")
                self._enhance_confirm()
                return True
            if added_item == slot_num:
                logger.info("Slot full, enhance without level up first")
                self._enhance_confirm()
                added_item = 0

            # The fact is, the locked/equipped relics will be sorted at bottom of the inventory
            # while inventory.is_item_locked(item):
            #     item = next(items)

            stackable = item.is_item_stackable(main=self)
            exp_count = 0
            if stackable:
                _, remain, _ = item.get_stackable_item_count(main=self)
                exp = exp_list[item.get_rarity(main=self) - 1]
                exp_needed = self.get_exp_remain()
                exp_count = math.ceil(exp_needed / exp)
                exp_count = exp_count if remain > exp_count else remain

            if self._add_item(item, stackable, count=exp_count):
                added_item += 1

                if not item:
                    logger.warning("Can not fed enough materials, unable to level up")
                    return False

                if stackable:
                    _, remain, _ = item.get_stackable_item_count(main=self)
                    if remain == 0:
                        item = next(items)
                else:
                    item = next(items)

            else:
                logger.warning(f"Try add item {item} failed")

    def _enhance_confirm(self, skip_first_screenshot=True):
        interval = Timer(1).start()
        # click enhance
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(ENHANCE_POPUP):
                break
            if self.handle_popup_confirm():
                continue
            if interval.reached():
                self.device.click(ENHANCE)
                interval.reset()

        # handle popup
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(ENHANCE_MATERIAL_SLOTS):
                logger.info("Enhance complete")
                break
            if self.appear_then_click(ENHANCE_POPUP):
                continue

    def _select_relic(self, skip_first_screenshot=True) -> bool:
        def is_max_level(relic: Item):
            level = relic.get_data_count(main=self)
            rarity = relic.get_rarity(main=self)
            return level == rarity * 3

        interval = Timer(1)
        # select first relic
        inventory = Inventory(ITEM_PAGE_INVENTORY)
        items = iter(inventory.recognize_single_page_items(main=self))
        item = next(items)

        while item and is_max_level(item):
            logger.info(f"{item} is max level, skip")
            item = next(items)
        if not item:
            logger.warning("No relic can be leveled up")
            return False

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if item.is_item_selected(main=self):
                break

            if interval.reached():
                self.device.click(item)
                interval.reset()

        return True

    def level_up_relic(self, skip_first_screenshot=True) -> bool:
        logger.hr('Level up relic', level=2)
        self.item_goto(KEYWORD_ITEM_TAB.Relics, wait_until_stable=False)
        self.ensure_sort_type(RELIC_MAIN_PAGE_SORT_TYPE_BUTTON, key=KEYWORD_SORT_TYPE.Rarity)
        self.ensure_sort_order(offset_to_sort_order_area(RELIC_MAIN_PAGE_SORT_TYPE_BUTTON), "ascending")

        # select relic
        if not self._select_relic():
            return False

        interval = Timer(1)
        # details -> enhance tab
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(ENHANCE_TAB):
                break

            if interval.reached():
                self.device.click(ITEM_DETAILS)
                interval.reset()

        # enhance tab -> open slots
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.image_color_count(RELIC_SELECTION_PAGE_SORT_TYPE_BUTTON, (225, 226, 229)):
                break
            if self.match_template_color(ENHANCE_TAB) and interval.reached():
                self.device.click(ENHANCE_TAB)
                interval.reset()
                continue
            if self.appear_then_click(ENHANCE_MATERIAL_SLOTS):
                continue

        # add items
        self.ensure_sort_type(RELIC_SELECTION_PAGE_SORT_TYPE_BUTTON, KEYWORD_SORT_TYPE.Rarity)
        self.ensure_sort_order(offset_to_sort_order_area(RELIC_SELECTION_PAGE_SORT_TYPE_BUTTON), "ascending")
        inventory = Inventory(ENHANCE_INVENTORY)

        result = self._feed_one_level(inventory)

        # handle popup
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(GOTO_SALVAGE):
                logger.info("Enhance page exited")
                break
            if interval.reached() and not self.appear(GOTO_SALVAGE):
                logger.info(f'enhance -> {CLOSE}')
                self.device.click(CLOSE)
                interval.reset()
                continue

        return result
