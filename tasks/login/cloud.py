import re

from module.base.base import ModuleBase
from module.base.timer import Timer
from module.base.utils import area_offset, random_rectangle_vector_opted
from module.device.method.utils import AreaButton
from module.exception import GameNotRunningError, RequestHumanTakeover
from module.logger import logger


class XPath:
    """
    xpath 元素，元素可通过 uiautomator2 内的 weditor.exe 查找
    """

    """
    登录界面元素
    """
    # 帐号登录界面的进入游戏按钮
    ACCOUNT_LOGIN = '//*[@text="进入游戏"]'
    # 帐号登录界面，有这些按钮说明帐号没登录
    ACCOUNT_PASSWORD_LOGIN = '//*[@text="账号密码"]'
    ACCOUNT_REGISTER = '//*[@text="立即注册"]'
    ACCOUNT_FORGET_PASSWORD = '//*[@text="忘记密码"]'
    # 登录后的弹窗，获得免费时长
    GET_REWARD = '//*[@text="点击空白区域关闭"]'
    # 额外点击页面
    # https://github.com/LmeSzinc/StarRailCopilot/issues/893
    CLICK_TO_START_GAME = '//*[@text="点击任意处开始游戏"]'
    CLICK_TO_LOGIN = '//*[@text="点击任意地方登录"]'
    # 用户协议和隐私政策更新提示
    # - 拒绝 - 接受
    AGREEMENT_ACCEPT = '//*[@text="接受"]'
    # 版本更新
    # - 立即更新
    UPDATE_CONFIRM = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/mUpgradeDialogOK"]'
    # 新版本已下载完成
    # - 开始安装
    UPDATE_INSTALL = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/mBtnConfirm"]'
    # 安卓系统弹窗
    # 要更新此应用吗？- 取消 - 更新
    # 已完成安装应用。-完成 -打开
    ANDROID_UPDATE_CONFIRM = '//*[@resource-id="android:id/button1"]'
    # 补丁资源已更新，重启游戏可活动更好的游玩体验
    # - 下次再说 - 关闭游戏
    POPUP_TITLE = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/titleTv"]'
    POPUP_CONFIRM = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/confirmTv"]'
    POPUP_CANCEL = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/cancelTv"]'
    # 畅玩卡的剩余时间
    REMAIN_SEASON_PASS = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/tvRemindTime"]'
    # 星云币时长：0 分钟
    REMAIN_PAID = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/tvCoinCount"]'
    # 免费时长： 600 分钟
    REMAIN_FREE = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/tvFreeTimeCount"]'
    # 主界面的开始游戏按钮
    START_GAME = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/btnLauncher"]'
    # 请选择排队队列
    # - 星云币时长快速通道队列 - 普通队列
    QUEUE_SELECT_TITLE = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/tvSelectQueueTypeTitle"]'
    QUEUE_SELECT_PRIOR = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/tvOptionPrior"]'
    QUEUE_SELECT_PRIOR_NAME = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/tvOptionPriorName"]'
    QUEUE_SELECT_NORMAL = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/clOptionNormal"]'
    QUEUE_SELECT_NORMAL_NAME = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/clOptionNormalName"]'
    # 排队中
    QUEUE_TITLE = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/tvEnqueueDialogTitle"]'
    # 预计等待时间
    QUEUE_REMAIN = ('//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/llEnqueueBody"]'
                    '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/tvSingleValue"]')
    QUEUE_REMAIN_LONG = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/tvQueueInfoWaitTimeDefault"]'

    """
    游戏界面元素
    """
    # 网络状态 简洁
    FLOAT_STATE_SIMPLE = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/tvSimpleNetStateMode"]'
    # 网络状态 详细
    FLOAT_STATE_DETAIL = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/tv_ping_value"]'
    """
    悬浮窗及侧边栏元素
    """
    # 悬浮窗
    FLOAT_WINDOW = ('//*[@package="com.miHoYo.cloudgames.hkrpg" and @class="android.widget.RelativeLayout"]'
                    '/*[@class="android.widget.LinearLayout"]')
    # 退出按钮，返回登录页面
    FLOAT_EXIT = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/iv_exit"]'
    # 弹出侧边栏的 节点信息
    # 将这个区域向右偏移作为退出悬浮窗的按钮
    FLOAT_DELAY = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/tv_node_region"]'
    # 弹出侧边栏的滚动区域
    SCROLL_VIEW = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/innerScrollView"]'
    # 画质选择 超高清
    # 选中时selected=True
    SETTING_BITRATE_UHD = '//*[@text="超高清"]'
    # 网络状态 开关
    SETTING_NET_STATE_TOGGLE = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/sw_net_state"]'
    SETTING_NET_STATE_SIMPLE = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/mTvTitleOfSimpleMode"]'
    SETTING_NET_STATE_DETAIL = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/mTvTitleOfDetailMode"]'
    # 问题反馈
    SETTING_PROBLEM = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/tv_problem"]'
    # 下载游戏
    SETTING_DOWNLOAD = '//*[@resource-id="com.miHoYo.cloudgames.hkrpg:id/tv_downloadGame"]'


