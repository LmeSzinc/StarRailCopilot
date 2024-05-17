import re
from dataclasses import dataclass
from functools import cached_property
from typing import ClassVar

import module.config.server as server
from module.exception import ScriptError

# ord('．') = 65294
REGEX_PUNCTUATION = re.compile(r'[ ,.．\'"“”，。…:：;；!！?？·・•●〇°*※\-—–－/\\|丨\n\t()\[\]（）「」『』【】《》［］]')


def parse_name(n):
    n = REGEX_PUNCTUATION.sub('', str(n)).lower()
    return n.strip()


@dataclass
class Keyword:
    id: int
    name: str
    cn: str
    en: str
    jp: str
    cht: str
    es: str

    """
    Instance attributes and methods
    """

    @cached_property
    def ch(self) -> str:
        return self.cn

    @cached_property
    def cn_parsed(self) -> str:
        return parse_name(self.cn)

    @cached_property
    def en_parsed(self) -> str:
        return parse_name(self.en)

    @cached_property
    def jp_parsed(self) -> str:
        return parse_name(self.jp)

    @cached_property
    def cht_parsed(self) -> str:
        return parse_name(self.cht)

    @cached_property
    def es_parsed(self) -> str:
        return parse_name(self.cht)

    def __str__(self):
        return f'{self.__class__.__name__}({self.name})'

    __repr__ = __str__

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(self.name)

    def __bool__(self):
        return True

    def _keywords_to_find(self, lang: str = None, ignore_punctuation=True):
        if lang is None:
            lang = server.lang

        if lang in server.VALID_LANG:
            match lang:
                case 'cn':
                    if ignore_punctuation:
                        return [self.cn_parsed]
                    else:
                        return [self.cn]
                case 'en':
                    if ignore_punctuation:
                        return [self.en_parsed]
                    else:
                        return [self.en]
                case 'jp':
                    if ignore_punctuation:
                        return [self.jp_parsed]
                    else:
                        return [self.jp]
                case 'cht':
                    if ignore_punctuation:
                        return [self.cht_parsed]
                    else:
                        return [self.cht]
                case 'es':
                    if ignore_punctuation:
                        return [self.es_parsed]
                    else:
                        return [self.es]
        else:
            if ignore_punctuation:
                return [
                    self.cn_parsed,
                    self.en_parsed,
                    self.jp_parsed,
                    self.cht_parsed,
                    self.es_parsed,
                ]
            else:
                return [
                    self.cn,
                    self.en,
                    self.jp,
                    self.cht,
                    self.es,
                ]

    """
    Class attributes and methods

    Note that dataclasses inherited `Keyword` must override `instances` attribute,
    or `instances` will still be a class attribute of base class.
    ```
    @dataclass
    class DungeonNav(Keyword):
        instances: ClassVar = {}
    ```
    """
    # Key: instance ID. Value: instance object.
    instances: ClassVar = {}

    def __post_init__(self):
        self.__class__.instances[self.id] = self

    @classmethod
    def _compare(cls, name, keyword):
        return name == keyword

    @classmethod
    def find(cls, name, lang: str = None, ignore_punctuation=True):
        """
        Args:
            name: Name in any server or instance id.
            lang: Lang to find from
                None to search the names from current server only.
            ignore_punctuation: True to remove punctuations and turn into lowercase before searching.

        Returns:
            Keyword instance.

        Raises:
            ScriptError: If nothing found.
        """
        # Already a keyword
        if isinstance(name, Keyword):
            return name
        # Probably an ID
        if isinstance(name, int) or (isinstance(name, str) and name.isdigit()):
            try:
                return cls.instances[int(name)]
            except KeyError:
                pass
        # Probably a variable name
        if isinstance(name, str) and '_' in name:
            for instance in cls.instances.values():
                if name == instance.name:
                    return instance
        # Probably an in-game name
        if ignore_punctuation:
            name = parse_name(name)
        else:
            name = str(name)
        instance: Keyword
        for instance in cls.instances.values():
            for keyword in instance._keywords_to_find(
                    lang=lang, ignore_punctuation=ignore_punctuation):
                if cls._compare(name, keyword):
                    return instance

        # Not found
        raise ScriptError(f'Cannot find a {cls.__name__} instance that matches "{name}"')

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
        for instance in cls.instances.values():
            if name == instance.name:
                return instance

        # Not found
        raise ScriptError(f'Cannot find a {cls.__name__} instance that matches "{name}"')


class KeywordDigitCounter(Keyword):
    """
    A fake Keyword class to filter digit counters in ocr results
    OcrResultButton.match_keyword will be a str
    """
    @classmethod
    def find(cls, name, lang: str = None, ignore_punctuation=True):
        from module.ocr.ocr import DigitCounter
        if DigitCounter.is_format_matched(name):
            return name
        else:
            raise ScriptError
