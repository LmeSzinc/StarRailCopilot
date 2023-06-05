from dataclasses import dataclass
from typing import ClassVar
from module.ocr.keyword import Keyword, parse_name, text_to_variable
from module.exception import ScriptError


@dataclass
class DailyQuest(Keyword):
    instances: ClassVar = {}

    @classmethod
    def find(cls, name, in_current_server=False, ignore_punctuation=True):
        if isinstance(name, Keyword):
            return name
        if isinstance(name, int) or (isinstance(name, str) and name.isdigit()):
            try:
                return cls.instances[int(name)]
            except KeyError:
                pass

        if ignore_punctuation:
            name = parse_name(name)
        else:
            name = str(name)
        instance: Keyword
        for instance in cls.instances.values():
            for keyword in instance._keywords_to_find(
                    in_current_server=in_current_server, ignore_punctuation=ignore_punctuation):
                name = text_to_variable(name)
                keyword = text_to_variable(keyword)
                if name == keyword:
                    return instance

        raise ScriptError(f'Cannot find a {cls.__name__} instance that matches "{name}"')
