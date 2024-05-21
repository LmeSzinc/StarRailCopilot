import re

from module.base.timer import Timer
from module.exception import ScriptError
from module.logger import logger
from module.ocr.ocr import Digit
from tasks.combat.assets.assets_combat_obtain import *
from tasks.combat.assets.assets_combat_prepare import COMBAT_PREPARE
from tasks.dungeon.keywords import DungeonList
from tasks.planner.keywords import ITEM_CLASSES
from tasks.planner.model import ObtainedAmmount, PlannerMixin
from tasks.planner.scan import OcrItemName


class OcrItemAmount(Digit):
    def format_result(self, result):
        res = re.split(r'[:：;；]', result)
        result = res[-1]
        return super().format_result(result)


class CombatObtain(PlannerMixin):
    """
    Parse items that can be obtained from dungeon

    Pages:
        in: COMBAT_PREPARE
    """
    # False to click again when combat ends
    # True to exit and reenter to get obtained items
    obtain_frequent_check = False

    def _obtain_enter(self, entry, skip_first_screenshot=True):
        """
        Args:
            entry: Item entry
            skip_first_screenshot:

        Pages:
            in: COMBAT_PREPARE
            out: ITEM_CLOSE
        """
        logger.info(f'Obtain enter {entry}')
        self.interval_clear(COMBAT_PREPARE)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(ITEM_CLOSE):
                break
            if self.appear(COMBAT_PREPARE, interval=2):
                self.device.click(entry)
                self.interval_reset(COMBAT_PREPARE)
                continue

        # Wait animation
        timeout = Timer(1.4, count=7).start()
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.image_color_count(ITEM_NAME, color=(0, 0, 0), threshold=221, count=50):
                break
            if timeout.reached():
                logger.warning('Wait obtain item timeout')
                break

    def _obtain_close(self, skip_first_screenshot=True):
        """
        Args:
            skip_first_screenshot:

        Pages:
            in: ITEM_CLOSE
            out: COMBAT_PREPARE
        """
        logger.info(f'Obtain close')
        self.interval_clear(ITEM_CLOSE)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if not self.appear(ITEM_CLOSE) and self.appear(COMBAT_PREPARE) and self.appear(MAY_OBTAIN):
                break
            if self.appear_then_click(ITEM_CLOSE, interval=2):
                continue

    @staticmethod
    def _obtain_get_entry(dungeon: DungeonList, index: int = 1, prev: ObtainedAmmount = None):
        """
        Args:
            dungeon: Current dungeon
            index: 1 to 3, index to check
            prev: Previous item checked

        Returns:
            ButtonWrapper: Item entry, or None if no more check needed
        """
        if (index > 1 and prev is None) or (index <= 1 and prev is not None):
            raise ScriptError(f'_obtain_get_entry: index and prev must be set together, index={index}, prev={prev}')

        if index > 3:
            return None

        def may_obtain_one():
            if prev is None:
                return OBTAIN_1
            else:
                return None

        def may_obtain_multi():
            if prev is None:
                return OBTAIN_1
            # End at the item with the lowest rarity
            if prev.item.is_rarity_green:
                return None
            if index == 2:
                return OBTAIN_2
            if index == 3:
                return OBTAIN_3

        if dungeon is None:
            return may_obtain_multi()
        if dungeon.is_Echo_of_War:
            return may_obtain_one()
        if dungeon.is_Cavern_of_Corrosion:
            return None
        if dungeon.is_Stagnant_Shadow:
            return may_obtain_one()
        if dungeon.is_Calyx_Golden:
            if dungeon.is_Calyx_Golden_Treasures:
                return may_obtain_one()
            else:
                return may_obtain_multi()
        if dungeon.is_Calyx_Crimson:
            return may_obtain_multi()

        raise ScriptError(f'_obtain_get_entry: Cannot get entry from {dungeon}')

    def _obtain_parse(self) -> ObtainedAmmount | None:
        """
        Pages:
            in: ITEM_CLOSE
        """
        ocr = OcrItemName(ITEM_NAME)
        item = ocr.matched_single_line(self.device.image, keyword_classes=ITEM_CLASSES)
        ocr = OcrItemAmount(ITEM_AMOUNT)
        amount = ocr.ocr_single_line(self.device.image)

        if item is None:
            logger.warning('_obtain_parse: Unknown item name')
            return None

        # logger.info(f'ObtainedAmmount: item={item}, value={amount}')
        return ObtainedAmmount(
            item=item,
            value=amount,
        )

    def obtain_get(self, dungeon=None, skip_first_screenshot=True) -> list[ObtainedAmmount]:
        """
        Args:
            dungeon: Current dungeon,
                or None for no early stop optimization
            skip_first_screenshot:

        Returns:
            list[ObtainedAmmount]:

        Pages:
            in: COMBAT_PREPARE
            out: COMBAT_PREPARE
        """
        logger.hr('Obtain get', level=2)
        if not skip_first_screenshot:
            self.device.screenshot()

        index = 1
        prev = None
        items = []

        self._find_may_obtain()

        for _ in range(5):
            entry = self._obtain_get_entry(dungeon, index=index, prev=prev)
            if entry is None:
                logger.info('Obtain get end')
                break

            self._obtain_enter(entry)
            item = self._obtain_parse()
            if item is not None:
                items.append(item)
                index += 1
                prev = item
            self._obtain_close()

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

    def obtained_is_full(self, dungeon: DungeonList | None) -> bool:
        if dungeon is None:
            self.obtain_frequent_check = False
            return False
        row = self.planner.row_come_from_dungeon(dungeon)
        if row is None:
            self.obtain_frequent_check = False
            return False

        # Update
        self.obtain_get(dungeon)

        # Check progress
        row = self.planner.row_come_from_dungeon(dungeon)
        if row is None:
            logger.error(f'obtained_is_full: Row disappeared after obtain_get')
            self.obtain_frequent_check = False
            return False
        if not row.need_farm():
            logger.info('Planner row full')
            self.obtain_frequent_check = False
            return True

        # obtain_frequent_check
        # approaching = row.is_approaching_total()
        # logger.attr('is_approaching_total', approaching)
        # self.obtain_frequent_check = approaching
        return False

    def _find_may_obtain(self, skip_first_screenshot=True):
        logger.info('Find may obtain')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if MAY_OBTAIN.match_template(self.device.image):
                OBTAIN_1.load_offset(MAY_OBTAIN)
                OBTAIN_2.load_offset(MAY_OBTAIN)
                OBTAIN_3.load_offset(MAY_OBTAIN)
                return True


if __name__ == '__main__':
    self = CombatObtain('src')
    self.device.screenshot()
    self.obtain_get()
