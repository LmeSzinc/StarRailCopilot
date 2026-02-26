from module.base.timer import Timer
from module.exception import GameNotRunningError
from module.logger import logger
from tasks.base.assets.assets_base_page import CHARACTER_CHECK, CLOSE
from tasks.base.page import page_main
from tasks.combat.assets.assets_combat_interact import MAP_LOADING
from tasks.login.agreement import AgreementHandler
from tasks.login.assets.assets_login import *
from tasks.login.assets.assets_login_popup import *
from tasks.login.cloud import LoginAndroidCloud
from tasks.login.uid import UIDHandler
from tasks.rogue.blessing.ui import RogueUI


class Login(LoginAndroidCloud, RogueUI, AgreementHandler, UIDHandler):
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
        start_success = False
        start_timeout = Timer(30).start()
        login_success = False
        first_map_loading = True
        self.device.stuck_record_clear()

        while 1:
            # Watch if game alive
            if app_timer.reached():
                if self.device.app_is_running():
                    start_success = True
                else:
                    if start_success:
                        logger.error('Game died during launch')
                        raise GameNotRunningError('Game not running')
                    else:
                        if start_timeout.reached():
                            logger.error('Game not started after 30s')
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

            # Error
            # Unable to initialize Unity Engine
            if self.match_template_luma(UNITY_ENGINE_ERROR):
                logger.error('Unable to initialize Unity Engine')
                self.device.app_stop()
                raise GameNotRunningError('Unable to initialize Unity Engine')
            # Login
            if self.is_in_login_confirm(interval=5):
                self.device.click(LOGIN_CONFIRM)
                # Reset stuck record to extend wait time on slow devices
                self.device.stuck_record_clear()
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
            if self.handle_login_popup():
                continue
            if self.handle_blessing():
                continue

        return True

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

    def handle_login_popup(self):
        """
        Returns:
            bool: If clicked
        """
        # 4.0 ADVERTISE for new world
        if self.match_template_luma(ADVERTISE_Planarcadia, interval=2):
            self.device.click(ADVERTISE_Planarcadia)
            return True
        # 3.7 ADVERTISE_Cyrene popup
        if self.match_template_luma(ADVERTISE_Cyrene, interval=2):
            logger.info(f'{ADVERTISE_Cyrene} -> {CLOSE}')
            self.device.click(CLOSE)
            return True
        if self.match_template_luma(MAIL_Cyrene, interval=2):
            self.device.click(MAIL_Cyrene)
            return True
        # 3.2 Castorice popup that advertise you go gacha, but no, close it
        if self.handle_ui_close(ADVERTISE_Castorice, interval=2):
            return True
        # homecoming popup
        if self.handle_ui_close(HOMECOMING_TITLE, interval=2):
            return True
        # Might enter page_character while clicking CLOSE
        if self.handle_ui_close(CHARACTER_CHECK, interval=2):
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
