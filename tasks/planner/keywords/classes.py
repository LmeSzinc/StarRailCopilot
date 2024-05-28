from dataclasses import dataclass
from functools import cached_property
from typing import ClassVar

from module.exception import ScriptError
from module.ocr.keyword import Keyword


@dataclass(repr=False)
class ItemBase(Keyword):
    instances: ClassVar = {}

    rarity: str
    item_id: int
    item_group: int
    dungeon_id: int

    def __post_init__(self):
        self.__class__.instances[self.name] = self

    @classmethod
    def find_name(cls, name):
        """
        Args:
            name: Attribute name of keyword.

        Returns:
            Keyword instance.

        Raises:
            ScriptError: If nothing found.
        """
        if isinstance(name, Keyword):
            return name
        try:
            return cls.instances[name]
        except KeyError:
            # Not found
            raise ScriptError(f'Cannot find a {cls.__name__} instance that matches "{name}"')

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

    @cached_property
    def is_rarity_gold(self):
        return self.rarity == 'SuperRare'

    @cached_property
    def is_rarity_purple(self):
        return self.rarity == 'VeryRare'

    @cached_property
    def is_rarity_blue(self):
        return self.rarity == 'Rare'

    @cached_property
    def is_rarity_green(self):
        return self.rarity == 'NotNormal'

    @cached_property
    def is_ItemAscension(self):
        return self.__class__.__name__ == 'ItemAscension'

    @cached_property
    def is_ItemCalyx(self):
        return self.__class__.__name__ == 'ItemCalyx'

    @cached_property
    def is_ItemCurrency(self):
        return self.__class__.__name__ == 'ItemCurrency'

    @cached_property
    def is_ItemExp(self):
        return self.__class__.__name__ == 'ItemExp'

    @cached_property
    def is_ItemTrace(self):
        return self.__class__.__name__ == 'ItemTrace'

    @cached_property
    def is_ItemWeekly(self):
        return self.__class__.__name__ == 'ItemWeekly'

    @cached_property
    def group_base(self):
        if not self.has_group_base:
            return self
        if self.item_group <= 0:
            raise ScriptError(f'Item {self} has no item_group defined, cannot find group_base')

        for instance in self.__class__.instances.values():
            if instance.item_group == self.item_group and instance.is_rarity_purple:
                return instance

        raise ScriptError(f'Item {self} has no group_base')

    @cached_property
    def has_group_base(self):
        return self.is_ItemCalyx or self.is_ItemExp or self.is_ItemTrace

    @cached_property
    def is_group_base(self):
        if self.has_group_base:
            return self.is_rarity_purple
        else:
            return True


"""
Sub item genres don't have `instances` defined, so all objects are in ItemBase.instances
"""


@dataclass(repr=False)
class ItemAscension(ItemBase):
    pass


@dataclass(repr=False)
class ItemCalyx(ItemBase):
    pass


@dataclass(repr=False)
class ItemCurrency(ItemBase):
    pass


@dataclass(repr=False)
class ItemExp(ItemBase):
    pass


@dataclass(repr=False)
class ItemTrace(ItemBase):
    pass


@dataclass(repr=False)
class ItemWeekly(ItemBase):
    pass
