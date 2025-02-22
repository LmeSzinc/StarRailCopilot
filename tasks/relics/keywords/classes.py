from dataclasses import dataclass
from functools import cached_property
from typing import ClassVar

from module.ocr.keyword import Keyword


@dataclass(repr=False)
class MainStat(Keyword):
    instances: ClassVar = {}

    def __hash__(self) -> int:
        return super().__hash__()


@dataclass(repr=False)
class SubStat(Keyword):
    instances: ClassVar = {}

    def __hash__(self) -> int:
        return super().__hash__()


@dataclass(repr=False)
class RelicSet(Keyword):
    instances: ClassVar = {}

    setid: int

    def __hash__(self) -> int:
        return super().__hash__()

    @cached_property
    def is_outer(self):
        return bool(100 <= self.setid < 200)

    @cached_property
    def is_inner(self):
        return bool(300 <= self.setid < 400)
