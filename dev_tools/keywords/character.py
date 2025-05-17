import re
import typing as t

from dev_tools.keywords.base import GenerateKeyword
from module.base.decorator import cached_property
from module.config.deep import deep_get
from module.exception import ScriptError
from module.logger import logger
from module.ocr.keyword import REGEX_PUNCTUATION


class GenerateCharacterList(GenerateKeyword):
    output_file = './tasks/character/keywords/character_list.py'

    @cached_property
    def data(self):
        # Player profile avatar
        return self.read_file('./ExcelOutput/ItemConfigAvatarPlayerIcon.json')

    def convert_name(self, text: str, keyword: dict) -> str:
        text = REGEX_PUNCTUATION.sub('', text)
        return super().convert_name(text, keyword)

    def iter_keywords(self) -> t.Iterable[dict]:
        names = {}
        for row in self.data:
            icon = deep_get(row, ['ItemIconPath'], default='')
            # Must be a avartar icon
            if not icon.startswith('SpriteOutput/AvatarRoundIcon/Avatar'):
                continue

            name_id = deep_get(row, 'ItemName.Hash')
            _, name_en = self.find_keyword(name_id, lang='en')
            if name_en in names and not name_en.startswith('Trailblazer'):
                logger.warning(f'Duplicate character name: id={name_id}, name={name_en}')
            names[name_en] = name_id

        # Sort characters by their English names
        names = sorted(names.items(), key=lambda kv: kv[0])

        for _, name_id in names:
            yield dict(
                text_id=name_id,
            )


class GenerateCombatType(GenerateKeyword):
    output_file = './tasks/character/keywords/combat_type.py'

    def iter_keywords(self) -> t.Iterable[dict]:
        yield from self.iter_keywords_from_text(
            ['物理', '火', '冰', '雷', '风', '量子', '虚数'],
            lang='cn',
        )


def convert_inner_character_to_keyword(name):
    convert_dict = {
        'Mar_7th_00': 'March7thPreservation',
        'Mar_7th_10': 'March7thTheHunt',
    }
    if name in convert_dict:
        return convert_dict[name]
    name = re.sub(r'_\d\d$', '', name)
    convert_dict = {
        'Silwolf': 'SilverWolf',
        'Klara': 'Clara',
        'Mar_7th': 'March7th',
        'PlayerGirl': 'TrailblazerFemale',
        'PlayerBoy': 'TrailblazerMale',
        'Ren': 'Blade',
        'DanHengIL': 'DanHengImbibitorLunae',
        'Topaz': 'TopazNumby',
        'Dr_Ratio': 'DrRatio',
        'Mydeimos': 'Mydei',
    }
    return convert_dict.get(name, name)


class GenerateCharacterHeight(GenerateKeyword):
    output_file = './tasks/character/keywords/height.py'

    @cached_property
    def data(self):
        # Player profile avatar
        return self.read_file('./ExcelOutput/FreeStyleCharacterInfo.json')

    def generate_content(self):
        # NPC_Avatar_Girl_Silwolf_00
        # 00, 10 are for different trace
        regex = re.compile(r'NPC_Avatar_(?P<height>.*?)_(?P<character>.*?_\d0)$')
        dict_height = {}
        height_index = ['Kid', 'Girl', 'Boy', 'Maid', 'Miss', 'Lady', 'Lad', 'Male']
        for row in self.data:
            avatar = deep_get(row, 'FreeStyleCharacterID', default='')
            if res := regex.search(avatar):
                character, height = res.group('character'), res.group('height')
                if height not in height_index:
                    continue
                dict_height[character] = height

        dict_height = {k: v for k, v in sorted(dict_height.items(), key=lambda item: height_index.index(item[1]))}

        from tasks.character.keywords.classes import CharacterList
        with self.gen.Dict('CHARACTER_HEIGHT'):
            for character, height in dict_height.items():
                # print(character, height)
                character = convert_inner_character_to_keyword(character)
                try:
                    CharacterList.find_name(character)
                except ScriptError:
                    print(f'Character height data {character} is not defined')
                    continue
                self.gen.DictItem(key=character, value=height)
