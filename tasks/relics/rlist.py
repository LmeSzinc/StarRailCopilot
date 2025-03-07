import cv2
import numpy as np
from scipy import signal

from module.base.button import match_template
from module.base.decorator import cached_property, set_cached_property
from module.base.timer import Timer
from module.base.utils import area_offset, color_similarity_2d, point_in_area, rgb2gray
from module.logger import logger
from tasks.item.inventory import InventoryItem, InventoryManager
from tasks.relics.assets.assets_relics_rec import REC_SUBVALUE
from tasks.relics.assets.assets_relics_rlist import INVENTORY_AREA, INVENTORY_ROW4FIRST
from tasks.relics.lock import RelicLock
from tasks.relics.rec.rec import RelicRec


class RelicItem(InventoryItem):
    def crop(self, area, copy=False):
        area = area_offset(area, offset=self.point)
        # Limit in INVENTORY_AREA
        y_max = INVENTORY_AREA.area[3]
        area = (area[0], area[1], area[2], min(area[3], y_max))
        return self.main.image_crop(area, copy=copy)

    @cached_property
    def is_selected(self):
        image = self.crop((-60, -100, 60, 40))
        image = color_similarity_2d(image, (255, 255, 255))
        param = {
            'height': 160,
            # [ 10 110 114]
            'distance': 10,
        }
        # from PIL import Image
        # Image.fromarray(image, mode='L').show()

        # hori = cv2.reduce(image, 1, cv2.REDUCE_AVG).flatten()
        # peaks, _ = signal.find_peaks(hori, **param)
        # if len(peaks) != 2:
        #     return False
        vert = cv2.reduce(image, 0, cv2.REDUCE_AVG).flatten()
        # print(vert)
        peaks, _ = signal.find_peaks(vert, **param)
        # Left border and right border
        # Body of GeniusofBrilliantStars may have high peak height
        if np.any(peaks < 20) and np.any(peaks > 100):
            return True
        else:
            return False


class RelicRow4First(RelicItem):
    @cached_property
    def is_selected(self):
        image = self.crop((-60, -80, 60, 40))
        image = color_similarity_2d(image, (255, 255, 255))
        # from PIL import Image
        # Image.fromarray(image, mode='L').show()
        param = {
            'height': 160,
            # [ 10 110 114]
            'distance': 10,
        }
        vert = cv2.reduce(image, 0, cv2.REDUCE_AVG).flatten()
        # print(vert)
        peaks, _ = signal.find_peaks(vert, **param)
        # Left border and right border
        # Body of GeniusofBrilliantStars may have high peak height
        if np.any(peaks < 20) and np.any(peaks > 100):
            return True
        else:
            return False


