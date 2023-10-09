from dataclasses import dataclass
from typing import ClassVar

from module.ocr.keyword import Keyword

@dataclass(repr=False)
class Profile(Keyword):
    instances: ClassVar = {}