import itertools
import os
import re
import typing as t
from collections import defaultdict
from functools import cache, cached_property
from hashlib import md5

from module.base.code_generator import CodeGenerator
from module.config.utils import deep_get, read_file
from module.exception import ScriptError
from module.logger import logger

UI_LANGUAGES = ['cn', 'cht', 'en', 'jp', 'es']


def text_to_variable(text):
    text = re.sub("'s |s' ", '_', text)
    text = re.sub('[ \-—:\'/•.]+', '_', text)
    text = re.sub(r'[(),#"?!&%*]|</?\w+>', '', text)
    # text = re.sub(r'[#_]?\d+(_times?)?', '', text)
    text = re.sub(r'<color=#?\w+>', '', text)
    text = text.replace('é', 'e')
    return text.strip('_')


def dungeon_name(name: str) -> str:
    name = text_to_variable(name)
    name = re.sub('Bud_of_(Memories|Aether|Treasures)', r'Calyx_Golden_\1', name)
    name = re.sub('Bud_of_(.*)', r'Calyx_Crimson_\1', name).replace('Calyx_Crimson_Calyx_Crimson_', 'Calyx_Crimson_')
    name = re.sub('Shape_of_(.*)', r'Stagnant_Shadow_\1', name)
    name = re.sub('Path_of_(.*)', r'Cavern_of_Corrosion_Path_of_\1', name)
    if name in ['Destruction_Beginning', 'End_of_the_Eternal_Freeze', 'Divine_Seed', 'Borehole_Planet_Old_Crater']:
        name = f'Echo_of_War_{name}'
    if name in ['The_Swarm_Disaster', 'Gold_and_Gears']:
        name = f'Simulated_Universe_{name}'
    return name


def blessing_name(name: str) -> str:
    name = text_to_variable(name)
    name = re.sub(r'^\d', lambda match: f"_{match.group(0)}", name)
    return name


def character_name(name: str) -> str:
    name = text_to_variable(name)
    name = re.sub('_', '', name)
    return name


def convert_inner_character_to_keyword(name):
    convert_dict = {
        'Silwolf': 'SilverWolf',
        'Klara': 'Clara',
        'Mar_7th': 'March7th',
        'PlayerGirl': 'TrailblazerFemale',
        'PlayerBoy': 'TrailblazerMale',
        'Ren': 'Blade',
    }
    return convert_dict.get(name, name)


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
        file = os.path.join(TextMap.DATA_FOLDER, 'TextMap', f'TextMap{self.lang.upper()}.json')
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
            name = int(name)
            try:
                return name, self.data[name]
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


