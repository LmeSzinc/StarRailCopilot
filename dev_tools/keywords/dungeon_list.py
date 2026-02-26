import re
import typing as t

from dev_tools.keywords.base import GenerateKeyword, SHARE_DATA, text_to_variable
from module.base.decorator import cached_property
from module.config.deep import deep_get


def dungeon_name(name: str) -> str:
    name = text_to_variable(name)
    name = re.sub('Bud_of_(Memories|Aether|Treasures)', r'Calyx_Golden_\1', name)
    name = re.sub('Bud_of_(.*)', r'Calyx_Crimson_\1', name).replace('Calyx_Crimson_Calyx_Crimson_', 'Calyx_Crimson_')
    name = re.sub('Shape_of_(.*)', r'Stagnant_Shadow_\1', name)
    name = re.sub('Path_of_(.*)', r'Cavern_of_Corrosion_Path_of_\1', name)
    if name in [
        'Destruction_Beginning',
        'End_of_the_Eternal_Freeze',
        'Divine_Seed',
        'Borehole_Planet_Past_Nightmares',
        'Inner_Beast_Battlefield',
        'Salutations_of_Ashen_Dreams',
        'Glance_of_Twilight',
        'Rusted_Crypt_of_the_Iron_Carcass',
    ]:
        name = f'Echo_of_War_{name}'
    if name in [
        'The_Swarm_Disaster',
        'Swarm_Disaster',
        'Gold_and_Gears',
    ]:
        name = f'Simulated_Universe_{name}'
    name = name.replace('Stagnant_Shadow_Stagnant_Shadow', 'Stagnant_Shadow')
    name = name.replace('Cavern_of_Corrosion_Cavern_of_Corrosion', 'Cavern_of_Corrosion')
    return name


class GenerateDungeonList(GenerateKeyword):
    output_file = './tasks/dungeon/keywords/dungeon.py'

    @cached_property
    def data(self):
        return SHARE_DATA.GameplayGuideData

    def iter_keywords(self) -> t.Iterable[dict]:
        for keyword in self.iter_dungeon():
            if isinstance(keyword, str):
                yield dict(
                    text_id=self.find_keyword(keyword, lang='cn')[0],
                    dungeon_id=-1,
                    plane_id=-1,
                )
            else:
                yield keyword

    def iter_dungeon(self):
        temp_save = ""
        for data in self.data:
            dungeon_id = data.get('ID', 0)
            text_id = deep_get(data, keys='Name.Hash')
            plane_id = deep_get(data, 'MapEntranceID', 0)
            _, name = self.find_keyword(text_id, lang='cn')
            if '永屹之城遗秘' in name:  # load after all forgotten hall to make sure the same order in Game UI
                temp_save = text_id
                continue
            if '忘却之庭' in name:
                continue
            yield dict(
                text_id=text_id,
                dungeon_id=dungeon_id,
                plane_id=plane_id,
            )
        if temp_save:
            yield temp_save
        # Consider rogue DLC as a dungeon
        yield '寰宇蝗灾'
        yield '黄金与机械'
        # 'Memory of Chaos' is not a real dungeon, but represents a group
        yield '混沌回忆'
        yield '天艟求仙迷航录'
        yield '永屹之城遗秘'

    def convert_name(self, text: str, keyword: dict) -> str:
        text = super().convert_name(text, keyword=keyword)
        text = dungeon_name(text)

        # Add plane suffix
        from tasks.map.keywords import MapPlane

        if text.startswith('Calyx_Golden'):
            plane = MapPlane.find_plane_id(keyword['plane_id'])
            if plane is not None:
                text = f'{text}_{plane.world.name}'
            else:
                text = f'{text}_unknown_world'
        if text.startswith('Calyx_Crimson'):
            plane = MapPlane.find_plane_id(keyword['plane_id'])
            if plane is not None:
                text = f'{text}_{plane.name}'
            else:
                text = f'{text}_unknown_plane'
        return text

    def convert_keyword(self, text: str, lang: str) -> str:
        text = super().convert_keyword(text, lang=lang)
        # Bud of Memories (Jarilo-Ⅵ)
        # Use roman numbers instead
        text = re.sub(r'-[VⅤ][IⅠ]', '-Ⅵ', text)

        return text

    def iter_rows(self) -> t.Iterable[dict]:
        dungeons = list(super().iter_rows())

        # Sort by path
        calyx = []
        order = [
            'Calyx_Golden',
            'Calyx_Crimson_Destruction',
            'Calyx_Crimson_Preservation',
            'Calyx_Crimson_The_Hunt',
            'Calyx_Crimson_Abundance',
            'Calyx_Crimson_Erudition',
            'Calyx_Crimson_Harmony',
            'Calyx_Crimson_Nihility',
            'Calyx_Crimson_Remembrance',
            'Calyx_Crimson_Elation',
        ]
        for keyword in order:
            condition = lambda x: x['name'].startswith(keyword)
            calyx += [d for d in dungeons if condition(d)]
            dungeons = [d for d in dungeons if not condition(d)]
        dungeons = calyx + dungeons

        # 2024.09.10, v2.5, add genre prefix
        for dungeon in dungeons:
            if 230 <= dungeon['dungeon_id'] < 1000:
                dungeon['name'] = 'Divergent_Universe_' + dungeon['name']
            if 100 < dungeon['dungeon_id'] < 200:
                dungeon['name'] = 'Simulated_Universe_' + dungeon['name']

        # Reverse dungeon list, latest at top
        def reverse_on_name(d, prefix):
            start = 0
            end = 0
            for index, dungeon in enumerate(d):
                if dungeon['name'].startswith(prefix):
                    if start == 0:
                        start = index
                    end = index + 1
            if start > 0 and end > 0:
                d = d[:start] + d[start:end][::-1] + d[end:]
            return d

        dungeons = reverse_on_name(dungeons, 'Divergent_Universe')
        dungeons = reverse_on_name(dungeons, 'Cavern_of_Corrosion')
        dungeons = reverse_on_name(dungeons, 'Echo_of_War')

        # Reverse Calyx_Golden, sort by world
        # Poor sort
        Jarilo = dungeons[0:3]
        Luofu = dungeons[3:6]
        Penacony = dungeons[6:9]
        Amphoreus = dungeons[9:12]
        Planarcadia = dungeons[12:15]
        others = dungeons[15:]
        dungeons = Planarcadia + Amphoreus + Penacony + Luofu + Jarilo + others

        # Re-sort ID
        self.keyword_index = 0
        for row in dungeons:
            self.keyword_index += 1
            row['id'] = self.keyword_index
            yield row
