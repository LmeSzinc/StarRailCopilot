import re

from module.base.timer import Timer
from module.logger import logger
from module.ocr.ocr import Digit, DigitCounter
from tasks.base.page import page_item
from tasks.item.assets.assets_item_data import OCR_DATA, OCR_RELIC
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
        result = re.sub(r'[l1|]3000', '/3000', result)
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
        while 1:
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
        Page:
            in: page_item, KEYWORDS_ITEM_TAB.Relics
        """
        ocr = RelicOcr(OCR_RELIC)
        timeout = Timer(2, count=6).start()
        while 1:
            relic, _, total = ocr.ocr_single_line(self.device.image)
            if total == 3000 or relic < 0:
                break
            logger.warning(f'Invalid relic amount: {relic}/{total}')
            if timeout.reached():
                logger.warning('Get relic timeout')
                break

        logger.attr('Relic', relic)
        return relic

    def run(self):
        self.ui_ensure(page_item, acquire_lang_checked=False)
        # item tab stays at the last used tab, switch to UpgradeMaterials
        self.item_goto(KEYWORDS_ITEM_TAB.UpgradeMaterials, wait_until_stable=False)
        credit, jade = self._get_data()

        self.item_goto(KEYWORDS_ITEM_TAB.Relics, wait_until_stable=False)
        relic = self._get_relic()

        with self.config.multi_set():
            self.config.stored.Credit.value = credit
            self.config.stored.StallerJade.value = jade
            self.config.stored.Relic.value = relic
            self.config.task_delay(server_update=True)
            # Sync to planner
            require = self.config.cross_get('Dungeon.Planner.Item_Credit.total', default=0)
            if require:
                self.config.cross_set('Dungeon.Planner.Item_Credit.value', credit)
                self.config.cross_set('Dungeon.Planner.Item_Credit.time', self.config.stored.Credit.time)
                self.planner_write()
