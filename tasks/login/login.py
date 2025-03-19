from module.base.timer import Timer
from module.exception import GameNotRunningError
from module.logger import logger
from tasks.base.page import page_main
from tasks.combat.assets.assets_combat_interact import MAP_LOADING
from tasks.login.assets.assets_login import *
from tasks.login.cloud import LoginAndroidCloud
from tasks.rogue.blessing.ui import RogueUI


class Login(LoginAndroidCloud, RogueUI):
    def _handle_app_login(self):
        """
        Pages:
            in: Any page
            out: page_main

        Raises:
            GameStuckError:
            GameTooManyClickError:
            GameNotRunningError:
        """
        logger.hr('App login')
        orientation_timer = Timer(5)
        startup_timer = Timer(5).start()
        app_timer = Timer(5).start()
        login_success = False
        first_map_loading = True
        self.device.stuck_record_clear()

        while 1:
            # Watch if game alive
            if app_timer.reached():
                if not self.device.app_is_running():
                    logger.error('Game died during launch')
                    raise GameNotRunningError('Game not running')
                app_timer.reset()
            # Watch device rotation
            if not login_success and orientation_timer.reached():
                # Screen may rotate after starting an app
                self.device.get_orientation()
                orientation_timer.reset()

            self.device.screenshot()

            # End
            # Game client requires at least 5s to start
            # The first few frames might be captured before app_stop(), ignore them
            if startup_timer.reached():
                if self.ui_page_appear(page_main):
                    logger.info('Login to main confirm')
                    break

            # Watch resource downloading and loading
            if self.appear(LOGIN_LOADING, interval=5):
                logger.info('Game resources downloading or loading')
                self.device.stuck_record_clear()
                app_timer.reset()
                orientation_timer.reset()
            # Watch map loading
            if first_map_loading and self.appear(MAP_LOADING, similarity=0.75):
                logger.info('Map loading')
                # Reset stuck record after map loading to extend wait time on slow devices
                self.device.stuck_record_clear()
                first_map_loading = False
                continue

            # Login
            if self.is_in_login_confirm(interval=5):
                self.device.click(LOGIN_CONFIRM)
                login_success = True
                continue
            if self.handle_user_agreement():
                continue
            # Additional
            if self.handle_popup_single():
                continue
            if self.handle_popup_confirm():
                continue
            if self.ui_additional():
                continue
            if self.handle_blessing():
                continue

        return True

    def handle_user_agreement(self):
        """
        Returns:
            bool: If clicked
        """
        # CN user agreement popup
        if self.appear_then_click(USER_AGREEMENT_ACCEPT, interval=3):
            return True
        # Oversea TOS
        if self.match_template_color(TOS_ACCEPT, interval=3):
            self.device.click(TOS_ACCEPT)
            return True
        if self.appear(TOS_AGREE_TEXT, interval=3):
            # Select checkbox
            if not self.image_color_count(TOS_AGREE_CHECKBOX, color=(254, 240, 108), count=20, threshold=180):
                self.device.click(TOS_AGREE_CHECKBOX)
                return True
        return False

    def handle_account_confirm(self):
        """
        ACCOUNT_CONFIRM is not a multi-server assets as text language is not detected before log in.
        It just detects all languages.

        ACCOUNT_CONFIRM doesn't appear in most times, sometimes game client won't auto login but requiring you to
        click login even if there is only one account.

        Returns:
            bool: If clicked
        """
        if self.appear_then_click(ACCOUNT_CONFIRM):
            return True
        return False

    def handle_app_login(self):
        logger.info('handle_app_login')
        self.device.screenshot_interval_set(1.0)
        self.device.stuck_timer = Timer(300, count=300).start()
        try:
            self._handle_app_login()
        finally:
            self.device.screenshot_interval_set()
            self.device.stuck_timer = Timer(60, count=60).start()

    def app_stop(self):
        logger.hr('App stop')
        if self.config.is_cloud_game:
            self.cloud_exit()
        self.device.app_stop()

    def app_start(self):
        logger.hr('App start')
        self.device.app_start()

        if self.config.is_cloud_game:
            self.device.dump_hierarchy()
            self.cloud_enter_game()
        else:
            self.handle_app_login()

    def app_restart(self):
        logger.hr('App restart')
        self.device.app_stop()
        self.device.app_start()

        if self.config.is_cloud_game:
            self.device.dump_hierarchy()
            self.cloud_enter_game()
        else:
            self.handle_app_login()

        self.config.task_delay(server_update=True)
