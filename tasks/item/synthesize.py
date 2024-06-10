import cv2
import numpy as np

from module.base.decorator import cached_property
from module.base.timer import Timer
from module.base.utils import SelectedGrids, color_similarity_2d, crop, image_size
from module.exception import ScriptError
from module.logger import logger
from module.ocr.ocr import Ocr
from tasks.base.page import page_synthesize
from tasks.combat.obtain import CombatObtain
from tasks.item.assets.assets_item_synthesize import *
from tasks.item.inventory import InventoryManager
from tasks.planner.keywords import ITEM_CLASSES, ItemCalyx, ItemTrace
from tasks.planner.keywords.classes import ItemBase
from tasks.planner.model import ObtainedAmmount
from tasks.planner.scan import OcrItemName

RARITY_COLOR = {
    'green': (68, 127, 124),
    'blue': (76, 124, 191),
    'purple': (141, 97, 203),
}


def image_color_count(image, color, threshold=221):
    mask = color_similarity_2d(image, color=color)
    cv2.inRange(mask, threshold, 255, dst=mask)
    sum_ = cv2.countNonZero(mask)
    return sum_


class WhiteStrip(Ocr):
    def pre_process(self, image):
        mask = color_similarity_2d(image, color=(255, 255, 255))
        mask = cv2.inRange(mask, 180, 255, dst=mask)

        mask = np.mean(mask, axis=0)
        point = np.array(cv2.findNonZero(mask))[:, 0, 1]
        x1, x2 = point.min(), point.max()

        _, y = image_size(image)
        image = crop(image, (x1 - 5, 0, x2 + 5, y), copy=False)
        return image


class SynthesizeItemName(OcrItemName, WhiteStrip):
    pass


class SynthesizeInventoryManager(InventoryManager):
    @cached_property
    def dic_item_index(self):
        """
        Index of items in synthesize inventory.
        Basically ItemTrace then ItemCalyx, but high rarity items first

        Returns:
            dict: Key: item name, Value: index starting from 1
        """
        data = {}
        index = 0
        items = SelectedGrids(ItemBase.instances.values()).select(is_ItemTrace=True)
        items.create_index('item_group')
        for item_group in items.indexes.values():
            for item in item_group[::-1]:
                index += 1
                data[item.name] = index
        items = SelectedGrids(ItemBase.instances.values()).select(is_ItemCalyx=True)
        items.create_index('item_group')
        for item_group in items.indexes.values():
            for item in item_group[::-1]:
                index += 1
                data[item.name] = index
        return data

    def is_item_below(self, item1: ItemBase, item2: ItemBase) -> bool:
        """
        If item2 is on the right or below item1
        """
        try:
            id1 = self.dic_item_index[item1.name]
            id2 = self.dic_item_index[item2.name]
        except KeyError:
            raise ScriptError(f'is_item_below: {item1} {item2} not in SynthesizeInventoryManager')
        return id2 > id1


