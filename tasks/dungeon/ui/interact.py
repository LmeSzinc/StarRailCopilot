import re

from module.exception import ScriptError
from module.logger import logger
from tasks.base.ui import UI
from tasks.combat.assets.assets_combat_interact import DUNGEON_COMBAT_INTERACT, DUNGEON_COMBAT_INTERACT_TEXT
from tasks.dungeon.keywords import (
    DungeonList,
    DungeonNav,
    KEYWORDS_DUNGEON_LIST,
    KEYWORDS_DUNGEON_NAV
)
from tasks.dungeon.ui.llist import OcrDungeonName


class DungeonUIInteract(UI):
    def get_dungeon_interact(self) -> DungeonList | None:
        """
        Pages:
            in: page_main
        """
        if not self.appear(DUNGEON_COMBAT_INTERACT):
            logger.info('No dungeon interact')
            return None

        self.acquire_lang_checked()

        ocr = OcrDungeonName(DUNGEON_COMBAT_INTERACT_TEXT)
        result = ocr.detect_and_ocr(self.device.image)

        dungeon = None
        # Special match names in English
        # Second row must have at least 3 characters which is the shortest name "Ire"
        # Stangnant Shadow: Shape of
        # Quanta
        if len(result) == 2 and len(result[1].ocr_text) >= 3:
            first, second = result[0].ocr_text, result[1].ocr_text
            if re.search(r'Stagnant\s*Shadow', first):
                dungeon = DungeonList.find_dungeon_by_string(en=second, is_Stagnant_Shadow=True)
            elif re.search(r'Cavern\s*of\s*Corrosion', first):
                dungeon = DungeonList.find_dungeon_by_string(en=second, is_Cavern_of_Corrosion=True)
            elif re.search(r'Echo\s*of\s*War', first):
                dungeon = DungeonList.find_dungeon_by_string(en=second, is_Echo_of_War=True)
            elif re.search(r'Calyx[\s(]+Golden', first):
                dungeon = DungeonList.find_dungeon_by_string(en=second, is_Calyx_Golden=True, world=self.plane.world)
            elif re.search(r'Calyx[\s(]+Crimson', first):
                dungeon = DungeonList.find_dungeon_by_string(en=second, is_Calyx_Crimson=True, plane=self.plane)
        if dungeon is not None:
            logger.attr('DungeonInteract', dungeon)
            return dungeon

        # Join
        result = ' '.join([row.ocr_text for row in result])

        # Special match names in Chinese
        # Only calyxes need spacial match
        if res := re.search(r'(^.+之蕾)', result):
            dungeon = DungeonList.find_dungeon_by_string(cn=res.group(1), is_Calyx_Crimson=True, plane=self.plane)
            if dungeon is not None:
                logger.attr('DungeonInteract', dungeon)
                return dungeon
            dungeon = DungeonList.find_dungeon_by_string(cn=res.group(1), is_Calyx_Golden=True, world=self.plane.world)
            if dungeon is not None:
                logger.attr('DungeonInteract', dungeon)
                return dungeon

        # Dungeons
        try:
            dungeon = DungeonList.find(result)
            logger.attr('DungeonInteract', dungeon)
            return dungeon
        except ScriptError:
            pass
        # Simulated Universe returns Simulated_Universe_World_1
        try:
            dungeon = DungeonNav.find(result)
            if dungeon == KEYWORDS_DUNGEON_NAV.Simulated_Universe:
                dungeon = KEYWORDS_DUNGEON_LIST.Simulated_Universe_World_1
                logger.attr('DungeonInteract', dungeon)
                return dungeon
        except ScriptError:
            pass
        # Unknown
        logger.attr('DungeonInteract', None)
        return None
