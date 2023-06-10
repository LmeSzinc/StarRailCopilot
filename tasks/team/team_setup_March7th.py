from module.logger import logger
from module.ocr.ocr import *
from tasks.base.assets.assets_base_page import CLOSE
from tasks.base.page import page_team, page_main
from tasks.team.assets.assets_team import *
from tasks.team.assets.assets_team_character_list import *
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
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                ocr = Ocr(TEAM_CHECK_HOMEPAGE)
                ocr.merge_thres_y = 20
                result = ocr.detect_and_ocr(self.device.screenshot(), direct_ocr=False)
                for r in result:
                    if r.ocr_text in CHARACTER_RECOMMEND:
                        logger.info('Long-handed Character "{}" in team'.format(r.ocr_text))
                        button = OcrResultButton(r, r.ocr_text)
                        self.device.click(button)
                        return True
                logger.info('no Long-handed Character in team')
                if self.setup_team_character():
                    return True
                continue

    def setup_team_character(self, skip_first_screenshot=False):
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
                logger.info('setup team')
            if self.appear_then_click(TEAM_GRID_FIRST_SITE):
                logger.info('click TEAM_GRID_FIRST_SITE')
                self.device.screenshot()
                self.match_template(March_7th_Mini)
            if self.appear_then_click(March_7th_Mini, similarity=0.55):
                logger.info('click March_7th_Mini')
                self.appear_then_click(TEAM_CONFIRM)
            if self.appear(TEAM_SETUP_MARCH7TH):
                self.appear_then_click(CLOSE)
                return True
            logger.info('setup team character continue')
            continue
