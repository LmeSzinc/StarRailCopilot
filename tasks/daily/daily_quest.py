import numpy as np
from module.base.timer import Timer
from module.logger import *
from module.ocr.ocr import Ocr, OcrResultButton
from tasks.daily.assets.assets_daily import *
from tasks.daily.keywords import DailyQuest
from tasks.dungeon.ui import DungeonUI
from tasks.dungeon.keywords import KEYWORDS_DUNGEON_TAB


class DailyQuestUI(DungeonUI):
    def _ensure_position(self, direction: str, template: ButtonWrapper, skip_first_screenshot=True):
        interval = Timer(5)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(template):
                logger.info(f"Ensure position: {direction}")
                break
            if interval.reached():
                self._swipe(direction)
                interval.reset()
                continue

    def _swipe(self, direction: str):
        vector = np.random.uniform(0.65, 0.85)
        if direction == 'left':
            swipe_vector = (vector * OCR_DAILY_QUEST.width, 0)
        elif direction == 'right':
            swipe_vector = (-vector * OCR_DAILY_QUEST.width, 0)
        else:
            logger.warning(f'Unknown drag direction: {direction}')
            return
        self.device.swipe_vector(swipe_vector, box=OCR_DAILY_QUEST.button,
                                 random_range=(-10, -10, 10, 10), name='DAILY_QUEST_DRAG')

    def _ocr_single_page(self) -> list[OcrResultButton]:
        ocr = Ocr(OCR_DAILY_QUEST)
        ocr.merge_thres_y = 20
        return ocr.matched_ocr(self.device.image, DailyQuest)

    def daily_quests_recognition(self):
        logger.info("Recognizing daily quests")
        self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Daily_Training)
        self._ensure_position('left', DAILY_QUEST_LEFT_START)
        results = self._ocr_single_page()
        self._ensure_position('right', DAILY_QUEST_RIGHT_END)
        results += [result for result in self._ocr_single_page() if result not in results]
        if len(results) < 6:
            logger.warning(f"Recognition failed at {6 - len(results)} quests")
        logger.info("Daily quests recognition complete")
        return results

    def get_single_daily_reward(self, template: ButtonWrapper,
                                checked_template: ButtonWrapper, skip_first_screenshot=True):
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.handle_reward() or self.appear(checked_template):
                break
            if self.appear_then_click(template):
                continue

    def get_daily_rewards(self):
        self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Daily_Training)
        logger.info("Getting daily rewards")
        for i in range(1, 6):
            eval(f"self.get_single_daily_reward(DAILY_REWARD_{i}, DAILY_REWARD_{i}_CHECKED)")
            logger.info(f"Got reward: {i}")
        logger.info("All daily reward got")
