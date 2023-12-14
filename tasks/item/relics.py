import math
import re
from typing import Optional

import cv2

from module.base.timer import Timer
from module.base.utils import area_offset, area_pad, crop, extract_letters, extract_white_letters
from module.logger import logger
from module.ocr.ocr import Ocr
from tasks.base.assets.assets_base_page import CLOSE
from tasks.item.assets.assets_item_relics import *
from tasks.item.assets.assets_item_relics_enhance import *
from tasks.item.assets.assets_item_relics_salvage import *
from tasks.item.assets.assets_item_ui import ORDER_ASCENDING, ORDER_DESCENDING, ITEM_PAGE_INVENTORY
from tasks.item.inventory import Item, Inventory
from tasks.item.keywords import KEYWORD_ITEM_TAB, KEYWORD_SORT_TYPE
from tasks.item.ui import ItemUI


def offset_to_sort_order_area(sort_type_button):
    return area_offset(sort_type_button.button, (200, 0))


class RelicsUI(ItemUI):
    def _is_in_salvage(self) -> bool:
        return self.appear(ORDER_ASCENDING) or self.appear(ORDER_DESCENDING)

    def salvage_exit(self, skip_first_screenshot=True):
        """
        Pages:
            in: rewards claimed
                or _is_in_salvage()
            out: GOTO_SALVAGE
        """
        interval = Timer(1)
        while 1:
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

    def _select_salvage_relic(self, skip_first_screenshot=True) -> bool:
        """
        Returns: is selected
        """
        interval = Timer(1)
        timeout = Timer(5, count=3).start()
        self.ensure_sort_type(SALVAGE_SORT_TYPE_BUTTON, KEYWORD_SORT_TYPE.Rarity)
        self.ensure_sort_order(offset_to_sort_order_area(SALVAGE_SORT_TYPE_BUTTON), "ascending")
        inventory = Inventory(SALVAGE_INVENTORY, 7 * 3)
        inventory.wait_until_inventory_stable(main=self)
        items = iter(inventory.recognize_single_page_items(main=self))

        item = next(items, None)

        while item and item.is_item_locked(main=self):
            logger.info(f"{item} locked, choose next one")
            item = next(items, None)

        if not item:
            logger.warning(f"Can not select salvageable relic")
            return False

        rarity_threshold = 5
        if self.config.AchievableQuest_Salvage_any_Relic == '4-star_or_below':
            rarity_threshold = 4
        if self.config.AchievableQuest_Salvage_any_Relic == '3-star_or_below':
            rarity_threshold = 3

        if item.get_rarity(main=self) > rarity_threshold:
            logger.warning("No relic satisfy preset rarity, can not salvage")
            return False

        while 1:  # salvage -> first relic selected
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Timeout when selecting first relic')
                self.salvage_exit()
                return False
            # The first frame entering relic page, SALVAGE is a white button as it's the default state.
            # At the second frame, SALVAGE is disabled since no items are selected.
            # So here uses the minus button on the first relic.
            if item.is_item_selected(main=self):
                logger.info(f'Relic {item} selected')
                return True
            if interval.reached() and self._is_in_salvage():
                self.device.click(item)
                interval.reset()
                continue

    def salvage_relic(self, skip_first_screenshot=True) -> bool:
        """
        Args:
            skip_first_screenshot:

        Returns:
            bool: If success

        Pages:
            in: Any
            out: page_item, GOTO_SALVAGE
        """
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

        result = self._select_salvage_relic()  # salvage -> first relic selected

        if result:
            skip_first_screenshot = True
            while 1:  # selected -> rewards claimed
                if skip_first_screenshot:
                    skip_first_screenshot = False
                else:
                    self.device.screenshot()

                if self.reward_appear():
                    logger.info("Relic salvaged")
                    break
                if self.appear_then_click(SALVAGE, interval=2):
                    continue
                if self.handle_popup_confirm():
                    continue

        self.salvage_exit()
        return result

    def _is_in_material_select(self) -> bool:
        return self.image_color_count(RELIC_SELECTION_PAGE_SORT_TYPE_BUTTON, (225, 226, 229))

    def get_exp_remain(self) -> Optional[int]:
        ocr = Ocr(ENHANCE_RELIC_EXP_OCR)
        image = crop(self.device.image, ENHANCE_RELIC_EXP_OCR.area)
        green_letters = extract_letters(image, (125, 214, 192), threshold=80)
        white_letters = extract_white_letters(image=image)

        green_letters = cv2.cvtColor(green_letters, cv2.COLOR_GRAY2RGB)
        white_letters = cv2.cvtColor(white_letters, cv2.COLOR_GRAY2RGB)
        results = ocr.ocr_multi_lines([green_letters, white_letters])
        result = "".join([text for text, rate in results])
        # for result in results:
        res = re.search(r'(?:\+(\d+))?\D*(\d+)/(\d+)', result)
        if res:
            groups = [int(s) if s else 0 for s in res.groups()]
            [added, current, total] = groups
            logger.attr(name="EXP Counter", text=f"({added}, {current}, {total})")
            current += added
            return total - current
        logger.warning(f'No digit counter found in {results}')
        return None

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
                    click_num = count_needed if count_needed > 0 else -count_needed
                    self.device.multi_click(item, click_num)
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
                if interval.reached() and self._is_in_material_select():
                    self.device.click(item)
                    interval.reset()

    def _feed_one_level(self, inventory: Inventory, skip_first_screenshot=True) -> bool:
        exp_list = [0, 100, 500, 1000, 1500]

        inventory.wait_until_inventory_stable(main=self)
        items = inventory.recognize_single_page_items(main=self)
        if not items:
            return False

        items = iter(sorted(items, key=lambda i: i.get_rarity(main=self)))
        item = next(items, None)

        added_item = 0
        slot_num = 8

        rarity_threshold = 5
        if self.config.AchievableQuest_Level_up_any_Relic_1_time == '4-star_or_below':
            rarity_threshold = 4
        if self.config.AchievableQuest_Level_up_any_Relic_1_time == '3-star_or_below':
            rarity_threshold = 3

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
            # so checking whether relic is locked is no longer necessary here
            # while inventory.is_item_locked(item):
            #     item = next(items,  None)

            if not item or item.get_rarity(main=self) > rarity_threshold:
                logger.warning("No relic satisfy preset rarity, can not salvage")
                return False

            stackable = item.is_item_stackable(main=self)
            exp_count = 0
            if stackable:
                _, remain, _ = item.get_stackable_item_count(main=self)
                exp = exp_list[item.get_rarity(main=self) - 1]
                exp_needed = self.get_exp_remain()
                if exp_needed is None:
                    return False
                if exp_needed <= 0:
                    logger.warning("Get non-positive exp_needed, can not feed one level successfully")
                    return False
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
                        item = next(items, None)
                else:
                    item = next(items, None)

            else:
                logger.warning(f"Try add item {item} failed")
                return False

    def _enhance_confirm(self, skip_first_screenshot=True):
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
            if self.appear_then_click(ENHANCE):
                continue

        # handle popup
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(ENHANCE_TAB):
                logger.info("Enhance complete")
                break
            if self.appear_then_click(ENHANCE_POPUP):
                continue

    def _select_level_up_relic(self, skip_first_screenshot=True) -> bool:
        def is_max_level(relic: Item):
            level = relic.get_data_count(main=self)
            rarity = relic.get_rarity(main=self)
            return level == rarity * 3

        # select first relic
        inventory = Inventory(ITEM_PAGE_INVENTORY, 6 * 4)
        inventory.wait_until_inventory_stable(main=self)
        items = iter(inventory.recognize_single_page_items(main=self))
        item = next(items, None)

        while item and is_max_level(item):
            logger.info(f"{item} is max level, skip")
            item = next(items, None)
        if not item:
            logger.warning("No relic can be leveled up")
            return False

        rarity_threshold = 5
        if self.config.AchievableQuest_Level_up_any_Relic_1_time == '4-star_or_below':
            rarity_threshold = 4
        if self.config.AchievableQuest_Level_up_any_Relic_1_time == '3-star_or_below':
            rarity_threshold = 3

        if item.get_rarity(main=self) > rarity_threshold:
            logger.warning("No relic satisfy preset rarity, can not be leveled up")
            return False

        interval = Timer(1)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if item.is_item_selected(main=self):
                break

            if interval.reached() and self._is_in_material_select():
                self.device.click(item)
                interval.reset()

        return True

    def level_up_relic(self, skip_first_screenshot=True) -> bool:
        logger.hr('Level up relic', level=2)
        self.item_goto(KEYWORD_ITEM_TAB.Relics, wait_until_stable=False)
        self.ensure_sort_type(RELIC_MAIN_PAGE_SORT_TYPE_BUTTON, key=KEYWORD_SORT_TYPE.Rarity)
        self.ensure_sort_order(offset_to_sort_order_area(RELIC_MAIN_PAGE_SORT_TYPE_BUTTON), "ascending")

        # select relic
        if not self._select_level_up_relic():
            return False

        # details -> enhance tab
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(ENHANCE_TAB):
                break
            if self.appear_then_click(ITEM_DETAILS):
                continue

        interval = Timer(1)
        # enhance tab -> open slots
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._is_in_material_select():
                break
            if interval.reached() and self.match_template_color(ENHANCE_TAB):
                self.device.click(ENHANCE_TAB)
                interval.reset()
                continue
            if self.appear_then_click(ENHANCE_MATERIAL_SLOTS):
                continue

        # add items
        self.ensure_sort_type(RELIC_SELECTION_PAGE_SORT_TYPE_BUTTON, KEYWORD_SORT_TYPE.Rarity)
        self.ensure_sort_order(offset_to_sort_order_area(RELIC_SELECTION_PAGE_SORT_TYPE_BUTTON), "ascending")
        inventory = Inventory(ENHANCE_INVENTORY, 7 * 4)

        result = self._feed_one_level(inventory)

        # enhance -> item page relic tab
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(GOTO_SALVAGE):
                logger.info("Enhance page exited")
                break
            if interval.reached() and self.appear(ENHANCE_MATERIAL_SLOTS):
                logger.info(f'enhance -> {CLOSE}')
                self.device.click(CLOSE)
                interval.reset()
                continue

        return result