class RelicInventoryManager(InventoryManager):
    ITEM_CLASS = RelicItem
    # Hardcode X coordinates because lock icon would cover rarity stars causing grid shifts
    CONST_X_LIST = [200, 304, 408, 512, 616, 720]

    def item_grid_size(self):
        max_x = 0
        max_y = 0
        for x, y in self.items.keys():
            if x > max_x:
                max_x = x
            if y > max_y:
                max_y = y
        return max_x + 1, max_y + 1

    def hsv_count(self, area, h=(0, 360), s=(0, 100), v=(0, 100)):
        """
        Args:
            area (tuple): upper_left_x, upper_left_y, bottom_right_x, bottom_right_y, such as (-1, -1, 1, 1).
            h (tuple): Hue.
            s (tuple): Saturation.
            v (tuple): Value.
            shape (tuple): Output image shape, (width, height).

        Returns:
            int: Number of matched pixels.
        """
        image = self.main.image_crop(area, copy=False)
        # Don't set `dst` as image_crop didn't copy
        image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        lower = (h[0] / 2, s[0] * 2.55, v[0] * 2.55)
        upper = (h[1] / 2 + 1, s[1] * 2.55 + 1, v[1] * 2.55 + 1)
        # Don't set `dst`, output image is (50, 50) but `image` is (50, 50, 3)
        image = cv2.inRange(image, lower, upper)
        count = cv2.countNonZero(image)
        return count

    def get_row4first(self):
        # 4th row is only available if there is 3rd row
        _, y = self.item_grid_size()
        if y < 3:
            logger.info('row4first no 4th row')
            return None

        # Predict position of (0, 3)
        try:
            top = self.items[(0, 2)]
        except KeyError:
            logger.warning(f'Relic inventory has 3 rows of items but (0, 2) is missing')
            return None
        point = (top.point[0], top.point[1] + self.GRID_DELTA[1])
        if not point_in_area(point, INVENTORY_ROW4FIRST.area, threshold=0):
            # Out of row4first area
            logger.info('row4first is not in area')
            return None

        # Check if rarity stars is in area
        count = self.hsv_count(INVENTORY_ROW4FIRST.area, h=(0, 60), s=(0, 100), v=(25, 100))
        if count < 100:
            logger.info('row4first not appear')
            return None

        # Product item
        loca = (top.loca[0], top.loca[1] + 1)
        item = RelicRow4First(main=self.main, loca=loca, point=point)
        # Override button
        set_cached_property(item, 'button', INVENTORY_ROW4FIRST.area)
        logger.info('row4first appear')
        return item

    def select_row4first(self, item: InventoryItem, skip_first_screenshot=True):
        logger.info(f'Inventory select {item}')

        click_interval = Timer(2, count=6)
        clicked = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.main.device.screenshot()
                item.clear_cache()

            # End
            if clicked and item.is_selected:
                logger.info('Inventory item selected')
                break
            # Click
            if click_interval.reached():
                self.main.device.click(item)
                click_interval.reset()
                clicked = True
                continue

    _substat_image = None

    def substats_watch_init(self):
        # Copy image so full screenshot can be GC later
        image = self.main.image_crop(REC_SUBVALUE, copy=False)
        image = rgb2gray(image)
        self._substat_image = image

    def substats_watch_changed(self):
        image = self.main.image_crop(REC_SUBVALUE, copy=False)
        image = rgb2gray(image)
        if match_template(image, self._substat_image, similarity=0.9):
            return False
        else:
            return True


class RelicList(RelicLock):
    @cached_property
    def relic_inventory(self):
        return RelicInventoryManager(main=self, inventory=INVENTORY_AREA)

    @cached_property
    def relic_rec(self):
        return RelicRec(lang=self.config.LANG)

    def iter_relic_from_page(self):
        inv = self.relic_inventory
        inv.wait_selected()

        logger.hr('Iter relic from page', level=2)
        self.device.click_record_clear()

        # First
        # Don't select first, selection needs to be continuous when reaching end
        # first = inv.get_first()
        # if first is None:
        #     logger.warning('No item found')
        #     return
        # elif first.is_selected:
        #     logger.info('First item selected')
        # else:
        #     logger.info('Select first item')
        #     inv.select(first)
        yield inv.selected

        while 1:
            right = inv.get_right()
            if right is None:
                down = inv.get_row_first()
                if down is None:
                    # Reached end
                    logger.info('No more relics on current page')
                    return
                else:
                    # Next row
                    self.device.click_record_clear()
                    inv.select(down)
                    yield down
            else:
                # Select right
                inv.substats_watch_init()
                # Wait until substats changed, fast yield item
                inv.select(right, early_stop=inv.substats_watch_changed)
                inv.assume_selected(right)
                yield right

    def relic_next_page(self):
        """
        Switch to next page and set first item to top
        """
        logger.hr('Relic next page', level=2)
        inv = self.relic_inventory
        inv.update()
        row4first = inv.get_row4first()
        if row4first is None:
            return False

        inv.select_row4first(row4first)
        self.relic_reset_state()
        return True

    def relic_iter(self):
        """
        Yields:
            RelicRecResult
        """
        # Select first
        inv = self.relic_inventory
        inv.update()
        first = inv.get_first()
        if first is None:
            logger.warning('No item found')
            return
        elif first.is_selected:
            logger.info('First item selected')
        else:
            logger.info('Select first item')
            inv.select(first)

        self.device.screenshot_interval_set(0.05)
        rec = self.relic_rec
        try:
            while 1:
                for _ in self.iter_relic_from_page():
                    relic = rec.rec(self.device.image)
                    # if relic is None:
                    #     self.device.image_save()
                    if relic is not None:
                        yield relic
                new_page = self.relic_next_page()
                if not new_page:
                    break
        finally:
            self.device.screenshot_interval_set()
        logger.info('Relic list end')


if __name__ == '__main__':
    self = RelicList('src')
    self.device.screenshot()
    for _ in self.relic_iter():
        pass