class KeywordExtract:
    def __init__(self):
        self.text_map: dict[str, TextMap] = {lang: TextMap(lang) for lang in UI_LANGUAGES}
        self.text_map['cn'] = TextMap('chs')
        self.keywords_id: list[int] = []

    def iter_guide(self) -> t.Iterable[int]:
        file = os.path.join(TextMap.DATA_FOLDER, './ExcelOutput/GameplayGuideData.json')
        # visited = set()
        temp_save = ""
        for data in read_file(file).values():
            hash_ = deep_get(data, keys='Name.Hash')
            _, name = self.find_keyword(hash_, lang='cn')
            if '永屹之城遗秘' in name:  # load after all forgotten hall to make sure the same order in Game UI
                temp_save = hash_
                continue
            if '忘却之庭' in name:
                continue
                # if name in visited:
                #     continue
                # visited.add(name)
            yield hash_
        yield temp_save
        # Consider rogue DLC as a dungeon
        yield '寰宇蝗灾'
        yield '黄金与机械'
        # 'Memory of Chaos' is not a real dungeon, but represents a group
        yield '混沌回忆'
        yield '天艟求仙迷航录'
        yield '永屹之城遗秘'

    def find_keyword(self, keyword, lang) -> tuple[int, str]:
        """
        Args:
            keyword: text string or text id
            lang: Language to find

        Returns:
            text id (hash in TextMap)
            text
        """
        text_map = self.text_map[lang]
        return text_map.find(keyword)

    def load_keywords(self, keywords: list[str | int], lang='cn'):
        text_map = self.text_map[lang]
        keywords_id = [text_map.find(keyword) for keyword in keywords]
        self.keywords_id = [keyword[0] for keyword in keywords_id if keyword[0] != 0 and keyword[1].strip()]

    def clear_keywords(self):
        self.keywords_id = []

    def write_keywords(
            self,
            keyword_class,
            output_file: str = '',
            text_convert=text_to_variable,
            generator: CodeGenerator = None,
            extra_attrs: dict[str, dict] = None
    ):
        """
        Args:
            keyword_class:
            output_file:
            text_convert:
            generator: Reuse an existing code generator
            extra_attrs: Extra attributes write in keywords
        """
        if generator is None:
            gen = CodeGenerator()
            gen.Import(f"""
            from .classes import {keyword_class}
            """)
            gen.CommentAutoGenerage('dev_tools.keyword_extract')
        else:
            gen = generator

        last_id = getattr(gen, 'last_id', 0)
        if extra_attrs:
            keyword_num = len(self.keywords_id)
            for attr_key, attr_value in extra_attrs.items():
                if len(attr_value) != keyword_num:
                    print(f"Extra attribute {attr_key} does not match the size of keywords")
                    return
        for index, keyword in enumerate(self.keywords_id):
            _, name = self.find_keyword(keyword, lang='en')
            name = text_convert(replace_templates(name))
            with gen.Object(key=name, object_class=keyword_class):
                gen.ObjectAttr(key='id', value=index + last_id + 1)
                gen.ObjectAttr(key='name', value=name)
                for lang in UI_LANGUAGES:
                    gen.ObjectAttr(key=lang, value=replace_templates(self.find_keyword(keyword, lang=lang)[1]))
                if extra_attrs:
                    for attr_key, attr_value in extra_attrs.items():
                        gen.ObjectAttr(key=attr_key, value=attr_value[keyword])
                gen.last_id = index + last_id + 1

        if output_file:
            print(f'Write {output_file}')
            gen.write(output_file)
            self.clear_keywords()
        return gen

    def load_quests(self, quests, lang='cn'):
        """
        Load a set of quest keywords

        Args:
            quests: iterable quest id collection
            lang:

        """
        quest_data = read_file(os.path.join(TextMap.DATA_FOLDER, 'ExcelOutput', 'QuestData.json'))
        quests_hash = [quest_data[str(quest_id)]["QuestTitle"]["Hash"] for quest_id in quests]
        quest_keywords = list(dict.fromkeys([self.text_map[lang].find(quest_hash)[1] for quest_hash in quests_hash]))
        self.load_keywords(quest_keywords, lang)

    def write_daily_quest_keywords(self):
        text_convert = text_to_variable
        keyword_class = 'DailyQuest'
        gen = CodeGenerator()
        gen.Import(f"""
        from .classes import {keyword_class}
        """)
        gen.CommentAutoGenerage('dev_tools.keyword_extract')

        old_quest = [
            "Go_on_assignment_1_time", # -> Dispatch_1_assignments
            "Complete_1_stage_in_Simulated_Universe_Any_world", # -> Complete_Simulated_Universe_1_times
            "Complete_Calyx_Crimson_1_time", # -> Clear_Calyx_Crimson_1_times
            "Enter_combat_by_attacking_enemy_Weakness_and_win_3_times", # -> Enter_combat_by_attacking_enemie_Weakness_and_win_1_times
            "Use_Technique_2_times", # -> Use_Technique_1_times
            "Destroy_3_destructible_objects", # -> Destroy_1_destructible_objects
            "Obtain_victory_in_combat_with_Support_Characters_1_time", # -> Obtain_victory_in_combat_with_Support_Characters_1_times
            "Level_up_any_character_1_time", # -> Level_up_any_character_1_times
            "Level_up_any_Light_Cone_1_time", # -> Level_up_any_Light_Cone_1_times
            "Synthesize_Consumable_1_time", # -> Use_the_Omni_Synthesizer_1_times
            "Synthesize_material_1_time", # -> Use_the_Omni_Synthesizer_1_times
            "Take_1_photo", # -> Take_photos_1_times
            "Level_up_any_Relic_1_time", # -> Level_up_any_Relic_1_times
        ]

        correct_times = {
        #    "Dispatch_1_assignments":  1,
        #    "Complete_Simulated_Universe_1_times": 1,
        #    "Clear_Calyx_Crimson_1_times": 1,
            "Enter_combat_by_attacking_enemie_Weakness_and_win_1_times": 3,
            "Use_Technique_1_times": 2,
            "Destroy_1_destructible_objects": 3,
        #    "Obtain_victory_in_combat_with_Support_Characters_1_times": 1,
        #    "Level_up_any_character_1_times": 1,
        #    "Level_up_any_Light_Cone_1_times": 1,
        #    "Use_the_Omni_Synthesizer_1_times": 1,
        #    "Take_photos_1_times": 1,
        #    "Level_up_any_Relic_1_times": 1,
            "Consume_1_Trailblaze_Power": 120

        }
        def replace_templates_quest(text: str, correct_time = 1) -> str:
            text = replace_templates(text)
            text = text.replace('1', f'{correct_time}')
            return text

        last_id = getattr(gen, 'last_id', 0)
        for index, keyword in enumerate(self.keywords_id):
            _, old_name = self.find_keyword(keyword, lang='en')
            old_name = text_convert(replace_templates(old_name))
            if old_name in old_quest:
                continue
            name = old_name.replace('1', str(correct_times.setdefault(old_name, 1)))

            with gen.Object(key=name, object_class=keyword_class):
                gen.ObjectAttr(key='id', value=index + last_id + 1)
                gen.ObjectAttr(key='name', value=name)
                for lang in UI_LANGUAGES:
                    gen.ObjectAttr(key=lang, value=replace_templates_quest(self.find_keyword(keyword, lang=lang)[1], correct_times.setdefault(old_name, 1)))
                gen.last_id = index + last_id + 1

        output_file = './tasks/daily/keywords/daily_quest.py'
        print(f'Write {output_file}')
        gen.write(output_file)
        self.clear_keywords()
        return gen

    def generate_daily_quests(self):
        daily_quest = read_file(os.path.join(TextMap.DATA_FOLDER, 'ExcelOutput', 'DailyQuest.json'))
        self.load_quests(daily_quest.keys())
        self.write_daily_quest_keywords()

    def load_character_name_keywords(self, lang='en'):
        file_name = 'ItemConfigAvatarPlayerIcon.json'
        path = os.path.join(TextMap.DATA_FOLDER, 'ExcelOutput', file_name)
        character_data = read_file(path)
        characters_hash = [character_data[key]["ItemName"]["Hash"] for key in character_data]

        text_map = self.text_map[lang]
        keywords_id = sorted(
            {text_map.find(keyword)[1] for keyword in characters_hash}
        )
        self.load_keywords(keywords_id, lang)

    def generate_shadow_with_characters(self):
        # Damage type -> damage hash
        damage_info = dict()
        for type_name, data in read_file(os.path.join(
            TextMap.DATA_FOLDER, 'ExcelOutput',
            'DamageType.json'
        )).items():
            damage_info[type_name] = deep_get(data, 'DamageTypeName.Hash')
        # Character id -> character hash & damage type
        character_info = dict()
        for data in read_file(os.path.join(
            TextMap.DATA_FOLDER, 'ExcelOutput',
            'AvatarConfig.json'
        )).values():
            name_hash = deep_get(data, 'AvatarName.Hash')
            damage_type = deep_get(data, 'DamageType')
            character_info[data['AvatarID']] = (
                name_hash, damage_info[damage_type])
        # Item id -> character id
        promotion_info = defaultdict(list)
        for data in read_file(os.path.join(
            TextMap.DATA_FOLDER, 'ExcelOutput',
            'AvatarPromotionConfig.json'
        )).values():
            character_id = deep_get(data, '0.AvatarID')
            item_id = deep_get(data, '2.PromotionCostList')[-1]['ItemID']
            promotion_info[item_id].append(character_info[character_id])
        # Shadow hash -> item id
        shadow_info = dict()
        for data in read_file(os.path.join(
            TextMap.DATA_FOLDER, 'ExcelOutput',
            'MappingInfo.json'
        )).values():
            farm_type = deep_get(data, '0.FarmType')
            if farm_type != 'ELEMENT':
                continue
            shadow_hash = deep_get(data, '0.Name.Hash')
            item_id = deep_get(data, '5.DisplayItemList')[-1]['ItemID']
            shadow_info[shadow_hash] = promotion_info[item_id]
        prefix_dict = {
            'cn': '角色晋阶材料：',
            'cht': '角色晉階材料：',
            'jp': 'キャラクター昇格素材：',
            'en': 'Ascension: ',
            'es': 'Ascension: '
        }
        keyword_class = 'DungeonDetailed'
        output_file = './tasks/dungeon/keywords/dungeon_detailed.py'
        gen = CodeGenerator()
        gen.Import(f"""
        from .classes import {keyword_class}
        """)
        gen.CommentAutoGenerage('dev_tools.keyword_extract')
        for index, (keyword, characters) in enumerate(shadow_info.items()):
            _, name = self.find_keyword(keyword, lang='en')
            name = text_to_variable(name).replace('Shape_of_', '')
            with gen.Object(key=name, object_class=keyword_class):
                gen.ObjectAttr(key='id', value=index + 1)
                gen.ObjectAttr(key='name', value=name)
                for lang in UI_LANGUAGES:
                    character_names = ' / '.join([
                        replace_templates(self.find_keyword(c[0], lang)[1])
                        for c in characters
                    ])
                    damage_type = self.find_keyword(characters[0][1], lang)[1]
                    if lang in {'en', 'es'}:
                        value = f'{prefix_dict[lang]}{damage_type} ({character_names})'
                    else:
                        value = f'{prefix_dict[lang]}{damage_type}（{character_names}）'
                    gen.ObjectAttr(key=lang, value=value)
        print(f'Write {output_file}')
        gen.write(output_file)
        self.clear_keywords()

    def generate_forgotten_hall_stages(self):
        keyword_class = "ForgottenHallStage"
        output_file = './tasks/forgotten_hall/keywords/stage.py'
        gen = CodeGenerator()
        gen.Import(f"""
        from .classes import {keyword_class}
        """)
        gen.CommentAutoGenerage('dev_tools.keyword_extract')
        for stage_id in range(1, 16):
            id_str = str(stage_id).rjust(2, '0')
            with gen.Object(key=f"Stage_{stage_id}", object_class=keyword_class):
                gen.ObjectAttr(key='id', value=stage_id)
                gen.ObjectAttr(key='name', value=id_str)
                for lang in UI_LANGUAGES:
                    gen.ObjectAttr(key=lang, value=id_str)

        print(f'Write {output_file}')
        gen.write(output_file)
        self.clear_keywords()

    def generate_assignments(self):
        self.load_keywords(['空间站特派'])
        self.write_keywords(
            keyword_class='AssignmentEventGroup',
            output_file='./tasks/assignment/keywords/event_group.py'
        )
        for file_name, class_name, output_file in (
            ('ExpeditionGroup.json', 'AssignmentGroup', './tasks/assignment/keywords/group.py'),
            ('ExpeditionData.json', 'AssignmentEntry', './tasks/assignment/keywords/entry.py'),
            ('ActivityExpedition.json', 'AssignmentEventEntry', './tasks/assignment/keywords/event_entry.py'),
        ):
            file = os.path.join(TextMap.DATA_FOLDER, 'ExcelOutput', file_name)
            self.load_keywords(deep_get(data, 'Name.Hash') for data in read_file(file).values())
            self.write_keywords(keyword_class=class_name, output_file=output_file)

    def generate_map_planes(self):
        planes = {
            'Special': ['黑塔的办公室', '锋芒崭露'],
            'Rogue': [ '区域-战斗', '区域-事件', '区域-遭遇', '区域-休整', '区域-精英', '区域-首领', '区域-交易'],
            'Herta': ['观景车厢', '主控舱段', '基座舱段', '收容舱段', '支援舱段', '禁闭舱段'],
            'Jarilo': ['行政区', '城郊雪原', '边缘通路', '铁卫禁区', '残响回廊', '永冬岭',
                       '造物之柱', '旧武器试验场', '磐岩镇', '大矿区', '铆钉镇', '机械聚落'],
            'Luofu': ['星槎海中枢', '流云渡', '迴星港', '长乐天', '金人巷', '太卜司',
                      '工造司', '绥园', '丹鼎司', '鳞渊境'],
        }

        def text_convert(world_):
            def text_convert_wrapper(name):
                name = text_to_variable(name).replace('_', '')
                name = f'{world_}_{name}'
                return name

            return text_convert_wrapper

        gen = None
        for world, plane in planes.items():
            self.load_keywords(plane)
            gen = self.write_keywords(keyword_class='MapPlane', output_file='',
                                      text_convert=text_convert(world), generator=gen)
        gen.write('./tasks/map/keywords/plane.py')
        self.load_keywords(['Herta Space Station', 'Jarilo-VI', 'The Xianzhou Luofu'], lang='en')
        self.write_keywords(keyword_class='MapWorld', output_file='./tasks/map/keywords/world.py')

    def generate_character_keywords(self):
        self.load_character_name_keywords()
        self.write_keywords(keyword_class='CharacterList', output_file='./tasks/character/keywords/character_list.py',
                            text_convert=character_name)
        # Generate character height
        characters = read_file(os.path.join(TextMap.DATA_FOLDER, 'ExcelOutput', 'FreeStyleCharacterConfig.json'))
        regex = re.compile(r'NPC_Avatar_(?P<height>.*?)_(?P<character>.*?)_00')
        gen = CodeGenerator()
        dict_height = {}
        height_index = ['Kid', 'Girl', 'Boy', 'Maid', 'Miss', 'Lady', 'Lad', 'Male']
        for key in characters.keys():
            if res := regex.search(key):
                character, height = res.group('character'), res.group('height')
                if height not in height_index:
                    continue
                dict_height[character] = height
        dict_height = {k: v for k, v in sorted(dict_height.items(), key=lambda item: height_index.index(item[1]))}
        from tasks.character.keywords.classes import CharacterList
        with gen.Dict('CHARACTER_HEIGHT'):
            for character, height in dict_height.items():
                character = convert_inner_character_to_keyword(character)
                try:
                    CharacterList.find_name(character)
                except ScriptError:
                    print(f'Character height data {character} is not defined')
                    continue
                gen.DictItem(key=character, value=height)
        gen.write('./tasks/character/keywords/height.py')

    def generate_battle_pass_quests(self):
        battle_pass_quests = read_file(os.path.join(TextMap.DATA_FOLDER, 'ExcelOutput', 'BattlePassConfig.json'))
        latest_quests = list(battle_pass_quests.values())[-1]
        week_quest_list = deep_get(latest_quests, "WeekQuestList")
        week_order1 = deep_get(latest_quests, "WeekOrder1")
        week_chain_quest_list = deep_get(latest_quests, "WeekChainQuestList")
        quests = week_quest_list + week_order1 + week_chain_quest_list
        self.load_quests(quests)
        self.write_keywords(keyword_class='BattlePassQuest', output_file='./tasks/battle_pass/keywords/quest.py')

    def generate_rogue_buff(self):
        # paths
        aeons = read_file(os.path.join(TextMap.DATA_FOLDER, 'ExcelOutput', 'RogueAeonDisplay.json'))
        aeons_hash = [deep_get(aeon, 'RogueAeonPathName2.Hash') for aeon in aeons.values()]
        self.keywords_id = aeons_hash
        self.write_keywords(keyword_class='RoguePath', output_file='./tasks/rogue/keywords/path.py')

        # blessings
        blessings_info = read_file(os.path.join(TextMap.DATA_FOLDER, 'ExcelOutput', 'RogueBuff.json'))
        blessings_name_map = read_file(os.path.join(TextMap.DATA_FOLDER, 'ExcelOutput', 'RogueMazeBuff.json'))
        blessings_id = [deep_get(blessing, '1.MazeBuffID') for blessing in blessings_info.values()
                        if not deep_get(blessing, '1.AeonID')][1:]
        resonances_id = [deep_get(blessing, '1.MazeBuffID') for blessing in blessings_info.values()
                         if deep_get(blessing, '1.AeonID')]

        # ignore endless buffs
        endless_buffs = read_file(os.path.join(TextMap.DATA_FOLDER, 'ExcelOutput', 'RogueEndlessMegaBuffDesc.json'))
        endless_buff_ids = [int(id_) for id_ in endless_buffs]
        blessings_id = [id_ for id_ in blessings_id if id_ not in endless_buff_ids]

        def get_blessing_infos(id_list, with_enhancement: bool):
            blessings_hash = [deep_get(blessings_name_map, f"{blessing_id}.1.BuffName.Hash")
                              for blessing_id in id_list]
            blessings_path_id = {blessing_hash: int(deep_get(blessings_info, f'{blessing_id}.1.RogueBuffType')) - 119
                                 # 119 is the magic number make type match with path in keyword above
                                 for blessing_hash, blessing_id in zip(blessings_hash, id_list)}
            blessings_rarity = {blessing_hash: deep_get(blessings_info, f'{blessing_id}.1.RogueBuffRarity')
                                for blessing_hash, blessing_id in zip(blessings_hash, id_list)}
            enhancement = {blessing_hash: "" for blessing_hash in blessings_hash}
            if with_enhancement:
                return blessings_hash, {'path_id': blessings_path_id, 'rarity': blessings_rarity,
                                        'enhancement': enhancement}
            else:
                return blessings_hash, {'path_id': blessings_path_id, 'rarity': blessings_rarity}

        hash_list, extra_attrs = get_blessing_infos(blessings_id, with_enhancement=True)
        self.keywords_id = hash_list
        self.write_keywords(keyword_class='RogueBlessing', output_file='./tasks/rogue/keywords/blessing.py',
                            text_convert=blessing_name, extra_attrs=extra_attrs)

        hash_list, extra_attrs = get_blessing_infos(resonances_id, with_enhancement=False)
        self.keywords_id = hash_list
        self.write_keywords(keyword_class='RogueResonance', output_file='./tasks/rogue/keywords/resonance.py',
                            text_convert=blessing_name, extra_attrs=extra_attrs)

    def generate_rogue_events(self):
        # An event contains several options
        event_title_file = os.path.join(
            TextMap.DATA_FOLDER, 'ExcelOutput',
            'RogueTalkNameConfig.json'
        )
        event_title_ids = {
            id_: deep_get(data, 'Name.Hash')
            for id_, data in read_file(event_title_file).items()
        }
        event_title_texts = defaultdict(list)
        for title_id, title_hash in event_title_ids.items():
            if title_hash not in self.text_map['en']:
                continue
            _, title_text = self.find_keyword(title_hash, lang='en')
            event_title_texts[text_to_variable(title_text)].append(title_id)
        option_file = os.path.join(
            TextMap.DATA_FOLDER, 'ExcelOutput',
            'DialogueEventDisplay.json'
        )
        option_ids = {
            id_: deep_get(data, 'EventTitle.Hash')
            for id_, data in read_file(option_file).items()
        }
        # Key: event name hash, value: list of option id/hash
        options_grouped = dict()
        # Key: option md5, value: option text hash in StarRailData
        option_md5s = dict()

        @cache
        def get_option_md5(option_hash):
            m = md5()
            for lang in UI_LANGUAGES:
                option_text = self.find_keyword(option_hash, lang=lang)[1]
                m.update(option_text.encode())
            return m.hexdigest()

        # Drop invalid or duplicate options
        def clean_options(options):
            visited = set()
            for i in options:
                option_hash = option_ids[str(i)]
                if option_hash not in self.text_map['en']:
                    continue
                option_md5 = get_option_md5(option_hash)
                if option_md5 in visited:
                    continue
                if option_md5 not in option_md5s:
                    option_md5s[option_md5] = option_hash
                visited.add(option_md5)
                yield option_md5s[option_md5]

        for group_title_ids in event_title_texts.values():
            group_option_ids = []
            for title_id in group_title_ids:
                # Special case for Nildis (尼尔迪斯牌)
                # Missing option: Give up
                if title_id == '13501':
                    group_option_ids.append(13506)
                option_id = title_id
                # title ids in Swarm Disaster (寰宇蝗灾) have a "1" prefix
                if option_id not in option_ids:
                    option_id = title_id[1:]
                # Some title may not has corresponding options
                if option_id not in option_ids:
                    continue
                group_option_ids += list(itertools.takewhile(
                    lambda x: str(x) in option_ids,
                    itertools.count(int(option_id))
                ))
            if group_option_ids:
                title_hash = event_title_ids[group_title_ids[0]]
                options_grouped[title_hash] = group_option_ids

        for title_hash, options in options_grouped.items():
            options_grouped[title_hash] = list(clean_options(options))
        for title_hash in list(options_grouped.keys()):
            if len(options_grouped[title_hash]) == 0:
                options_grouped.pop(title_hash)
        option_dup_count = defaultdict(int)
        for option_hash in option_md5s.values():
            if option_hash not in self.text_map['en']:
                continue
            _, option_text = self.find_keyword(option_hash, lang='en')
            option_dup_count[text_to_variable(option_text)] += 1

        def option_text_convert(option_md5, md5_prefix_len=4):
            def wrapper(option_text):
                option_var = text_to_variable(option_text)
                if option_dup_count[option_var] > 1:
                    option_var = f'{option_var}_{option_md5[:md5_prefix_len]}'
                return option_var
            return wrapper

        option_gen = None
        option_hash_to_keyword_id = dict()  # option hash -> option keyword id
        for i, (option_md5, option_hash) in enumerate(option_md5s.items(), start=1):
            self.load_keywords([option_hash])
            option_gen = self.write_keywords(
                keyword_class='RogueEventOption',
                text_convert=option_text_convert(option_md5),
                generator=option_gen
            )
            option_hash_to_keyword_id[option_hash] = i
        output_file = './tasks/rogue/keywords/event_option.py'
        print(f'Write {output_file}')
        option_gen.write(output_file)

        # title hash -> option keyword id
        title_to_option_keyword_id = {
            title_hash: sorted(
                option_hash_to_keyword_id[x] for x in option_hashes
            ) for title_hash, option_hashes in options_grouped.items()
        }
        self.load_keywords(options_grouped.keys())
        self.write_keywords(
            keyword_class='RogueEventTitle',
            output_file='./tasks/rogue/keywords/event_title.py',
            extra_attrs={'option_ids': title_to_option_keyword_id}
        )
        try:
            from tasks.rogue.event.event import OcrRogueEventOption
        except AttributeError:
            logger.critical(
                f'Importing OcrRogueEventOption fails, probably due to changes in {output_file}')
        try:
            from tasks.rogue.event.preset import STRATEGIES
        except AttributeError:
            logger.critical(
                f'Importing preset strategies fails, probably due to changes in {output_file}')

    def iter_without_duplication(self, file: dict, keys):
        visited = set()
        for data in file.values():
            hash_ = deep_get(data, keys=keys)
            _, name = self.find_keyword(hash_, lang='cn')
            if name in visited:
                continue
            visited.add(name)
            yield hash_

    def generate(self):
        self.load_keywords(['模拟宇宙', '拟造花萼（金）', '拟造花萼（赤）', '凝滞虚影', '侵蚀隧洞', '历战余响',
                            '忘却之庭', '虚构叙事'])
        self.write_keywords(keyword_class='DungeonNav', output_file='./tasks/dungeon/keywords/nav.py')
        self.load_keywords(['行动摘要', '生存索引', '每日实训', '逐光捡金', '战术训练'])
        self.write_keywords(keyword_class='DungeonTab', output_file='./tasks/dungeon/keywords/tab.py')
        self.load_keywords(['前往', '领取', '进行中', '已领取', '本日活跃度已满'])
        self.write_keywords(keyword_class='DailyQuestState', output_file='./tasks/daily/keywords/daily_quest_state.py')
        self.load_keywords(['领取', '追踪'])
        self.write_keywords(keyword_class='BattlePassQuestState',
                            output_file='./tasks/battle_pass/keywords/quest_state.py')
        self.load_keywords(list(self.iter_guide()))
        self.write_keywords(keyword_class='DungeonList', output_file='./tasks/dungeon/keywords/dungeon.py',
                            text_convert=dungeon_name)
        self.load_keywords(['进入', '传送', '追踪'])
        self.write_keywords(keyword_class='DungeonEntrance', output_file='./tasks/dungeon/keywords/dungeon_entrance.py')
        self.generate_shadow_with_characters()
        self.load_keywords(['奖励', '任务', ])
        self.write_keywords(keyword_class='BattlePassTab', output_file='./tasks/battle_pass/keywords/tab.py')
        self.load_keywords(['本周任务', '本期任务'])
        self.write_keywords(keyword_class='BattlePassMissionTab',
                            output_file='./tasks/battle_pass/keywords/mission_tab.py')
        self.generate_assignments()
        self.generate_forgotten_hall_stages()
        self.generate_map_planes()
        self.generate_character_keywords()
        self.generate_daily_quests()
        self.generate_battle_pass_quests()
        self.load_keywords(['养成材料', '光锥', '遗器', '其他材料', '消耗品', '任务', '贵重物'])
        self.write_keywords(keyword_class='ItemTab', text_convert=lambda name: name.replace(' ', ''),
                            output_file='./tasks/item/keywords/tab.py')
        self.generate_rogue_buff()
        self.load_keywords(['已强化'])
        self.write_keywords(keyword_class='RogueEnhancement', output_file='./tasks/rogue/keywords/enhancement.py')
        self.load_keywords(list(self.iter_without_duplication(
            read_file(os.path.join(TextMap.DATA_FOLDER, 'ExcelOutput', 'RogueMiracleDisplay.json')),
            'MiracleName.Hash')))
        self.write_keywords(keyword_class='RogueCurio', output_file='./tasks/rogue/keywords/curio.py')
        self.load_keywords(list(self.iter_without_duplication(
            read_file(os.path.join(TextMap.DATA_FOLDER, 'ExcelOutput', 'RogueBonus.json')), 'BonusTitle.Hash')))
        self.write_keywords(keyword_class='RogueBonus', output_file='./tasks/rogue/keywords/bonus.py')
        self.generate_rogue_events()


if __name__ == '__main__':
    TextMap.DATA_FOLDER = '../StarRailData'
    KeywordExtract().generate()
