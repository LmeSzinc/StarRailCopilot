from module.base.utils import random_rectangle_vector_opted
from module.exception import ScriptError
from module.logger import logger
from tasks.combat.assets.assets_combat_prepare import COMBAT_PREPARE
from tasks.combat.assets.assets_combat_support import COMBAT_SUPPORT_LIST, COMBAT_TEAM_SUPPORT, COMBAT_SUPPORT_LIST_GRID
from tasks.combat.support_dev import SupportDev
from tasks.combat.support_tab import support_tab
from tasks.dungeon.dungeon import Dungeon
from tasks.dungeon.keywords import DungeonList, KEYWORDS_DUNGEON_LIST, KEYWORDS_DUNGEON_TAB


class SupportExtract(Dungeon, SupportDev):
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
        self.interval_clear(COMBAT_TEAM_SUPPORT)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self.appear(COMBAT_SUPPORT_LIST):
                break
            if self.appear_then_click(COMBAT_TEAM_SUPPORT, interval=2):
                self.interval_reset(COMBAT_PREPARE)
                continue
            if self.appear_then_click(COMBAT_PREPARE, interval=5):
                continue

    def support_quit(self, skip_first_screenshot=True):
        """
        Pages:
            in: COMBAT_SUPPORT_LIST
            out: SUPPORT_ADD
        """
        logger.info('Support quit')
        self.interval_clear(COMBAT_SUPPORT_LIST)
        COMBAT_TEAM_SUPPORT.clear_offset()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()
            if self.appear(COMBAT_TEAM_SUPPORT):
                break
            if self.appear(COMBAT_SUPPORT_LIST, interval=2):
                self.device.click(COMBAT_TEAM_SUPPORT)
                self.interval_reset(COMBAT_SUPPORT_LIST)
                continue

    def _init_support_page(self):
        """
        Set to stranger tab and full load support list

        Pages:
            in: COMBAT_SUPPORT_LIST
        """
        tab = support_tab()
        tab.set('Support', main=self)
        scroll = self._support_scroll()
        scroll.set_bottom(main=self)
        scroll.set_top(main=self)

    def goto_support_page(self):
        """
        Pages:
            out: COMBAT_SUPPORT_LIST
        """
        if self.appear(COMBAT_SUPPORT_LIST):
            logger.info('Already in support page')
            self._init_support_page()
            return

        if self.appear(COMBAT_TEAM_SUPPORT):
            logger.info('At SUPPORT_ADD')
            self.support_enter()
            self._init_support_page()
            return

        if self.appear(COMBAT_PREPARE):
            logger.info('At COMBAT_PREPARE')
            self.support_enter()
            self._init_support_page()
            return

        logger.info('Goto support page')
        # Goto first calyx golden
        dungeon = KEYWORDS_DUNGEON_LIST.Calyx_Golden_Aether_Planarcadia
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
                p1, p2 = random_rectangle_vector_opted(
                    (0, -320), box=COMBAT_SUPPORT_LIST_GRID.button, random_range=(-20, -30, 20, 30), padding=0)
                self.device.drag(p1, p2, name=f'SUPPORT_DRAG')
                self.device.click_record_clear()
                self.device.screenshot()
            self.support_refresh_list()
            self.support_refresh_wait_top()


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
    # from tasks.character.keywords import KEYWORDS_CHARACTER_LIST
    # self.support_set(KEYWORDS_CHARACTER_LIST.Castorice)
