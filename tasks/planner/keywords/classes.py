from dataclasses import dataclass
from functools import cached_property
from typing import ClassVar

from module.ocr.keyword import Keyword


@dataclass(repr=False)
class ItemBase(Keyword):
    instances: ClassVar = {}

    rarity: str
    item_id: int
    item_group: int
    dungeon_id: int

    @cached_property
    def dungeon(self):
        """
        Dungeon that drops this item

        Returns:
            DungeonList: DungeonList object or None
        """
        if self.dungeon_id > 0:
            from tasks.dungeon.keywords.classes import DungeonList
            return DungeonList.find_dungeon_id(self.dungeon_id)
        else:
            return None


@dataclass(repr=False)
class ItemAscension(ItemBase):
    instances: ClassVar = {}


@dataclass(repr=False)
class ItemCalyx(ItemBase):
    instances: ClassVar = {}


@dataclass(repr=False)
class ItemCurrency(ItemBase):
    instances: ClassVar = {}


@dataclass(repr=False)
class ItemExp(ItemBase):
    instances: ClassVar = {}


@dataclass(repr=False)
class ItemTrace(ItemBase):
    instances: ClassVar = {}


@dataclass(repr=False)
class ItemWeekly(ItemBase):
    instances: ClassVar = {}
