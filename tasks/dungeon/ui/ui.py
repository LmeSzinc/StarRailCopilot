from module.logger import logger
from tasks.dungeon.keywords import DungeonList
from tasks.dungeon.ui.interact import DungeonUIInteract
from tasks.dungeon.ui.llist import DungeonUIList
from tasks.dungeon.ui.nav import DungeonUINav
from tasks.dungeon.ui.state import DungeonState


class DungeonUI(DungeonState, DungeonUINav, DungeonUIList, DungeonUIInteract):
    def dungeon_goto(self, dungeon: DungeonList):
        """
        Returns:
            bool: If success

        Pages:
            in: page_guide, Survival_Index
            out: COMBAT_PREPARE if success
                page_guide if failed

        Examples:
            from tasks.dungeon.keywords import KEYWORDS_DUNGEON_LIST
            self = DungeonUI('src')
            self.device.screenshot()
            self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Survival_Index)
            self.dungeon_goto(KEYWORDS_DUNGEON_LIST.Calyx_Crimson_Harmony)
        """
        # Reset search button
        if dungeon.is_Calyx_Golden \
                or dungeon.is_Calyx_Crimson \
                or dungeon.is_Stagnant_Shadow \
                or dungeon.is_Cavern_of_Corrosion \
                or dungeon.is_Echo_of_War \
                or dungeon.is_Ornament_Extraction:
            self.dungeon_nav_goto(dungeon.dungeon_nav)
            self._dungeon_wait_until_dungeon_list_loaded()
            self.dungeon_insight(dungeon)
            self._dungeon_enter(dungeon)
            return True

        logger.error(f'Goto dungeon {dungeon} is not supported')
        return False
