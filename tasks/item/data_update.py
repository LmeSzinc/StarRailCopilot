import re

from module.base.timer import Timer
from module.logger import logger
from module.ocr.ocr import Digit, DigitCounter
from tasks.base.page import page_gacha, page_item
from tasks.item.assets.assets_item_data import OCR_DATA, OCR_RELIC
from tasks.item.assets.assets_item_gacha import OCR_SPECIAL_PASS
from tasks.item.keywords import KEYWORDS_ITEM_TAB
from tasks.item.ui import ItemUI
from tasks.planner.model import PlannerMixin


class DataDigit(Digit):
    def after_process(self, result):
        result = re.sub(r'[l|]', '1', result)
        result = re.sub(r'[oO]', '0', result)
        return super().after_process(result)


class RelicOcr(DigitCounter):
    def after_process(self, result):
        result = re.sub(r'[l|](?=\d+$)', '/', result)
        result = re.sub(r'[oO]', '0', result)
        return super().after_process(result)


class DataUpdate(ItemUI, PlannerMixin):
    def _get_data(self):
        """
        Page:
            in: page_item, KEYWORDS_ITEM_TAB.UpgradeMaterials
        """
        ocr = DataDigit(OCR_DATA)

        timeout = Timer(2, count=6).start()
        credit, jade = 0, 0
        for _ in self.loop():
            data = ocr.detect_and_ocr(self.device.image)
            if len(data) == 2:
                credit, jade = [int(re.sub(r'\s', '', d.ocr_text)) for d in data]
                if credit > 0 or jade > 0:
                    break

            logger.warning(f'Invalid credit and stellar jade: {data}')
            if timeout.reached():
                logger.warning('Get data timeout')
                break

        logger.attr('Credit', credit)
        logger.attr('StellarJade', jade)
        return credit, jade

    def _get_relic(self):
        """
        Returns:
            tuple[int, int] | None: Confirmed count and capacity, or None on timeout.

        Page:
            in: page_item, KEYWORDS_ITEM_TAB.Relics
        """
        ocr = RelicOcr(OCR_RELIC)
        timeout = Timer(2, count=6).start()
        relic = None
        previous_reading = None
        for _ in self.loop(skip_first=False):
            relic, _, total = ocr.ocr_single_line(self.device.image)
            if total > 0 and 0 <= relic <= total:
                if (relic, total) == previous_reading:
                    logger.attr('Relic', f'{relic}/{total}')
                    return relic, total
                previous_reading = (relic, total)
            else:
                previous_reading = None
                logger.warning(f'Invalid relic amount: {relic}/{total}')
            if timeout.reached():
                logger.warning('Get relic timeout')
                return None

        return None

    def _get_special_pass(self):
        """
        Page:
            in: page_gacha
        """
        # wait gacha page fully loaded
        for _ in self.loop(timeout=1.5):
            if self.match_template_color(page_gacha.check_button):
                break
        else:
            logger.warning('Wait page_gacha fully loaded timeout')

        ocr = DataDigit(OCR_SPECIAL_PASS)
        timeout = Timer(2, count=6).start()
        special_pass = 0
        for _ in self.loop():
            data = ocr.detect_and_ocr(self.device.image)
            if len(data) == 1:
                text = re.sub(r'\s', '', data[0].ocr_text)
                try:
                    special_pass = int(text)
                    if special_pass >= 0:
                        break
                except ValueError:
                    pass

            logger.warning(f'Invalid special pass: {data}')
            if timeout.reached():
                logger.warning('Get special pass timeout')
                break

        logger.attr('SpecialPass', special_pass)
        return special_pass

    def run(self):
        self.ui_ensure(page_item, acquire_lang_checked=False)
        # item tab stays at the last used tab, switch to UpgradeMaterials
        self.item_goto(KEYWORDS_ITEM_TAB.UpgradeMaterials, wait_until_stable=False)
        credit, jade = self._get_data()

        self.item_goto(KEYWORDS_ITEM_TAB.Relics, wait_until_stable=False)
        stored = self.config.stored.Relic
        previous = (stored.value, stored.total, stored.time)
        relic = self._get_relic()

        self.ui_ensure(page_gacha, acquire_lang_checked=False)
        special_pass = self._get_special_pass()

        with self.config.multi_set():
            self.config.stored.Credit.value = credit
            self.config.stored.StallerJade.value = jade
            if relic is not None:
                self.config.stored.Relic.set(*relic)
            self.config.stored.SpecialPass.value = special_pass
            self.config.task_delay(server_update=True)
            # Sync to planner
            require = self.config.cross_get('Dungeon.Planner.Item_Credit.total', default=0)
            if require:
                self.config.cross_set('Dungeon.Planner.Item_Credit.value', credit)
                self.config.cross_set('Dungeon.Planner.Item_Credit.time', self.config.stored.Credit.time)
                self.planner_write()

        self._notify_relic_full(previous, relic)

    def _notify_relic_full(self, previous, current):
        from module.notify import handle_notify
        from module.notify.relic import near_full, notification_language, relic_notice
        value, total, time = previous
        if (not near_full(value, total, time) or current is None
                or current[1] != total or current[0] != current[1]):
            return False
        stored = self.config.stored.Relic
        title, content = relic_notice(current[0], current[1], stored.time, previous=value,
                                      lang=notification_language())
        logger.warning(content)
        return handle_notify(self.config.Error_OnePushConfig, title=title, content=content)

    def check_relic_full(self):
        """
        Recheck inventory after failed entry when the last update was near full.

        Returns:
            bool: Whether a confirmed full-inventory notification was accepted.

        Pages:
            in: Any
            out: page_item, Relics; unchanged when the previous count is below 99%.
        """
        from module.notify.relic import near_full
        stored = self.config.stored.Relic
        previous = (stored.value, stored.total, stored.time)
        if not near_full(*previous):
            return False
        self.ui_ensure(page_item, acquire_lang_checked=False)
        self.item_goto(KEYWORDS_ITEM_TAB.Relics, wait_until_stable=False)
        current = self._get_relic()
        if current is None:
            return False
        stored.set(*current)
        return self._notify_relic_full(previous, current)