class LoginAndroidCloud(ModuleBase):
    def _cloud_start(self, skip_first=False):
        """
        Pages:
            out: XPath.START_GAME
        """
        logger.hr('Cloud start')
        update_checker = Timer(2)
        while 1:
            if skip_first:
                skip_first = False
            else:
                self.device.dump_hierarchy()

            # End
            if self.appear(XPath.START_GAME):
                logger.info('Login to cloud main page')
                break
            if (
                    self.appear(XPath.ACCOUNT_REGISTER)
                    or self.appear(XPath.ACCOUNT_PASSWORD_LOGIN)
                    or self.appear(XPath.ACCOUNT_FORGET_PASSWORD)
            ):
                logger.critical('Account not login, you must have login once before running')
                raise RequestHumanTakeover
            if update_checker.started() and update_checker.reached():
                if not self.device.app_is_running():
                    logger.error('Detected hot fixes from game server, game died')
                    raise GameNotRunningError('Game not running')
                update_checker.clear()

            # Click
            if self.appear_then_click(XPath.GET_REWARD):
                continue
            if self.appear_then_click(XPath.CLICK_TO_START_GAME):
                continue
            if self.appear_then_click(XPath.CLICK_TO_LOGIN):
                continue
            if self.appear_then_click(XPath.ACCOUNT_LOGIN):
                continue
            if self.appear_then_click(XPath.POPUP_CONFIRM):
                update_checker.start()
                continue
            # Update
            if self.appear_then_click(XPath.AGREEMENT_ACCEPT):
                continue
            if self.appear_then_click(XPath.UPDATE_CONFIRM):
                continue
            button = self.xpath(XPath.UPDATE_INSTALL)
            if button.text == '开始安装':
                if self.appear_then_click(button):
                    continue
            button = self.xpath(XPath.ANDROID_UPDATE_CONFIRM)
            if button.text in ['更新', '打开']:
                if self.appear_then_click(button):
                    continue

    def _cloud_get_remain(self):
        """
        Pages:
            in: XPath.START_GAME
        """
        regex = re.compile(r'(\d+)')

        text = self.xpath(XPath.REMAIN_SEASON_PASS).text
        logger.info(f'Remain season pass: {text}')
        if res := regex.search(text):
            season_pass = int(res.group(1))
        else:
            season_pass = 0
        # 42 天
        # 5 小时
        if '天' in text:
            pass
        elif '小时' in text:
            season_pass = round(season_pass / 24, 2)
        elif '分钟' in text:
            season_pass = round(season_pass / 24 / 60, 3)
        elif text == '':
            season_pass = 0
        else:
            logger.error(f'Unexpected season pass text: {text}')

        text = self.xpath(XPath.REMAIN_PAID).text
        logger.info(f'Remain paid: {text}')
        if res := regex.search(text):
            paid = int(res.group(1))
        else:
            paid = 0

        text = self.xpath(XPath.REMAIN_FREE).text
        logger.info(f'Remain free: {text}')
        if res := regex.search(text):
            free = int(res.group(1))
        else:
            free = 0

        logger.info(f'Cloud remain: season pass {season_pass} days, {paid} min paid, {free} min free')
        with self.config.multi_set():
            self.config.stored.CloudRemainSeasonPass.value = season_pass
            self.config.stored.CloudRemainPaid.value = paid
            self.config.stored.CloudRemainFree.value = free

    def _is_cloud_ingame(self):
        button = self.xpath(XPath.FLOAT_WINDOW)
        if self.appear(button):
            # Confirm float window size
            width, height = button.size
            if (width < 120 and height < 120) and (width / height < 0.6 or height / width < 0.6):
                return True
        return False

    def _cloud_enter(self, skip_first=False):
        """
        Pages:
            in: XPath.START_GAME
            out: page_main
        """
        logger.hr('Cloud enter')
        while 1:
            if skip_first:
                skip_first = False
            else:
                self.device.dump_hierarchy()

            # End
            if self._is_cloud_ingame():
                logger.info('Cloud game entered')
                break

            # Queue daemon
            button = self.xpath(XPath.QUEUE_REMAIN)
            if self.appear(button, interval=20):
                remain = button.text
                logger.info(f'Queue remain: {remain}')
                self.device.stuck_record_clear()
            button = self.xpath(XPath.QUEUE_REMAIN_LONG)
            if self.appear(button, interval=20):
                remain = button.text
                logger.info(f'Queue remain: {remain}')
                self.device.stuck_record_clear()

            # Click
            if self.appear_then_click(XPath.GET_REWARD):
                continue
            if self.appear_then_click(XPath.START_GAME):
                continue
            if self.appear(XPath.POPUP_CONFIRM, interval=5):
                title = self.xpath(XPath.POPUP_TITLE).text
                logger.info(f'Popup: {title}')
                # 计费提示
                # 本次游戏将使用畅玩卡无限畅玩
                # - 进入游戏(9s) - 退出游戏
                if title == '计费提示':
                    self.device.click(self.xpath(XPath.POPUP_CONFIRM))
                    continue
                # 是否使用星云币时长进入游戏
                # 使用后可优先排队进入游戏，本次游戏仅可使用星云币时长，无法消耗免费时长
                # - 确认使用 - 暂不使用
                if title == '是否使用星云币时长进入游戏':
                    self.device.click(self.xpath(XPath.POPUP_CONFIRM))
                    continue
                # 连接中断
                # 因为您长时间未操作游戏，已中断连接，错误码: -1022
                # - 退出游戏
                if title == '连接中断':
                    self.device.click(self.xpath(XPath.POPUP_CONFIRM))
                    continue
                # 网络提示
                # 当前使用的是移动网络，将消耗较多流量，建议切换至WiFi下体验...
                # - 使用流量进行游戏 - 退出游戏
                if title == '网络提示':
                    self.device.click(self.xpath(XPath.POPUP_CONFIRM))
                    continue
                # 游戏时间已耗尽
                # 您的畅玩卡已到期且星云币时长不足，无法进行游戏。
                # - 取消 - 前往充值
                if title == '游戏时间已耗尽':
                    logger.error('Cloud game time exhausted')
                    self._cloud_exit_exhausted()
                    raise RequestHumanTakeover

            if self.config.Emulator_CloudPriorQueue:
                if self.appear_then_click(XPath.QUEUE_SELECT_PRIOR):
                    continue
                if self.appear_then_click(XPath.QUEUE_SELECT_PRIOR_NAME):
                    continue
            else:
                if self.appear_then_click(XPath.QUEUE_SELECT_NORMAL):
                    continue
                if self.appear_then_click(XPath.QUEUE_SELECT_NORMAL_NAME):
                    continue

        # Disable net state display
        if self._cloud_net_state_appear():
            self._cloud_setting_disable_net_state()
        # Login to game
        from tasks.login.login import Login
        Login(config=self.config, device=self.device).handle_app_login()

    def _cloud_setting_enter(self, skip_first=True):
        """
        Pages:
            in: XPath.FLOAT_WINDOW
            out: XPath.FLOAT_DELAY, setting aside expanded
        """
        while 1:
            if skip_first:
                skip_first = False
            else:
                self.device.dump_hierarchy()

            if self.appear(XPath.FLOAT_DELAY):
                break

            if self.appear_then_click(XPath.FLOAT_WINDOW, interval=3):
                continue

    def _cloud_setting_exit(self, skip_first=True):
        """
        Pages:
            in: XPath.FLOAT_DELAY, setting aside expanded
            out: XPath.FLOAT_WINDOW
        """
        while 1:
            if skip_first:
                skip_first = False
            else:
                self.device.dump_hierarchy()

            if self.appear(XPath.FLOAT_WINDOW):
                break

            if self.appear(XPath.FLOAT_DELAY, interval=3):
                area = self.xpath(XPath.FLOAT_DELAY).area
                area = area_offset(area, offset=(150, 0))
                button = AreaButton(area=area, name='CLOUD_SETTING_EXIT')
                self.device.click(button)
                continue

    def _cloud_setting_disable_net_state(self, skip_first=True):
        """
        Disable net state display, or will cause detection error on COMBAT_AUTO, COMBAT_2X

        Pages:
            in: page_main
            out: page_main
        """
        self._cloud_setting_enter(skip_first=skip_first)

        skip_first = True
        while 1:
            if skip_first:
                skip_first = False
            else:
                self.device.dump_hierarchy()

            button = self.xpath(XPath.SETTING_BITRATE_UHD)
            if self.appear(button, interval=3):
                if not button.selected:
                    logger.info('Set bitrate to UHD')
                    self.device.click(button)
                    continue
            if self.appear(XPath.SETTING_NET_STATE_TOGGLE):
                if self.appear(XPath.SETTING_NET_STATE_SIMPLE) or self.appear(XPath.SETTING_NET_STATE_DETAIL):
                    logger.info('Set net state to disabled')
                    self.appear_then_click(XPath.SETTING_NET_STATE_TOGGLE, interval=3)
                    continue
                else:
                    logger.info('Net state display disabled')
                    break
            # Scroll down
            if not self.appear(XPath.SETTING_PROBLEM):
                area = self.xpath(XPath.SCROLL_VIEW).area
                # An area safe to swipe
                area = (area[0], area[1], area[0] + 25, area[3])
                p1, p2 = random_rectangle_vector_opted(
                    (0, -450), box=area, random_range=(-10, -30, 10, 30), padding=2)
                self.device.swipe(p1, p2, name='SETTING_SCROLL')
                continue

        self._cloud_setting_exit(skip_first=True)

    def _cloud_net_state_appear(self):
        """
        Returns:
            bool: True if net state display is enabled
        """
        if self.appear(XPath.FLOAT_STATE_SIMPLE):
            logger.attr('Net state', 'FLOAT_STATE_SIMPLE')
            return True
        if self.appear(XPath.FLOAT_STATE_DETAIL):
            logger.attr('Net state', 'FLOAT_STATE_DETAIL')
            return True
        logger.attr('Net state', None)
        return False

    def cloud_enter_game(self):
        """
        Note that cloud game needs to be started before calling,
            hierarchy needs to be updated before calling

        Pages:
            in: Any page in cloud game
            out: page_main
        """
        logger.hr('Cloud enter game', level=1)

        with self.config.multi_set():
            if self.config.Emulator_GameClient != 'cloud_android':
                self.config.Emulator_GameClient = 'cloud_android'
            if self.config.Emulator_PackageName != 'CN-Official':
                self.config.Emulator_PackageName = 'CN-Official'
            if self.config.Optimization_WhenTaskQueueEmpty not in ['close_game', 'close_emulator']:
                self.config.Optimization_WhenTaskQueueEmpty = 'close_game'

        if self.appear(XPath.START_GAME):
            logger.info('Cloud game is in main page')
            self._cloud_get_remain()
            self._cloud_enter()
            return True
        elif self.appear(XPath.GET_REWARD):
            # Should be prior than is_in_cloud_page()
            logger.info('Cloud game is at GET_REWARD')
            self._cloud_start()
            self._cloud_get_remain()
            self._cloud_enter()
            return True
        elif self.is_in_cloud_page():
            logger.info('Cloud game is in game')
            return True
        elif self.appear(XPath.FLOAT_DELAY):
            logger.info('Cloud game is in game with float window expanded')
            self._cloud_setting_exit()
            return True
        elif self.appear(XPath.POPUP_CONFIRM):
            logger.info('Cloud game have a popup')
            self._cloud_enter()
            return True
        else:
            self._cloud_start()
            self._cloud_get_remain()
            self._cloud_enter()
            return True

    def is_in_cloud_page(self):
        if self.appear(XPath.START_GAME):
            logger.info('Cloud game is in main page')
            return True
        if self.appear(XPath.GET_REWARD):
            logger.info('Cloud game is at GET_REWARD')
            return True
        if self.appear(XPath.FLOAT_DELAY):
            logger.info('Cloud game is in game with float window expanded')
            return True
        if self.appear(XPath.POPUP_CONFIRM):
            logger.info('Cloud game have a popup')
            return True
        if self.appear(XPath.ACCOUNT_LOGIN):
            logger.info('Cloud game is at ACCOUNT_LOGIN')
            return True

        logger.info('Not in cloud page')
        return False

    def cloud_try_enter_game(self):
        """
        Note that hierarchy needs to be updated before calling

        Pages:
            in: Any page in cloud game
            out: page_main
        """
        if self.is_in_cloud_page():
            self.cloud_enter_game()
            return True

        return False

    def cloud_exit(self, skip_first=False):
        """
        Exit cloud game, note that actively exit is recommended,
        don't kill game directly, or will cause 3min extra fee because the sever side is still alive

        Args:
            skip_first: False by default because cloud_exit() is usually being called after running tasks,
                existing hierarchy may be outdated

        Pages:
            in: XPath.FLOAT_WINDOW
            out: XPath.START_GAME
        """
        logger.hr('Cloud exit')
        if not self.device.app_is_running():
            logger.info('App is not running, no need to exit')
            return

        while 1:
            if skip_first:
                skip_first = False
            else:
                self.device.dump_hierarchy()

            # End
            if self.appear(XPath.START_GAME):
                break

            if self.appear_then_click(XPath.FLOAT_WINDOW, interval=3):
                continue
            if self.appear_then_click(XPath.FLOAT_EXIT, interval=3):
                continue
            # 提示
            # 是否确认退出游戏
            # - 继续游戏 - 退出游戏
            if self.appear_then_click(XPath.POPUP_CONFIRM, interval=3):
                continue
            if self.appear_then_click(XPath.GET_REWARD):
                continue

        # Update remain
        if self.config.stored.CloudRemainSeasonPass:
            self._cloud_get_remain()
        else:
            # Wait cloud remain reduce
            # Value wasn't updated that fast at the time re-entering XPath.START_GAME
            skip_first = True
            timeout = Timer(2, count=4).start()
            prev = [
                self.config.stored.CloudRemainSeasonPass.value,
                self.config.stored.CloudRemainPaid.value,
                self.config.stored.CloudRemainFree.value,
            ]
            with self.config.multi_set():
                while 1:
                    if skip_first:
                        skip_first = False
                    else:
                        self.device.dump_hierarchy()

                    # End
                    if timeout.reached():
                        logger.warning('Wait cloud remain reduce timeout')
                        break
                    self._cloud_get_remain()
                    current = [
                        self.config.stored.CloudRemainSeasonPass.value,
                        self.config.stored.CloudRemainPaid.value,
                        self.config.stored.CloudRemainFree.value,
                    ]
                    if current != prev:
                        break

        logger.info('Cloud exited')

    def _cloud_exit_exhausted(self, skip_first=True):
        logger.info('Cloud exit exhausted')
        while 1:
            if skip_first:
                skip_first = False
            else:
                self.device.dump_hierarchy()

            # End
            if self.appear(XPath.START_GAME):
                break

            if self.appear_then_click(XPath.FLOAT_WINDOW, interval=3):
                continue
            if self.appear_then_click(XPath.FLOAT_EXIT, interval=3):
                continue
            if self.appear_then_click(XPath.POPUP_CANCEL, interval=3):
                continue
            if self.appear_then_click(XPath.GET_REWARD):
                continue

    def cloud_keep_alive(self):
        """
        Randomly do something to prevent being kicked

        WARNING:
            this may cause extra fee
        """
        logger.hr('cloud_keep_alive', level=2)
        while 1:
            self.device.sleep((45, 60))

            logger.info('cloud_keep_alive')
            self._cloud_setting_enter(skip_first=False)
            self._cloud_setting_exit(skip_first=True)


if __name__ == '__main__':
    self = LoginAndroidCloud('src')
    self.device.app_start()
    self.device.dump_hierarchy()
    self.cloud_enter_game()
    self.cloud_keep_alive()
