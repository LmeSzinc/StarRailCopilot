from dataclasses import dataclass
from typing import ClassVar
from module.ocr.keyword import Keyword, text_to_variable


def __compare__(name, keyword):
    return text_to_variable(name) == text_to_variable(keyword)


@dataclass
class DailyQuest(Keyword):
    instances: ClassVar = {}

    @classmethod
    def _keyword_compare(cls, name: str, keyword: str) -> bool:
        return text_to_variable(name) == text_to_variable(keyword)
