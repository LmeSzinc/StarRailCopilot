import re
import typing as t

from dev_tools.keywords.base import GenerateKeyword, text_to_variable
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

    @cached_property
    def character_data(self):
        data = self.read_file('./ExcelOutput/AvatarConfig.json')
        # collab characters
        collab = self.read_file('./ExcelOutput/AvatarConfigLD.json')
        data.extend(collab)
        return data

    @cached_property
    def dict_internal_to_path(self):
        """
        Dict that convert internal path name to official path name
        """
        out = {}
        data = self.read_file('./ExcelOutput/AvatarBaseType.json')
        for row in data:
            internal = row.get('ID', '')
            path = row.get('FirstWordText', '')
            if not internal or not path:
                continue
            out[internal] = text_to_variable(path)
        return out

    def convert_name(self, text: str, keyword: dict) -> str:
        text = REGEX_PUNCTUATION.sub('', text)
        return super().convert_name(text, keyword)

    def iter_keywords(self) -> t.Iterable[dict]:
        # key: character_id
        # value: {'id': 1224, 'text_id': 16417870574330506928, 'combat_type': 'Imaginary', 'path': 'The_Hunt'}

        # iter character config
        names = {}
        for row in self.character_data:
            character_id = row.get('AvatarID', 0)
            name_id = deep_get(row, 'AvatarName.Hash')
            _, name_en = self.find_keyword(name_id, lang='en')
            if name_en in names and not name_en.startswith('Trailblazer'):
                logger.warning(f'Duplicate character name: id={name_id}, name={name_en}')

            base_type = row.get('AvatarBaseType', '')
            path_name = self.dict_internal_to_path.get(base_type, '')
            if not path_name:
                logger.warning(f'Cannot convert character {character_id} base_type {base_type} to path')
                continue
            names[character_id] = {
                'id': character_id,
                'text_id': name_id,
                'type_name': row.get('DamageType', ''),
                'path_name': path_name,
            }

        # iter character icon to update name
        for row in self.data:
            icon = deep_get(row, ['ItemIconPath'], default='')
            # Must be a avatar icon
            if not icon.startswith('SpriteOutput/AvatarRoundIcon/Avatar'):
                continue

            name_id = deep_get(row, 'ItemName.Hash')
            # 201313 -> 1313
            character_id = row.get('ID') % 10000
            _, name_en = self.find_keyword(name_id, lang='en')
            if name_en in names and not name_en.startswith('Trailblazer'):
                logger.warning(f'Duplicate character name: id={name_id}, name={name_en}')
            row = names.get(character_id)
            if not row:
                logger.warning(f'Character {character_id} defined in AvatarPlayerIcon but not in AvatarConfig')
                continue
            row['text_id'] = name_id

        # Sort characters by character ID
        names = sorted(names.items(), key=lambda kv: kv[1]['id'])

        for character_id, row in names:
            # Keep only one trailblazer character per path
            if character_id > 8000 and character_id % 2 == 1:
                continue
            yield row


class GenerateCombatType(GenerateKeyword):
    output_file = './tasks/character/keywords/combat_type.py'

    def iter_keywords(self) -> t.Iterable[dict]:
        yield from self.iter_keywords_from_text(
            ['物理', '火', '冰', '雷', '风', '量子', '虚数'],
            lang='cn',
        )


class GenerateCharacterPath(GenerateKeyword):
    output_file = './tasks/character/keywords/character_path.py'

    def iter_keywords(self) -> t.Iterable[dict]:
        data = self.read_file('./ExcelOutput/AvatarBaseType.json')
        for row in data:
            path_name = row.get('FirstWordText', '')
            if not path_name:
                continue
            text_id = deep_get(row, 'BaseTypeText.Hash', '')
            if not text_id:
                continue
            yield {
                'text_id': text_id
            }


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
        'Harscyline': 'Hysilens',
        'DanHengPT': 'DanHengPermansorTerrae',
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

        dict_height = {
            k: v for k, v in sorted(
                dict_height.items(), key=lambda item: (height_index.index(item[1]), item[0])
            )
        }

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
