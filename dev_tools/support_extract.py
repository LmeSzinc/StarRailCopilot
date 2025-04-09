from module.exception import ScriptError
from module.logger import logger
from tasks.combat.assets.assets_combat_support import COMBAT_SUPPORT_LIST
from tasks.combat.support_dev import SupportDev
from tasks.dungeon.keywords import DungeonList, KEYWORDS_DUNGEON_TAB
from tasks.ornament.assets.assets_ornament_combat import SUPPORT_ADD
from tasks.ornament.ornament import Ornament


class SupportExtract(Ornament, SupportDev):
    def get_first_ornament_dungeon(self) -> DungeonList:
        for dungeon in DungeonList.instances.values():
            if dungeon.is_Ornament_Extraction:
                return dungeon
        logger.error('No is_Ornament_Extraction dungeons')
        raise ScriptError

    def support_enter(self, skip_first_screenshot=True):
        """
        Pages:
            in: SUPPORT_ADD
            out: COMBAT_SUPPORT_LIST
        """
        logger.info('Support enter')
        self.interval_clear(SUPPORT_ADD)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self.appear(COMBAT_SUPPORT_LIST):
                break
            if self.appear(SUPPORT_ADD, interval=2):
                self.device.click(SUPPORT_ADD)
                self.interval_reset(SUPPORT_ADD)
                continue

    def support_quit(self, skip_first_screenshot=True):
        """
        Pages:
            in: COMBAT_SUPPORT_LIST
            out: SUPPORT_ADD
        """
        logger.info('Support quit')
        self.interval_clear(COMBAT_SUPPORT_LIST)
        SUPPORT_ADD.clear_offset()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self.appear(SUPPORT_ADD):
                break
            if self.appear(COMBAT_SUPPORT_LIST, interval=2):
                self.device.click(SUPPORT_ADD)
                self.interval_reset(COMBAT_SUPPORT_LIST)
                continue

    def _init_support_page(self):
        """
        Set to stranger tab and full load support list

        Pages:
            in: COMBAT_SUPPORT_LIST
        """
        tab = self.support_tab()
        tab.set('Strangers', main=self)
        scroll = self._support_scroll()
        scroll.set_bottom(main=self)
        scroll.set_top(main=self)

    def goto_support_page(self):
        """
        Pages:
            out: COMBAT_SUPPORT_LIST, in ornament extraction
                because you can enter support without having enough stamina
        """
        if self.appear(COMBAT_SUPPORT_LIST):
            logger.info('Already in support page')
            self._init_support_page()
            return

        if self.appear(SUPPORT_ADD):
            logger.info('At SUPPORT_ADD')
            self.support_enter()
            self._init_support_page()
            return

        logger.info('Goto support page')
        # Goto first ornament extraction
        dungeon = self.get_first_ornament_dungeon()
        self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Survival_Index)
        self.dungeon_goto(dungeon)
        self.support_enter()
        self._init_support_page()

    def gen_templates(self):
        """
        Endlessly refreshing and scroll ramdom support, generate new support templates
        Stop manually if you think missing templates are all gathered.

        Pages:
            in: COMBAT_SUPPORT_LIST
        """
        while 1:
            logger.hr('Gen templates by list', level=2)
            self.device.click_record_clear()
            scroll = self._support_scroll()
            while 1:
                self.gen_support_templates()
                if scroll.at_bottom(main=self):
                    logger.info('Support list reached bottom')
                    break
                self.device.click_record_clear()
                scroll.next_page(main=self)
            self.support_refresh_list()


if __name__ == '__main__':
    """
    Auto Extract support templates

    1. Run config_updater to find missing templates,
        it will print "WARNING: character template not exist: Castorice"
    2. Login to game, stay at whatever page
    3. Run support_extract
    4. Stop manually if you think missing templates are all gathered.
    
    """
    self = SupportExtract('src')
    self.device.screenshot()
    self.goto_support_page()
    self.gen_templates()

    # Test if support can be selected
    # self.support_set('Castorice')
