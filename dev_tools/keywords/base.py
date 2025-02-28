import os
import re
import typing as t
from functools import cached_property

from module.base.code_generator import CodeGenerator
from module.config.utils import read_file
from module.logger import logger

UI_LANGUAGES = ['cn', 'cht', 'en', 'jp', 'es']


class TextMap:
    DATA_FOLDER = ''

    def __init__(self, lang: str):
        self.lang = lang

    def __contains__(self, name: t.Union[int, str]) -> bool:
        if isinstance(name, int) or (isinstance(name, str) and name.isdigit()):
            return int(name) in self.data
        return False

    @cached_property
    def data(self) -> dict[int, str]:
        if not os.path.exists(TextMap.DATA_FOLDER):
            logger.critical('`TextMap.DATA_FOLDER` does not exist, please set it to your path to StarRailData')
            exit(1)

        if self.lang == 'cn':
            lang = 'chs'
        else:
            lang = self.lang
        file = os.path.join(TextMap.DATA_FOLDER, 'TextMap', f'TextMap{lang.upper()}.json')
        data = {}
        for id_, text in read_file(file).items():
            text = text.replace('\u00A0', '')
            text = text.replace(r'{NICKNAME}', 'Trailblazer')
            data[int(id_)] = text
        return data

    def find(self, name: t.Union[int, str]) -> tuple[int, str]:
        """
        Args:
            name:

        Returns:
            text id (hash in TextMap)
            text
        """
        if isinstance(name, int) or (isinstance(name, str) and name.isdigit()):
            text_id = int(name)
            # if text_id < 10000000000:
            #     text_id = xxhash.xxh64(str(text_id)).intdigest()

            try:
                return text_id, self.data[text_id]
            except KeyError:
                pass

        name = str(name)
        for row_id, row_name in self.data.items():
            if row_id >= 0 and row_name == name:
                return row_id, row_name
        for row_id, row_name in self.data.items():
            if row_name == name:
                return row_id, row_name
        logger.error(f'Cannot find name: "{name}" in language {self.lang}')
        return 0, ''


def text_to_variable(text):
    text = re.sub("'s |s' ", '_', text)
    text = re.sub(r'[ \-—–:\'/•.™]+', '_', text)
    text = re.sub(r'[█]+', '', text)
    text = re.sub(r'[(),#"?!&%*]|</?\w+>', '', text)
    # text = re.sub(r'[#_]?\d+(_times?)?', '', text)
    text = re.sub(r'<color=#?\w+>', '', text)
    text = re.sub(r'^\d+', '', text)
    text = replace_non_ascii(text)
    return text.strip('_')


def replace_templates(text: str) -> str:
    """
    Replace templates in data to make sure it equals to what is shown in game

    Examples:
        replace_templates("Complete Echo of War #4 time(s)")
        == "Complete Echo of War 1 time(s)"
    """
    text = re.sub(r'#4', '1', text)
    text = re.sub(r'</?\w+>', '', text)
    text = re.sub(r'<color=#?\w+>', '', text)
    text = re.sub(r'{.*?}', '', text)
    return text


def replace_non_ascii(text: str) -> str:
    text = text.replace('ī', 'i')
    text = text.replace('é', 'e')
    text = text.replace('Ā', 'A')
    return text


class GenerateKeyword:
    text_map: dict[str, TextMap] = {lang: TextMap(lang) for lang in UI_LANGUAGES}

    # text_map['cn'] = TextMap('chs')

    @staticmethod
    def read_file(file: str) -> list:
        """
        Args:
            file: ./ExcelOutput/GameplayGuideData.json

        Returns:
            list
        """
        file = os.path.join(TextMap.DATA_FOLDER, file)
        data = read_file(file)
        if not data:
            logger.error(f'Empty data from file {file}')
        return data

    @classmethod
    def find_keyword(cls, keyword, lang) -> tuple[int, str]:
        """
        Args:
            keyword: text string or text id
            lang: Language to find

        Returns:
            text id (hash in TextMap)
            text
        """
        text_map = cls.text_map[lang]
        return text_map.find(keyword)

    output_file = ''
    DEFAULT_KEYWORD_NAME = 'Unnamed_Keyword'

    def __init__(self):
        self.gen = CodeGenerator()
        self.keyword_class = self.__class__.__name__.removeprefix('Generate')
        self.keyword_index = 0
        self.keyword_format = {
            'id': 0,
            'name': self.DEFAULT_KEYWORD_NAME
        }
        for lang in UI_LANGUAGES:
            self.keyword_format[lang] = ''

    def gen_import(self):
        self.gen.Import(
            f"""
            from .classes import {self.keyword_class}
            """
        )

    def iter_keywords(self) -> t.Iterable[dict]:
        """
        Yields
            dict: {'text_id': 123456, 'any_attr': 1}
        """
        pass

    def iter_keywords_from_text(self, text_list: list[str], lang: str) -> t.Iterable[dict]:
        for text in text_list:
            text_id, _ = self.find_keyword(text, lang)
            yield {
                'text_id': text_id
            }

    def convert_name(self, text: str, keyword: dict) -> str:
        return text_to_variable(replace_templates(text))

    def convert_keyword(self, text: str, lang: str) -> str:
        text = replace_templates(text)
        text = replace_non_ascii(text)
        return text

    def iter_rows(self) -> t.Iterable[dict]:
        for keyword in self.iter_keywords():
            keyword = self.format_keywords(keyword)
            if not keyword:
                continue
            yield keyword

    def format_keywords(self, keyword: dict) -> dict | None:
        base = self.keyword_format.copy()
        text_id = keyword.pop('text_id')
        if text_id is None:
            logger.warning(f'Empty text_id in {keyword}')
            return
        # id
        self.keyword_index += 1
        base['id'] = self.keyword_index
        # Attrs
        base.update(keyword)
        # Name
        if base['name'] == self.DEFAULT_KEYWORD_NAME:
            _, name = self.find_keyword(text_id, lang='en')
            name = self.convert_name(name, keyword=base)
            base['name'] = name
        if not base['name']:
            logger.warning(f'Empty name for {keyword}')
            return None
        # Translations
        for lang in UI_LANGUAGES:
            value = self.find_keyword(text_id, lang=lang)[1]
            value = self.convert_keyword(value, lang=lang)
            base[lang] = value
        return base

    def generate_content(self):
        self.gen_import()
        self.gen.CommentAutoGenerage('dev_tools.keyword_extract')

        for keyword in self.iter_rows():
            with self.gen.Object(key=keyword['name'], object_class=self.keyword_class):
                for key, value in keyword.items():
                    self.gen.ObjectAttr(key, value)

    def generate(self):
        self.generate_content()

        if self.output_file:
            print(f'Write {self.output_file}')
            self.gen.write(self.output_file)

    def __call__(self, *args, **kwargs):
        self.generate()


class ShareData(GenerateKeyword):
    @cached_property
    def GameplayGuideData(self):
        return self.read_file('./ExcelOutput/GameplayGuideData.json')

    @cached_property
    def MappingInfo(self):
        return self.read_file('./ExcelOutput/MappingInfo.json')

    @cached_property
    def ItemConfig(self):
        return self.read_file('./ExcelOutput/ItemConfig.json')


SHARE_DATA = ShareData()
