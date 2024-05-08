from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar

from module.ocr.keyword import Keyword


@dataclass(repr=False)
class AssignmentGroup(Keyword):
    instances: ClassVar = {}
    entries: tuple[AssignmentEntry] = ()


@dataclass(repr=False)
class AssignmentEntry(Keyword):
    instances: ClassVar = {}
    group: AssignmentGroup = None

    def __hash__(self) -> int:
        return super().__hash__()

    @classmethod
    def _compare(cls, name, keyword):
        # 2024.05.08 Assignment names are omitted in EN
        if name == keyword:
            return True
        # namelesslandnameless.. Nameless Land, Nameless People
        if name[:17] == keyword[:17]:
            return True
        return False


@dataclass(repr=False)
class AssignmentEntryDetailed(Keyword):
    instances: ClassVar = {}


@dataclass(repr=False)
class AssignmentEventGroup(AssignmentGroup):
    instances: ClassVar = {}


@dataclass(repr=False)
class AssignmentEventEntry(AssignmentEntry):
    instances: ClassVar = {}

    def __hash__(self) -> int:
        return super().__hash__()
