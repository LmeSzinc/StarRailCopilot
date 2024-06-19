import cv2
import numpy as np
from scipy import signal

from module.base.base import ModuleBase
from module.base.button import ButtonWrapper
from module.base.decorator import cached_property, del_cached_property
from module.base.timer import Timer
from module.base.utils import Lines, area_center, area_offset, color_similarity_2d
from module.exception import ScriptError
from module.logger import logger


def xywh2xyxy(area):
    """
    Convert (x, y, width, height) to (x1, y1, x2, y2)
    """
    x, y, w, h = area
    return x, y, x + w, y + h


def xyxy2xywh(area):
    """
    Convert (x1, y1, x2, y2) to (x, y, width, height)
    """
    x1, y1, x2, y2 = area
    return min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)


class InventoryItem:
    def __init__(self, main: ModuleBase, loca: tuple[int, int], point: tuple[int, int]):
        self.main = main
        self.loca = loca
        self.point = point

    def __str__(self):
        return f'Item({self.loca})'

    __repr__ = __str__

    def crop(self, area, copy=False):
        area = area_offset(area, offset=self.point)
        return self.main.image_crop(area, copy=copy)

    @cached_property
    def button(self):
        area = area_offset((-40, -20, 40, 20), offset=self.point)
        return area

    @cached_property
    def is_selected(self):
        image = self.crop((-60, -100, 60, 40))
        image = color_similarity_2d(image, (255, 255, 255))
        param = {
            'height': 160,
        }
        hori = cv2.reduce(image, 1, cv2.REDUCE_AVG).flatten()
        peaks, _ = signal.find_peaks(hori, **param)
        if len(peaks) != 2:
            return False
        vert = cv2.reduce(image, 0, cv2.REDUCE_AVG).flatten()
        peaks, _ = signal.find_peaks(vert, **param)
        if len(peaks) != 2:
            return False
        return True


