from module.base.decorator import cached_property
from module.base.timer import Timer
from module.logger import logger
from module.ocr.ocr import Ocr
from tasks.base.assets.assets_base_page import MAIN_GOTO_MENU
from tasks.base.assets.assets_base_popup import POPUP_CANCEL, POPUP_CONFIRM, POPUP_SINGLE, POPUP_TITLE_TIP
from tasks.base.page import page_menu
from tasks.base.ui import UI
from tasks.freebies.assets.assets_freebies_code import *
from tasks.freebies.assets.assets_freebies_support_reward import MENU_TO_PROFILE
from tasks.freebies.code_used import CodeManager


class RedemptionCode(UI):
    # Global cooldown to redeem codes
    # You need at least 5 seconds between 2 redeems, otherwise server don't accept
    code_cooldown = Timer(5)

    def is_in_code_input(self, interval=0):
        self.device.stuck_record_add(INPUT_CHECK)

        if interval and not self.interval_is_reached(INPUT_CHECK, interval=interval):
            return False

        appear = False
        # yellow confirm button
        if self.image_color_count(INPUT_CHECK, color=(255, 199, 89), count=400, threshold=221):
            appear = True
        # pure white button at bottom
        if self.image_color_count(INPUT_CHECK, color=(255, 255, 255), count=10000, threshold=221):
            appear = True
        # input border become orange
        if self.image_color_count(INPUT_BORDER, color=(210, 119, 10), count=100, threshold=221):
            appear = True

        if appear and interval:
            self.interval_reset(INPUT_CHECK, interval=interval)

        return appear

    def is_code_invalid(self):
        return self.image_color_count(CODE_INVALID, color=(186, 78, 82), count=400, threshold=221)

    def _code_enter(self):
        """
        From wherever to INPUT_CHECK, ready to input

        Pages:
            in: page_menu
            out: CODE_CHECK
        """
        logger.hr('Code enter')
        self.interval_clear([
            page_menu.check_button,
            CODE_ENTER,
            CODE_CHECK,
        ])
        for _ in self.loop():
            if self.appear(CODE_CHECK):
                break

            if self.is_in_main(interval=5):
                self.device.click(MAIN_GOTO_MENU)
                continue
            if self.ui_page_appear(page_menu, interval=3):
                self.device.click(MENU_TO_PROFILE)
                continue
            if self.appear_then_click(CODE_ENTER, interval=3):
                continue

    def _code_exit(self):
        """
        Pages:
            in: is_in_code_input
            out: page_menu
        """
        logger.hr('Code exit')
        self.interval_clear([
            INPUT_CHECK,
            POPUP_CONFIRM,
            POPUP_CANCEL,
        ])
        for _ in self.loop():
            if self.ui_page_appear(page_menu):
                break

            if self.handle_popup_cancel():
                continue
            if self.handle_popup_single():
                continue

        # clear state
        self.interval_clear([
            page_menu.check_button
        ])

    def _code_input(self, code):
        """
        Input code into game using uiautomator2
        """
        logger.info(f'Code input: {code}')
        self.interval_clear([
            POPUP_CONFIRM
        ])
        interval = Timer(2, count=6)
        for _ in self.loop():
            # might be both CODE_CHECK and POPUP_TITLE_TIP when POPUP_TITLE_TIP is transparent
            if self.appear(CODE_CHECK) and not self.appear(POPUP_TITLE_TIP) and self.appear(POPUP_CONFIRM):
                # check if POPUP_CONFIRM is white
                area = POPUP_CONFIRM.button
                area = (area[0] - 50, area[1] - 5, area[2] + 50, area[3] + 5)
                if self.image_color_count(area, color=(225, 225, 225), count=500, threshold=221):
                    logger.info('Code inputted')
                    break

            if interval.reached():
                logger.info('set_clipboard')
                d = self.device.u2
                d.set_clipboard(code)
                # no need to retry this clicking because POPUP_CONFIRM will only appear when code is not empty
                self.device.click(INPUT_PASTE)
                interval.reset()
            if self.appear(POPUP_TITLE_TIP) and self.handle_popup_confirm():
                continue

    def _code_redeem(self):
        """
        Returns:
            str: If having any error message

        Pages:
            in: POPUP_CONFIRM
            out: page_menu
        """
        logger.hr('Code redeem')

        # POPUP_CONFIRM -> POPUP_SINGLE
        self.interval_clear([POPUP_CONFIRM, POPUP_SINGLE])
        for _ in self.loop():
            if self.appear(POPUP_SINGLE):
                logger.info('Code redeem success')
                break
            if self.is_code_invalid():
                logger.warning('Code invalid')

                # show reason in log
                ocr = Ocr(CODE_INVALID)
                error = ocr.ocr_single_line(self.device.image)

                self._code_exit()
                return error

            if self.handle_popup_confirm():
                # confirm redeem, start global cooldown
                self.code_cooldown.reset()
                continue

        # POPUP_SINGLE -> page_menu
        for _ in self.loop():
            if self.appear(CODE_ENTER):
                logger.info(f'Code redeem ends at {CODE_ENTER}')
                break
            if self.ui_page_appear(page_menu):
                logger.info(f'Code redeem ends at {page_menu}')
                break

            if self.handle_popup_single():
                continue

        return ''

    @cached_property
    def code_manager(self):
        return CodeManager(self)

    def code_redeem(self, code):
        """
        Args:
            code (str):

        Returns:
            bool: If success

        Pages:
            in: page_menu
            out: page_menu
        """
        logger.hr('Code redeem', level=2)

        if not self.code_cooldown.reached():
            logger.info('Waiting code cooldown')
            self.code_cooldown.wait()

        self._code_enter()
        self._code_input(code)
        error = self._code_redeem()
        self.code_manager.mark_used(code, error)
        return not error

    def run(self):
        self.ui_ensure(page_menu)

        total = 0
        codes = self.code_manager.get_codes()
        logger.info(f'Redeem codes available: {codes}')
        for code in codes:
            if self.code_redeem(code):
                total += 1

        return total
