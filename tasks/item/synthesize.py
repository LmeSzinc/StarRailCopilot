import cv2
import numpy as np

from module.base.timer import Timer
from module.base.utils import color_similarity_2d, crop, image_size
from module.logger import logger
from module.ocr.ocr import Ocr
from tasks.base.page import page_synthesize
from tasks.combat.obtain import CombatObtain
from tasks.item.assets.assets_item_synthesize import *
from tasks.planner.keywords import ITEM_CLASSES
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
        image = self.image_crop(button)
        image = cv2.GaussianBlur(image, (3, 3), 0)
        x2, y2 = image_size(image)
        y1 = y2 - int(y2 // 4)
        image = crop(image, (0, y1, x2, y2))
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

    def synthesize_get_item(self):
        ocr = SynthesizeItemName(ITEM_NAME)
        item = ocr.matched_single_line(self.device.image, keyword_classes=ITEM_CLASSES)
        if item is None:
            logger.warning('synthesize_get_item: Unknown item name')
            return None

        return item


if __name__ == '__main__':
    self = Synthesize('src')
    self.device.screenshot()
    self.synthesize_obtain_get()
