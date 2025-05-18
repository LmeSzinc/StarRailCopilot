from dataclasses import dataclass
from typing import ClassVar

from module.base.decorator import cached_property
from module.exception import ScriptError
from module.logger import logger
from module.ocr.keyword import Keyword


@dataclass(repr=False)
class Cone(Keyword):
    instances: ClassVar = {}

    # Rare, VeryRare, SuperRare
    rarity: str
    # Character name if this cone is a character specific cone
    # Usually only SuperRare characters has their character specific cones
    character_name: str = ''

    def __hash__(self) -> int:
        return super().__hash__()

    @cached_property
    def character(self):
        """
        Returns:
            CharacterList | None:
        """
        if not self.character_name:
            return None
        from tasks.character.keywords import CharacterList
        try:
            return CharacterList.find_name(self.character_name)
        except ScriptError as e:
            logger.error(e)
            return None

    @property
    def star_string(self):
        if self.rarity == 'SuperRare':
            return '5*'
        if self.rarity == 'VeryRare':
            return '4*'
        if self.rarity == 'Rare':
            return '3*'
        return self.rarity
