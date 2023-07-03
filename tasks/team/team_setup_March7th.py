from module.logger import logger
from module.ocr.ocr import *
from tasks.base.assets.assets_base_page import CLOSE
from tasks.base.page import page_team, page_main, page_character
from tasks.team.assets.assets_team import *
from tasks.team.assets.assets_team_character_list import *
from tasks.team.base import ensure_character_selection
from tasks.base.ui import UI


CHARACTER_RECOMMEND = ['三月七', '娜塔莎', '艾丝妲', '青雀', '佩拉', '瓦尔特', '布洛妮娅']


class TeamUI(UI):
    """
    Examples:
        self = TeamUI('alas')
        self.device.screenshot()
        self.check_team_characters()
    """

    def check_team_characters(self, skip_first_screenshot=False):
        self.ui_ensure(page_main, skip_first_screenshot)
        skip_first_screenshot = True
        success = False
        character_selected = '三月七'

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            self.ui_ensure(page_main, skip_first_screenshot)
            ocr_page_main = Ocr(OCR_TEAM_CHECK_HOMEPAGE)
            ocr_page_main.merge_thres_y = 20
            result_page_main = ocr_page_main.detect_and_ocr(self.device.image, direct_ocr=False)
            logger.info('Detect Long-handed Character')
            for r in result_page_main:
                if r.ocr_text in CHARACTER_RECOMMEND:
                    logger.info(f'Long-handed Character "{r.ocr_text}" in team')
                    character_selected = r.ocr_text
                    button = OcrResultButton(r, r.ocr_text)
                    self.device.click(button)
                    success = True
                    break
            if success:
                # Ensure character selection
                selected = ensure_character_selection(self.device.image)
                character_ensure = result_page_main[selected[0]-1].ocr_text
                logger.info(f'"{character_ensure}" is selected ')
                if character_ensure == character_selected:
                    break
            else:
                logger.info('No Long-handed Character in team')
                self.setup_team_character_single()
                continue

        return True

    def setup_team_character_quick(self, skip_first_screenshot=False):
        """
        Examples:
            self = TeamUI('alas')
            self.device.screenshot()
            self.setup_team_character()
        """
        self.ui_ensure(page_team, skip_first_screenshot)
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self.appear_then_click(TEAM_SETUP):
                logger.info('Setup team')
            if self.appear_then_click(TEAM_GRID_FIRST_SITE):
                logger.info('Click TEAM_GRID_FIRST_SITE')
            if self.appear_then_click(March_7th_Mini, similarity=0.55):
                logger.info('Click March_7th_Mini')
                self.appear_then_click(TEAM_CONFIRM)
            if self.appear(TEAM_SETUP_MARCH7TH):
                self.appear_then_click(CLOSE)
                if self.ui_ensure(page_main, skip_first_screenshot):
                    break
            logger.info('Setup team character continue')
            continue

        return True

    def setup_team_character_single(self, skip_first_screenshot=False):
        self.ui_ensure(page_team, skip_first_screenshot)
        skip_first_screenshot = True
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self.appear(TEAM_SETUP_MARCH7TH):
                logger.info('March 7th in team')
                break
            if self.ui_page_appear(page_team):
                ocr_page_team = Ocr(OCR_TEAM_SETUP_FIRST_SITE)
                result_page_team = ocr_page_team.ocr_single_line(self.device.image)
                if result_page_team in CHARACTER_RECOMMEND:
                    break
                self.device.click(OCR_TEAM_SETUP_FIRST_SITE)
            if self.appear_then_click(March_7th_Mini, similarity=0.55):
                logger.info('Click March_7th_Mini')
            if self.appear(TEAM_SETUP_MARCH7TH_ENSURE):
                if self.appear_then_click(CHARACTER_STATE_JOIN):
                    logger.info('Character join team')
                if self.appear(CHARACTER_STATE_LEAVE):
                    self.device.click(CLOSE)
            logger.info('Setup team character continue')
            continue

        return True
