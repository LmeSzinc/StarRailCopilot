from dataclasses import dataclass
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