class InventoryManager:
    GRID_DELTA = (104, 124)

    ERROR_LINES_TOLERANCE = (-10, 10)
    COINCIDENT_POINT_ENCOURAGE_DISTANCE = 1.

    def __init__(self, main: ModuleBase, inventory: ButtonWrapper):
        """
        max_count: expected max count of this inventory page
        """
        self.main = main
        self.inventory = inventory
        self.items: dict[tuple[int, int], InventoryItem] = {}
        self.selected: InventoryItem | None = None

    def mid_cleanse(self, mids, mid_diff_range, edge_range):
        """
        Args:
            mids:
            mid_diff_range:
            edge_range:

        Returns:

        """
        count = len(mids)
        if count == 1:
            return mids
        elif count == 2:
            # Only one row, [173.5 175. ]
            mid_diff_mean = np.mean(mid_diff_range)
            diff = max(mids) - min(mids)
            if diff < mid_diff_mean * 0.3:
                return np.mean(mids).reshape((1,))
            # Double rows
            return mids
        # print(mids)
        encourage = self.COINCIDENT_POINT_ENCOURAGE_DISTANCE ** 2

        # Drawing lines
        def iter_lines():
            for index, mid in enumerate(mids):
                for n in range(self.ERROR_LINES_TOLERANCE[0], self.ERROR_LINES_TOLERANCE[1] + 1):
                    theta = np.arctan(index + n)
                    rho = mid * np.cos(theta)
                    yield [rho, theta]

        def coincident_point_value(point):
            """Value that measures how close a point to the coincident point. The smaller the better.
            Coincident point may be many.
            Use an activation function to encourage a group of coincident lines and ignore wrong lines.
            """
            x, y = point
            # Do not use:
            # distance = coincident.distance_to_point(point)
            distance = np.abs(x - coincident.get_x(y))
            # print((distance * 1).astype(int).reshape(len(mids), np.diff(self.config.ERROR_LINES_TOLERANCE)[0]+1))

            # Activation function
            # distance = 1 / (1 + np.exp(16 / distance - distance))
            distance = 1 / (1 + np.exp(encourage / distance) / distance)
            distance = np.sum(distance)
            return distance

        # Fitting mid
        coincident = Lines(np.vstack(list(iter_lines())), is_horizontal=False)
        coincident_point_range = (
            (
                -abs(self.ERROR_LINES_TOLERANCE[0]) * mid_diff_range[1] + edge_range[0],
                abs(self.ERROR_LINES_TOLERANCE[1]) * mid_diff_range[1] + edge_range[1]
            ),
            mid_diff_range
        )
        from scipy import optimize
        coincident_point = optimize.brute(coincident_point_value, coincident_point_range)
        # print(coincident_point)

        # Filling mid
        left, right = edge_range
        mids = np.arange(-25, 25) * coincident_point[1] + coincident_point[0]
        mids = mids[(mids > left) & (mids < right)]
        # print(mids)
        return mids

    def update(self):
        image = self.main.image_crop(self.inventory, copy=False)
        image = color_similarity_2d(image, color=(252, 200, 109))

        # Search rarity stars
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel, dst=image)
        # image_star = cv2.inRange(image, 221, 255)
        # Close rarity stars as item
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 3))
        cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel, dst=image)
        image_item = cv2.inRange(image, 221, 255)

        # from PIL import Image
        # Image.fromarray(image_item).show()

        def iter_area(im):
            # Iter matched area from given image
            contours, _ = cv2.findContours(im, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            for cont in contours:
                rect = cv2.boundingRect(cv2.convexHull(cont).astype(np.float32))
                # width < 5stars and height < 1star
                if not (65 > rect[2] >= 5 and 10 > rect[3]):
                    continue
                rect = xywh2xyxy(rect)
                rect = area_center(rect)
                yield rect

        area_item = list(iter_area(image_item))

        # Re-generate a correct xy array
        points = np.array(area_item)
        points += self.inventory.area[:2]
        area = self.inventory.area
        x_list = np.unique(np.sort(points[:, 0]))
        y_list = np.unique(np.sort(points[:, 1]))
        # print(x_list)
        # print(y_list)
        x_list = self.mid_cleanse(
            x_list,
            mid_diff_range=(self.GRID_DELTA[0] - 3, self.GRID_DELTA[0] + 3),
            edge_range=(area[0], area[2])
        )
        y_list = self.mid_cleanse(
            y_list,
            mid_diff_range=(self.GRID_DELTA[1] - 3, self.GRID_DELTA[1] + 3),
            edge_range=(area[1], area[3])
        )
        # print(x_list)
        # print(y_list)

        def is_near_existing(p):
            diff = np.linalg.norm(points - p, axis=1)
            return np.any(diff < 3)

        def iter_items():
            y_max = -1
            for y in y_list:
                for x in x_list:
                    if is_near_existing((x, y)):
                        y_max = y
                        break
            for yi, y in enumerate(y_list):
                if y < y_max:
                    # Fill items
                    for xi, x in enumerate(x_list):
                        yield InventoryItem(main=self.main, loca=(xi, yi), point=(int(x), int(y)))
                elif y == y_max:
                    # Fill until the last item
                    x_max = -1
                    for xi, x in enumerate(x_list):
                        if is_near_existing((x, y)):
                            x_max = xi
                    for xi, x in enumerate(x_list):
                        if xi <= x_max:
                            yield InventoryItem(main=self.main, loca=(xi, yi), point=(int(x), int(y)))
                else:
                    break

        # Re-generate items
        self.items = {}
        selected = []
        for item in iter_items():
            self.items[item.loca] = item
            if item.is_selected:
                selected.append(item)

        # Check selected
        self.selected = None
        count = len(selected)
        if count == 0:
            # logger.warning('Inventory has no item selected')
            pass
        elif count > 1:
            logger.warning(f'Inventory has multiple items selected: {selected}')
            self.selected = selected[0]
        else:
            self.selected = selected[0]

        logger.info(f'Inventory: {len(self.items)} items, selected {self.selected}')

    def get_row_first(self, row=1, first=0) -> InventoryItem | None:
        """
        Get the first item of the next row

        Args:
            row: 1 for next row, -1 for prev row
            first: 0 for the first_item
        """
        if self.selected == None:
            return None
        loca = self.selected.loca
        loca = (first, loca[1] + row)
        try:
            return self.items[loca]
        except KeyError:
            return None

    def get_right(self) -> InventoryItem | None:
        """
        Get the right item of the selected
        """
        if self.selected == None:
            return None
        loca = self.selected.loca
        loca = (loca[0] + 1, loca[1])
        try:
            return self.items[loca]
        except KeyError:
            return None

    def get_first(self) -> InventoryItem | None:
        """
        Get the first item of inventory
        """
        try:
            return self.items[(0, 0)]
        except KeyError:
            return None

    def select(self, item, skip_first_screenshot=True):
        logger.info(f'Inventory select {item}')
        if isinstance(item, InventoryItem):
            pass
        else:
            try:
                item = self.items[item]
            except KeyError:
                raise ScriptError(f'Inventory select {item} but is not in current items')

        interval = Timer(2, count=6)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.main.device.screenshot()

            # End
            del_cached_property(item, 'is_selected')
            if item.is_selected:
                logger.info('Inventory item selected')
                break
            # Click
            if interval.reached():
                self.main.device.click(item)
                interval.reset()

        self.update()

    def wait_selected(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot:

        Returns:
            bool: If success
        """
        timeout = Timer(2, count=6).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.main.device.screenshot()

            self.update()
            if self.selected is not None:
                return True
            if timeout.reached():
                logger.warning('Wait inventory selected timeout')
                return False
