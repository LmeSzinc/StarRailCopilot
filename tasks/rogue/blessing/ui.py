from module.base.utils import area_offset
from module.logger import logger
from module.ocr.ocr import Digit, OcrResultButton
from tasks.base.ui import UI
from tasks.rogue.assets.assets_rogue_ui import *
from tasks.rogue.assets.assets_rogue_weekly import REWARD_ENTER
from tasks.rogue.blessing.blessing import RogueBlessingSelector
from tasks.rogue.blessing.bonus import RogueBonusSelector
from tasks.rogue.blessing.curio import RogueCurioSelector
from tasks.rogue.keywords import RoguePath


class RogueUI(UI):
    path: RoguePath

    @property
    def cosmic_fragment(self):
        """
        Return valid result only when template appear
        """
        if self.appear(COSMIC_FRAGMENT):
            return Digit(OCR_COSMIC_FRAGMENT).ocr_single_line(self.device.image)
        return 0

    def is_page_choose_blessing(self):
        return (self.image_color_count(PAGE_CHOOSE_BUFF, (245, 245, 245), count=200)
                and self.appear(CHECK_BLESSING))

    def is_page_choose_curio(self):
        return self.appear(PAGE_CHOOSE_CURIO)

    def is_page_choose_bonus(self):
        if self.appear(PAGE_CHOOSE_BONUS):
            return True
        # Also check bonus cards
        if self.appear(PAGE_CHOOSE_BONUS_TRAILBLAZE):
            return True
        return False

    def is_page_event(self):
        return self.appear(PAGE_EVENT)

    def is_page_rogue_main(self):
        return self.match_template_color(REWARD_ENTER)

    def is_page_rogue_launch(self):
        return self.match_template_color(ROGUE_LAUNCH)

    def is_unrecorded(self, target: OcrResultButton, relative_area):
        """
        To check a rogue keyword is not record in game index by finding template
        """
        FLAG_UNRECORD.matched_button.search = area_offset(relative_area, target.area[:2])
        return self.appear(FLAG_UNRECORD)

    def handle_blessing_popup(self):
        # Obtained a free blessing from curio
        if self.appear(BLESSING_OBTAINED, interval=2):
            logger.info(f'{BLESSING_OBTAINED} -> {BLESSING_CONFIRM}')
            self.device.click(BLESSING_CONFIRM)
            return True
        # Enhanced a blessing from occurrence
        if self.appear(BLESSING_ENHANCED, interval=2):
            logger.info(f'{BLESSING_ENHANCED} -> {BLESSING_CONFIRM}')
            self.device.click(BLESSING_CONFIRM)
            return True
        # Lost and re-obtain blessing, randomized by curio
        if self.appear(BLESSING_LOST, interval=2):
            logger.info(f'{BLESSING_LOST} -> {BLESSING_CONFIRM}')
            self.device.click(BLESSING_CONFIRM)
            return True
        # Obtain a curio from occurrence
        if self.appear(CURIO_OBTAINED, interval=2):
            logger.info(f'{CURIO_OBTAINED} -> {BLESSING_CONFIRM}')
            self.device.click(BLESSING_CONFIRM)
            return True
        # Fixed a curio from occurrence
        if self.appear(CURIO_FIXED, interval=2):
            logger.info(f'{CURIO_FIXED} -> {BLESSING_CONFIRM}')
            self.device.click(BLESSING_CONFIRM)
            return True
        return False

    def handle_blessing(self):
        """
        Returns:
            bool: If handled
        """
        if self.is_page_choose_blessing():
            logger.hr('Choose blessing', level=2)
            selector = RogueBlessingSelector(self)
            selector.recognize_and_select()
            return True
        if self.is_page_choose_curio():
            logger.hr('Choose curio', level=2)
            selector = RogueCurioSelector(self)
            selector.recognize_and_select()
            return True
        if self.is_page_choose_bonus():
            logger.hr('Choose bonus', level=2)
            selector = RogueBonusSelector(self)
            selector.recognize_and_select()
            return True
        if self.handle_blessing_popup():
            return True

        return False
