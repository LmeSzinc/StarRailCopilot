from module.base.timer import Timer
from module.logger import logger
from module.ocr.ocr import Ocr
from tasks.base.page import page_event
from tasks.base.ui import UI
from tasks.freebies.assets.assets_freebies_gift_of_odyssey import (
    OCR_CLAIM,
    OCR_EVENT,
    EVENT_SELECTED,
    GET_REWARD_BUTTON,
)
from tasks.freebies.keywords import KEYWORDS_FREEBIES_GIFT_OF_ODYSSEY, GiftOfOdysseyEvent


class GiftofOdyssey(UI):

    def run(self):
        logger.hr("Gift of Odyssey", level=1)
        self.ui_ensure(page_event)
        if self._select_event():
            logger.info("Event selected")
            self._get_reward()

    def _select_event(self):
        logger.info("Selecting Gift of Odyssey event")
        ocr = Ocr(OCR_EVENT)
        # When Gift of Odyssey event is the first event, the ocr results will be effected due to the animation of selected event
        timer = Timer(0.5, count=1).start()
        while 1:
            self.device.screenshot()
            results = ocr.matched_ocr(self.device.image, GiftOfOdysseyEvent)
            if len(results) == 0 and timer.reached():
                logger.info("Event not found")
                return False
            if len(results) == 1:
                break

        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(EVENT_SELECTED):
                break
            if self.device.click(results[0]):
                continue
        return True

    def _get_claim_status(self, image):
        ocr = Ocr(OCR_CLAIM)
        results = ocr.matched_ocr(image, GiftOfOdysseyEvent)
        claimed = [result for result in results if result == KEYWORDS_FREEBIES_GIFT_OF_ODYSSEY.Claimed]
        claim = [result for result in results if result == KEYWORDS_FREEBIES_GIFT_OF_ODYSSEY.Claim]
        awaiting = [result for result in results if result == KEYWORDS_FREEBIES_GIFT_OF_ODYSSEY.Awaiting_check_in]
        status = len(claimed), len(claim), len(awaiting)
        logger.info(f"Claim status (Claimed, Claim, Awaiting check in): {status}")
        if sum(status) != 7:
            logger.warning("Num of OCR results is not seven")
        return status

    def _get_reward(self):
        logger.info("Getting reward")
        skip_first_screenshot = True
        interval = Timer(2)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(EVENT_SELECTED):
                _, claim, _ = self._get_claim_status(self.device.image)
                if claim == 0:
                    logger.info("No more reward to get")
                    break
            if self.handle_reward():
                continue
            if interval.reached():
                if self.appear_then_click(GET_REWARD_BUTTON):
                    interval.reset()
