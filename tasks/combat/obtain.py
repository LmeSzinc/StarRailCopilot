import re

from module.base.timer import Timer
from module.exception import ScriptError
from module.logger import logger
from module.ocr.ocr import Digit
from tasks.combat.assets.assets_combat_obtain import *
from tasks.combat.assets.assets_combat_prepare import COMBAT_PREPARE
from tasks.dungeon.keywords import DungeonList
from tasks.planner.keywords import ITEM_CLASSES, KEYWORDS_ITEM_CURRENCY
from tasks.planner.model import ObtainedAmmount, PlannerMixin
from tasks.planner.scan import OcrItemName


class OcrItemAmount(Digit):
    def format_result(self, result):
        res = re.split(r'[:：;；]', result, maxsplit=1)
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

    def _obtain_enter(self, entry, appear_button, skip_first_screenshot=True):
        """
        Args:
            entry: Item entry
            appear_button:
            skip_first_screenshot:

        Pages:
            in: COMBAT_PREPARE
            out: ITEM_CLOSE
        """
        logger.info(f'Obtain enter {entry}')
        self.interval_clear(appear_button)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(ITEM_CLOSE):
                break
            if self.appear(appear_button, interval=2):
                self.device.click(entry)
                self.interval_reset(appear_button)
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

    def _obtain_close(self, check_button, skip_first_screenshot=True):
        """
        Args:
            check_button:
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

            if not self.appear(ITEM_CLOSE):
                if callable(check_button):
                    if check_button():
                        break
                else:
                    if self.appear(check_button):
                        break
            if self.appear_then_click(ITEM_CLOSE, interval=2):
                continue

    @staticmethod
    def _obtain_get_entry(dungeon: DungeonList, index: int = 1, prev: ObtainedAmmount = None, start: int = 0):
        """
        Args:
            dungeon: Current dungeon
            index: 1 to 3, index to check
            prev: Previous item checked

        Returns:
            int: Item entry index, or None if no more check needed
        """
        if (index > 1 and prev is None) or (index <= 1 and prev is not None):
            raise ScriptError(f'_obtain_get_entry: index and prev must be set together, index={index}, prev={prev}')

        if index > 3:
            return None

        def may_obtain_one():
            if prev is None:
                if start:
                    return 1 + start
                else:
                    return 1
            else:
                return None

        def may_obtain_multi():
            if prev is None:
                if start:
                    return 1 + start
                else:
                    return 1
            # End at the item with the lowest rarity
            if prev.item.is_rarity_green:
                return None
            # End at credict
            if prev.item == KEYWORDS_ITEM_CURRENCY.Credit:
                return None
            if start:
                return index + start
            else:
                return index

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
        dic_entry = {
            1: OBTAIN_1,
            2: OBTAIN_2,
            3: OBTAIN_3,
            4: OBTAIN_4,
        }

        self._find_may_obtain()

        trailblaze_exp = False
        for _ in range(5):
            if not trailblaze_exp and self.appear(OBTAIN_TRAILBLAZE_EXP):
                trailblaze_exp = True
            logger.attr('trailblaze_exp', trailblaze_exp)

            entry_index = self._obtain_get_entry(dungeon, index=index, prev=prev, start=int(trailblaze_exp))
            if entry_index is None:
                logger.info('Obtain get end')
                break
            try:
                entry = dic_entry[entry_index]
            except KeyError:
                logger.error(f'No obtain entry for {entry_index}')
                break

            self._obtain_enter(entry, appear_button=COMBAT_PREPARE)
            item = self._obtain_parse()
            if item is not None:
                if item.item == KEYWORDS_ITEM_CURRENCY.Trailblaze_EXP:
                    logger.warning('Trailblaze_EXP is in obtain list, OBTAIN_TRAILBLAZE_EXP may need to verify')
                    index += 1
                    prev = item
                else:
                    items.append(item)
                    index += 1
                    prev = item
            else:
                index += 1
            self._obtain_close(check_button=MAY_OBTAIN)

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
        with self.config.multi_set():
            self.planner_write()
            # Sync to dashboard
            for item in items:
                if item.item.name == 'Credit':
                    self.config.stored.Credit.value = item.value

        return items

    def obtained_is_full(self, dungeon: DungeonList | None, wave_done=0, obtain_get=True) -> bool:
        if dungeon is None:
            self.obtain_frequent_check = False
            return False
        row = self.planner.row_come_from_dungeon(dungeon)
        if row is None:
            self.obtain_frequent_check = False
            return False

        # Update
        if obtain_get:
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
        approaching = row.is_approaching_total(wave_done)
        logger.attr('is_approaching_total', approaching)
        self.obtain_frequent_check = approaching
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
                OBTAIN_4.load_offset(MAY_OBTAIN)
                return True


if __name__ == '__main__':
    self = CombatObtain('src')
    self.device.screenshot()
    self.obtain_get()