class Synthesize(CombatObtain):
    def item_get_rarity(self, button) -> str | None:
        """
        Args:
            button:

        Returns:
            str: Rarity color or None if no match

        Pages:
            in: page_synthesize
        """
        image = self.image_crop(button, copy=False)
        image = cv2.GaussianBlur(image, (3, 3), 0)
        x2, y2 = image_size(image)
        y1 = y2 - int(y2 // 4)
        image = crop(image, (0, y1, x2, y2), copy=False)
        # self.device.image_show(image)
        # print(image.shape)

        # Must contain 30% target color at icon bottom
        minimum = x2 * (y2 - y1) * 0.3
        for rarity, color in RARITY_COLOR.items():
            count = image_color_count(image, color=color, threshold=221)
            # print(rarity, count, minimum)
            if count > minimum:
                return rarity

        return None

    def item_get_rarity_retry(self, button, skip_first_screenshot=True) -> str | None:
        timeout = Timer(1, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            current = self.item_get_rarity(button)
            logger.attr('SynthesizeRarity', current)
            if current is not None:
                return current
            if timeout.reached():
                logger.warning(f'item_get_rarity_retry timeout')
                return None

    def synthesize_rarity_set(self, rarity: str, skip_first_screenshot=True) -> bool:
        """
        Args:
            rarity: "green" or "blue"
                note that rarity is the one you consume to synthesize
            skip_first_screenshot:

        Returns:
            bool: If switched

        Pages:
            in: page_synthesize
        """
        logger.info(f'item_synthesize_rarity_set: {rarity}')

        switched = False
        self.interval_clear(page_synthesize.check_button)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            current = self.item_get_rarity(ENTRY_ITEM_FROM)
            logger.attr('SynthesizeRarity', current)
            if current is not None and current == rarity:
                break

            # Click
            if self.ui_page_appear(page_synthesize, interval=2):
                self.device.click(SWITCH_RARITY)
                switched = True
                continue

        return switched

    def synthesize_rarity_reset(self, skip_first_screenshot=True):
        """
        Reset rarity switch, so current item will pin on the first row

        Returns:
            bool: If success
        """
        logger.hr('synthesize rarity reset')
        current = self.item_get_rarity_retry(ENTRY_ITEM_FROM)
        if current == 'blue':
            r1, r2 = 'green', 'blue'
        elif current == 'green':
            r1, r2 = 'blue', 'green'
        else:
            logger.error(f'item_synthesize_rarity_reset: Unknown current rarity {current}')
            return False

        self.synthesize_rarity_set(r1, skip_first_screenshot=skip_first_screenshot)
        self.synthesize_rarity_set(r2, skip_first_screenshot=True)
        return True

    def synthesize_obtain_get(self) -> list[ObtainedAmmount]:
        """
        Update item amount from synthesize page
        """
        logger.hr('Synthesize obtain get', level=2)
        items = []

        def obtain_end():
            return self.item_get_rarity(ENTRY_ITEM_FROM) is not None

        # Purple
        self.synthesize_rarity_set('blue')
        self._obtain_enter(ENTRY_ITEM_TO, appear_button=page_synthesize.check_button)
        item = self._obtain_parse()
        if item is not None:
            items.append(item)
        self._obtain_close(check_button=obtain_end)
        # Blue
        self._obtain_enter(ENTRY_ITEM_FROM, appear_button=page_synthesize.check_button)
        item = self._obtain_parse()
        if item is not None:
            items.append(item)
        self._obtain_close(check_button=obtain_end)
        # Green
        self.synthesize_rarity_set('green')
        self._obtain_enter(ENTRY_ITEM_FROM, appear_button=page_synthesize.check_button)
        item = self._obtain_parse()
        if item is not None:
            items.append(item)
        self._obtain_close(check_button=obtain_end)

        logger.hr('Obtained Result')
        for item in items:
            # Pretend everything is full
            # item.value += 1000
            logger.info(f'Obtained item: {item.item.name}, {item.value}')
        """
        <<< OBTAIN GET RESULT >>>                   
        ItemAmount: Arrow_of_the_Starchaser, 15     
        ItemAmount: Arrow_of_the_Demon_Slayer, 68   
        ItemAmount: Arrow_of_the_Beast_Hunter, 85   
        """
        self.planner.load_obtained_amount(items)
        self.planner_write()
        return items

    def synthesize_get_item(self) -> ItemBase | None:
        ocr = SynthesizeItemName(ITEM_NAME)
        item = ocr.matched_single_line(self.device.image, keyword_classes=ITEM_CLASSES)
        if item is None:
            logger.warning('synthesize_get_item: Unknown item name')
            return None

        return item

    @cached_property
    def synthesize_inventory(self):
        return SynthesizeInventoryManager(main=self, inventory=SYNTHESIZE_INVENTORY)

    def synthesize_inventory_select(self, item: ItemTrace | ItemCalyx | str):
        """
        Select item from inventory list.
        Inventory list must be at top be fore selecting.

        This method is kind of a magic to lower maintenance cost
        by doing OCR on item names instead of matching item templates.

        - Iter first item of each row
        - If current item index > target item index, switch back to prev row and iter prev row
        - If item matches or item group matches, stop
        """
        logger.hr('Synthesize select', level=1)
        logger.info(f'Synthesize select {item}')
        if isinstance(item, str):
            item = ItemBase.find(item)
        if not isinstance(item, (ItemTrace, ItemCalyx)):
            raise ScriptError(f'synthesize_inventory_select: '
                              f'Trying to select item {item} but it is not an ItemTrace or ItemCalyx object')

        inv = self.synthesize_inventory
        inv.update()
        first = inv.get_first()
        if first.is_selected:
            logger.info('first item selected')
        else:
            inv.select(first)

        logger.hr('Synthesize select view', level=2)
        switch_row = True
        while 1:
            # End
            current = self.synthesize_get_item()
            if current == item:
                logger.info('Selected at target item')
                return True
            if current.item_group == item.item_group:
                logger.info('Selected at target item group')
                return True
            # Switch rows
            if switch_row and inv.is_item_below(current, item):
                # Reached end, reset rarity to set current item at top
                next_row = inv.get_row_first(row=1)
                if next_row is None:
                    if inv.selected.loca[1] >= 3:
                        logger.info('Reached inventory view end, reset view')
                        self.synthesize_rarity_reset()
                        inv.wait_selected()
                        logger.hr('Synthesize select view', level=2)
                        continue
                    else:
                        logger.info('Reached inventory list end, no more rows')
                        switch_row = False
                        logger.hr('Synthesize select row', level=2)
                else:
                    logger.info('Item below current, select next row')
                    inv.select(next_row)
                    continue
            # Over switched, target item is at prev row
            elif switch_row:
                logger.info('Item above current, stop switch_row')
                switch_row = False
                logger.hr('Synthesize select row', level=2)
                prev2 = inv.get_row_first(row=-1, first=1)
                if prev2 is None:
                    logger.error(f'Current selected item {inv.selected} has not prev2')
                else:
                    inv.select(prev2)
                continue
            # switch_row = False
            if not switch_row:
                right = inv.get_right()
                if right is None:
                    logger.error('No target item, inventory ended')
                    return False
                else:
                    inv.select(right)
                    continue
            else:
                logger.error(f'Unexpected switch_row={switch_row} during loop')
                return False



if __name__ == '__main__':
    self = Synthesize('src')
    self.device.screenshot()
    self.synthesize_obtain_get()
