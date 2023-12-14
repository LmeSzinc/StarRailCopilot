import time

import cv2
import numpy as np
from scipy import signal
from scipy.cluster.vq import kmeans

from module.base.base import ModuleBase
from module.base.decorator import cached_property
from module.base.timer import Timer
from module.base.utils import area_offset, crop, rgb2gray, color_similarity_2d, area_pad, float2str
from module.logger import logger
from module.ocr.ocr import Ocr, DigitCounter, Digit
from tasks.item.assets.assets_item_inventory import *


class Item:
    def __init__(self, position, icon_area, data_area, image):
        self.position = position
        self.icon_area = icon_area
        self.data_area = data_area
        self.full_area = (icon_area[0], icon_area[1], data_area[2], data_area[3])
        self.button = icon_area
        self.image = image
        self.name = "Unknown Item"

    def __str__(self):
        row, col = self.position
        return f"{self.name} ({row}-{col})"

    def __repr__(self):
        return self.__str__()

    @cached_property
    def icon_image(self):
        x1, y1, x2, y2 = self.icon_area
        x1, y2, x2, y3 = self.data_area
        return crop(self.image, (x1 - x1, y1 - y1, x2 - x1, y2 - y1))

    @cached_property
    def data_image(self):
        # Since item image won't change after cropped, the data area also won't change.
        # So be careful when use in detecting something that will change after recognized
        x1, y1, x2, y2 = self.icon_area
        x1, y2, x2, y3 = self.data_area
        return crop(self.image, (x1 - x1, y2 - y1, x2 - x1, y3 - y1))

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

    def is_item_stackable(self) -> bool:
        ocr = ItemDataOcr(self)
        return '/' in ocr.ocr_single_line(self.data_image, direct_ocr=True)

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


def group_by_distance_interval(lines: np.ndarray, interval: tuple[int, int], expect_num: int = 1):
    """
    group sorted lines by distance interval.

    Examples:
        In ndarray [0, 60, 95, 105, 140] and interval = (90, 110),
        (0, 95, 105) will be grouped together because 0 + 90 < 95 < 0 + 110 and so does 105

    Returns:
        generator of ndarray of grouped lines
    """
    left, right = interval
    matched_line = set()
    for line in lines:
        if line in matched_line:
            continue
        matches = lines[(line + left <= lines) & (lines <= line + right)]
        if len(matches) < expect_num:
            continue
        for match in lines[(line <= lines) & (lines <= matches[-1])]:
            matched_line.add(match)
        if len(matches) > expect_num:
            matches = np.sort(kmeans(matches.astype(np.float64), expect_num)[0].astype(np.int64))
        yield np.append(line, matches)


class Inventory:
    def __init__(self, inventory: ButtonWrapper, max_count: int):
        """
        max_count: expected max count of this inventory page
        """
        self.inventory = inventory
        self.row_recognized = 0
        self.max_count = max_count

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
            if count == self.max_count:
                logger.info(f'Reach page max item count, {self.inventory} is already stable')
                break
            if last_count == count:
                if timer.reached():
                    logger.info(f'Item count is stable at one timer interval, {self.inventory} is already stable')
                    break
            else:
                last_count = count
                timer.reset()

    def recognize_single_page_items(self, main: ModuleBase, hough_th=115, theta_th=0.005, edge_th=5) -> list[Item]:
        area = self.inventory.area
        image = crop(main.device.image, area)
        start_time = time.time()

        star_mask = color_similarity_2d(image, color=(252, 200, 109))
        _, star_mask = cv2.threshold(star_mask, 210, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        star_mask = cv2.morphologyEx(star_mask, cv2.MORPH_OPEN, kernel)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 3))
        star_mask = cv2.morphologyEx(star_mask, cv2.MORPH_CLOSE, kernel)

        star_mask = ~star_mask
        image = rgb2gray(image)

        # col
        peaks, _ = signal.find_peaks(image.ravel(), height=(90, 200), prominence=10, distance=5, wlen=500)
        peak_col_image = np.zeros(image.shape[0] * image.shape[1], dtype=np.uint8)
        peak_col_image[peaks] = 255
        peak_col_image = peak_col_image.reshape(image.shape)
        # row
        peaks, _ = signal.find_peaks(image.T.ravel(), height=(80, 180), prominence=10, distance=5, wlen=500)
        peak_row_image = np.zeros(image.shape[0] * image.shape[1], dtype=np.uint8)
        peak_row_image[peaks] = 255
        peak_row_image = peak_row_image.reshape(image.T.shape).T

        peak_image = cv2.bitwise_and(cv2.add(peak_row_image, peak_col_image), star_mask)

        results = cv2.HoughLines(peak_image, 1, np.pi / 180, hough_th)
        if results is None:
            logger.warning(f"Can not find any lines at {self.inventory}")
            return []
        lines = results[:, 0, :]
        col_bounds = [abs(int(rho)) for rho, theta in lines if not theta]
        row_bounds = [abs(int(rho)) for rho, theta in lines if
                      (np.deg2rad(90 - theta_th) < theta < np.deg2rad(90 + theta_th))]

        col_bounds = np.sort(np.array(col_bounds))
        row_bounds = np.sort(np.array(row_bounds))

        row_bounds = row_bounds[np.append(np.ones((1,), bool), np.abs(np.diff(row_bounds) > edge_th))]
        col_bounds = col_bounds[np.append(np.ones((1,), bool), np.abs(np.diff(col_bounds) > edge_th))]

        def get_items():
            row_recognized = 0
            for row, (y1, y2, y3) in enumerate(group_by_distance_interval(row_bounds, (80, 115), 2)):
                for col, (x1, x2) in enumerate(group_by_distance_interval(col_bounds, (85, 100))):
                    yield Item((row_recognized + 1, col + 1),
                               (x1 + area[0], y1 + area[1], x2 + area[0], y2 + area[1]),
                               (x1 + area[0], y2 + area[1], x2 + area[0], y3 + area[1]),
                               crop(main.device.image, (x1 + area[0], y1 + area[1], x2 + area[0], y3 + area[1])))
                row_recognized += 1

        items = [item for item in get_items()]
        logger.attr(name='%s %ss' % (self.inventory.name, float2str(time.time() - start_time)),
                    text=f"{len(items)} item recognized")
        return items
