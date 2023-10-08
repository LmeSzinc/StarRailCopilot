import cv2
import numpy as np

from module.base.base import ModuleBase
from module.base.timer import Timer
from module.base.utils import area_offset, crop, rgb2gray, color_similarity_2d, area_pad
from module.logger import logger
from module.ocr.ocr import Ocr, DigitCounter, Digit
from tasks.item.assets.assets_item_inventory import *


class Item:
    def __init__(self, position, icon_area, data_area):
        self.position = position
        self.icon_area = icon_area
        self.data_area = data_area
        self.full_area = (icon_area[0], icon_area[1], data_area[2], data_area[3])
        self.button = icon_area
        self.name = "Unknown Item"

    def __str__(self):
        row, col = self.position
        return f"{self.name} ({row}-{col})"

    def __repr__(self):
        return self.__str__()

    def get_minus_button(self):
        x1, y1, _, _ = self.button
        return x1, y1, x1 + 10, y1 + 10

    def get_rarity(self, main: ModuleBase):
        rarity_colors = [  # background colors of item
            (115, 118, 125),
            (60, 117, 121),
            (62, 88, 144),
            (127, 88, 181),
            (170, 128, 94)
        ]
        for rarity, color in enumerate(rarity_colors):
            if main.image_color_count(self.icon_area, color, count=1000):
                return rarity + 1
        return 0

    def get_data_count(self, main: ModuleBase) -> bool:
        ocr = ItemDataDigit(self)
        return ocr.ocr_single_line(main.device.image)

    def is_item_selected(self, main: ModuleBase) -> bool:
        # white border
        return main.image_color_count(area_pad(self.full_area, -10), (255, 255, 255), count=1000)

    def is_item_locked(self, main: ModuleBase) -> bool:
        ITEM_LOCK.matched_button.search = self.icon_area
        return main.appear(ITEM_LOCK)

    def is_item_stackable(self, main: ModuleBase) -> bool:
        ocr = ItemDataOcr(self)
        return '/' in ocr.ocr_single_line(main.device.image)

    def get_stackable_item_count(self, main: ModuleBase) -> tuple[int, int, int]:
        counter = ItemDataCounter(self)
        return counter.ocr_single_line(main.device.image)


class ItemDataOcr(Ocr):
    def __init__(self, item: Item):
        ITEM_DATA.matched_button.area = item.data_area
        super().__init__(ITEM_DATA)

    def after_process(self, result):
        result = result.replace(':', '')
        return result


class ItemDataDigit(Digit):
    def __init__(self, item: Item):
        ITEM_DATA.matched_button.area = item.data_area
        super().__init__(ITEM_DATA)


class ItemDataCounter(DigitCounter):
    def __init__(self, item: Item):
        # This is used only when the item is selected. Selected item will enlarge a little bit.
        ITEM_DATA.matched_button.area = area_offset(item.data_area, (0, 3))
        super().__init__(ITEM_DATA)

    def after_process(self, result):
        result = result.replace(':', '')
        return result


class Inventory:
    def __init__(self, inventory: ButtonWrapper):
        self.inventory = inventory
        self.row_recognized = 0

    def count_items(self, main: ModuleBase):
        image = crop(main.device.image, self.inventory.area)
        image = color_similarity_2d(image, color=(252, 200, 109))

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 3))
        image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)

        _, image = cv2.threshold(image, 230, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        count = 0
        for index, cont in enumerate(contours):
            rect = cv2.boundingRect(cv2.convexHull(cont).astype(np.float32))
            if not (65 > rect[2] >= 20 and 10 > rect[3]):
                continue
            count += 1
        return count

    def wait_until_inventory_stable(self, main: ModuleBase, timer=Timer(0.3, count=1), timeout=Timer(5, count=10)):
        logger.info(f'Wait until stable: {self.inventory}')
        last_count = self.count_items(main)
        timer.reset()
        timeout.reset()
        while 1:
            main.device.screenshot()

            if timeout.reached():
                logger.warning(f'wait_until_inventory_stable({self.inventory}) timeout')
                break

            count = self.count_items(main)
            if last_count == count:
                if timer.reached():
                    logger.info(f'{self.inventory} stabled')
                    break
            else:
                last_count = count
                timer.reset()

    def recognize_single_page_items(self, main: ModuleBase, hough_th=120, theta_th=0.005, edge_th=5) -> list[Item]:
        area = self.inventory.area
        image = crop(main.device.image, area)

        image = rgb2gray(image)
        _, image = cv2.threshold(image, 60, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 2))
        image = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 2))
        image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
        image = cv2.Canny(image, 50, 60, apertureSize=3)

        results = cv2.HoughLines(image, 1, np.pi / 180, hough_th)
        if results is None:
            logger.warning(f"Can not find any lines at {self.inventory}")
            return []
        lines = [(rho, theta) for rho, theta in results[:, 0, :]]
        row_bounds = [
            abs(int(rho)) for rho, theta in lines if (np.deg2rad(90 - theta_th) < theta < np.deg2rad(90 + theta_th))]
        col_bounds = [abs(int(rho)) for rho, theta in lines if not theta]

        col_bounds = np.sort(np.array(col_bounds))
        row_bounds = np.sort(np.array(row_bounds))

        row_bounds = row_bounds[np.append(np.ones((1,), bool), np.abs(np.diff(row_bounds) > edge_th))]
        col_bounds = col_bounds[np.append(np.ones((1,), bool), np.abs(np.diff(col_bounds) > edge_th))]

        while abs(row_bounds[0] - row_bounds[1]) < 80:  # the size of one item icon is 96 * 90 / 86(salvage)
            row_bounds = np.delete(row_bounds, 0)

        for _ in range(len(row_bounds) % 3):
            row_bounds = np.delete(row_bounds, -1)

        for _ in range(len(col_bounds) % 2):
            col_bounds = np.delete(col_bounds, -1)

        def get_items():
            for row, (y1, y2, y3) in enumerate(row_bounds.reshape((-1, 3))):
                for col, (x1, x2) in enumerate(col_bounds.reshape((-1, 2))):
                    yield Item((self.row_recognized + 1, col + 1),
                               (x1 + area[0], y1 + area[1], x2 + area[0], y2 + area[1]),
                               (x1 + area[0], y2 + area[1], x2 + area[0], y3 + area[1]))
                self.row_recognized += 1

        items = [item for item in get_items()]

        # size should be all the same
        icon_area = [item.icon_area for item in items]
        sizes = [(x2 - x1, y2 - y1) for x1, y1, x2, y2 in icon_area]
        size, counts = np.unique(sizes, axis=0, return_counts=True)
        if len(size) == 1:
            logger.info(f"{len(items)} item recognized with uniform icon size: {size[0][0]}x{size[0][1]}")
        else:
            logger.warning(f"{len(items)} item recognized but with different icon size: {size}")
        return items
