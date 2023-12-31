from module.base.button import match_template
from module.base.timer import Timer
from module.logger import logger
from module.ocr.ocr import Digit
from tasks.base.page import page_item
from tasks.base.ui import UI
from tasks.item.assets.assets_item_data import *
from tasks.item.assets.assets_item_items import *


class DataUpdate(UI):
    def _get_data(self):
        """
        Page:
            in: page_item
        """
        ocr = Digit(OCR_DATA)

        timeout = Timer(2, count=6).start()
        credit, jade = 0, 0
        while 1:
            data = ocr.detect_and_ocr(self.device.image)
            if len(data) == 2:
                credit, jade = [int(d.ocr_text) for d in data]
                if credit > 0 or jade > 0:
                    break

            logger.warning(f'Invalid credit and stellar jade: {data}')
            if timeout.reached():
                logger.warning('Get data timeout')
                break

        logger.attr('Credit', credit)
        logger.attr('StellarJade', jade)
        with self.config.multi_set():
            self.config.stored.Credit.value = credit
            self.config.stored.StallerJade.value = jade

        return credit, jade
    def _match_item(self, image):
        logger.info("Matching!!!!!!!!!!!!!!!!!!!!")
        list = [
            ITEM_XP_LIGHTCONE_C
        ]
        for item in list:
            item.matched_button.search = STORED_AREA.matched_button.search
            if item.match_template(image):
                return item
        return ButtonWrapper(name='None')
    def _match_items(self,image):
        #logger.info("Matching!!!!!!!!!!!!!!!!!!!!")
        list = [
            ITEM_XP_CHARACTER_A,
            ITEM_XP_CHARACTER_B,
            ITEM_XP_CHARACTER_C,
            ITEM_XP_LIGHTCONE_A,
            ITEM_XP_LIGHTCONE_B,
            ITEM_XP_LIGHTCONE_C,
            ITEM_XP_RELIC_A,
            ITEM_XP_RELIC_B,
            ITEM_XP_RELIC_C,
        ]
        match = []
        for item in list:
            item.matched_button.search = STORED_AREA.matched_button.search
            if item.match_template(image):
                match.append(item)
        return match
    def _get_stored(self):
        """
        Page:
            in: page_item
        """
        #self.device.sleep(0.3)
        logger.info("获取材料中")
        ocr = Digit(STORED_AREA_LINE_A)
        timeout = Timer(2, count=6).start()

        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            data1 = ocr.detect_and_ocr(self.device.image)
            data2 = ocr.detect_and_ocr(self.device.image)

            dl1 = [int(d.ocr_text) for d in data1]
            dl2 = [int(d.ocr_text) for d in data2]

            matched1 = self._match_items(self.device.image)
            matched2 = self._match_items(self.device.image)


            if dl1 == dl2 and matched1 == matched2:
                for index,value in enumerate(dl1):
                    logger.info(f"{matched1[index].name}  {value}")
                #for item in matched1:
                #    logger.info(item.name)
                break
            if timeout.reached():
                logger.warning('Get data timeout')
                break


    def run(self):
        #self.device.screenshot()


        self.ui_ensure(page_item, acquire_lang_checked=False)
        
        with self.config.multi_set():
            self._get_data()
            self._get_stored()
            self.config.task_delay(server_update=True)



if __name__ == "__main__":
    DataUpdate(config='src', task='Data_Update').run()
