from module.base.timer import Timer
from module.logger import logger
from tasks.base.assets.assets_base_page import BACK, MAIN_GOTO_MENU
from tasks.base.page import page_menu
from tasks.base.ui import UI
from tasks.freebies.assets.assets_freebies_mail import *


class MailReward(UI):
    def _mail_enter(self):
        """
        Pages:
            in: page_menu
            out: MAIL_CHECK
        """
        logger.info('Mail enter')
        self.interval_clear([
            page_menu.check_button
        ])
        for _ in self.loop():
            if self.match_template_luma(MAIL_CHECK):
                break

            if self.is_in_main(interval=5):
                self.device.click(MAIN_GOTO_MENU)
                continue
            if self.ui_page_appear(page_menu, interval=3):
                self.device.click(MENU_GOTO_MAIL)
                continue
            if self.handle_popup_confirm():
                continue

    def _mail_exit(self):
        """
        Pages:
            in: MAIL_CHECK
            out: page_menu
        """
        logger.info('Mail exit')
        self.interval_clear([
            MAIL_CHECK
        ])

        for _ in self.loop():
            if self.ui_page_appear(page_menu):
                break

            if self.handle_reward():
                self.interval_clear(MAIL_CHECK)
                continue
            if self.handle_popup_confirm():
                continue
            if self.match_template_luma(MAIL_CHECK, interval=3):
                logger.info(f'{MAIL_CHECK} -> {BACK}')
                self.device.click(BACK)
                continue

        # clear state
        self.interval_clear([
            page_menu.check_button
        ])

    def _mail_get_claim_button(self):
        """
        Returns:
            CLAIM_ALL or CLAIM_ALL_DONE or None
        """
        timeout = Timer(1.5, count=5).start()
        for _ in self.loop():
            if self.appear(CLAIM_ALL):
                logger.attr('MailClaim', CLAIM_ALL)
                return CLAIM_ALL
            # CLAIM_ALL_DONE is transparent, use match_template_luma
            if self.match_template_luma(CLAIM_ALL_DONE):
                logger.attr('MailClaim', CLAIM_ALL_DONE)
                return CLAIM_ALL
            if timeout.reached():
                logger.warning('Get MailClaim timeout')
                return None

    def _mail_claim(self):
        """
        Pages:
            in: CLAIM_ALL
            out: CLAIM_ALL_DONE
        """
        logger.info('Mail claim all')
        for _ in self.loop():
            # CLAIM_ALL_DONE is transparent, use match_template_luma
            if self.match_template_luma(CLAIM_ALL_DONE):
                break

            if self.appear_then_click(CLAIM_ALL, interval=3):
                continue
            if self.handle_popup_confirm():
                continue
            if self.handle_reward():
                continue

    def _is_mail_red_dot(self):
        """
        Pages:
            in: page_menu
        """
        return self.image_color_count(MAIL_RED_DOT, color=(202, 24, 48), count=30, threshold=221)

    def mail_claim_all(self):
        """
        Claim mails and exit

        Returns:
            bool: If claimed

        Pages:
            in: page_menu
            out: page_menu
        """
        self.ui_ensure(page_menu)

        dot = self._is_mail_red_dot()
        logger.attr('MailRedDot', dot)
        if not dot:
            return False

        # claim all
        self._mail_enter()
        button = self._mail_get_claim_button()
        if button is CLAIM_ALL:
            self._mail_claim()
            self._mail_exit()
            return True
        else:
            self._mail_exit()
            return False
