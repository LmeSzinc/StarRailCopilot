import typing as t

from dev_tools.keywords.base import GenerateKeyword, TextMap
from dev_tools.keywords.character import convert_inner_character_to_keyword
from module.base.decorator import cached_property
from module.config.deep import deep_get, deep_set
from module.exception import ScriptError


class GenerateCone(GenerateKeyword):
    output_file = './tasks/cone/keywords/cone.py'

    @cached_property
    def data(self):
        # cones
        return self.read_file('./ExcelOutput/ItemConfigEquipment.json')

    def icon_to_name(self, name: str) -> "str | int":
        """
        Extract character name (inner name) or cone id from PoolLabelIcon
        SpriteOutput/DrawCardPic/GachaTabIcon/TabIcon_Dr_Ratio_00.png
        SpriteOutput/DrawCardPic/GachaTabIcon/TabIcon_LightCone_23020.png
        """
        _, _, name = name.rpartition('/')
        name, _, _ = name.partition('.')
        name = name.removeprefix('TabIcon_LightCone_')
        name = name.removeprefix('SubTabIcon_LightCone_')
        # cone
        if name.isdigit():
            return int(name)
        name = name.removeprefix('TabIcon_')
        name = name.removeprefix('SubTabIcon_')
        name = name.removesuffix('_00')
        name = convert_inner_character_to_keyword(name)

        return name

    @cached_property
    def cone_to_character(self):
        # gacha pool
        data = self.read_file('ExcelOutput/GachaBasicInfo.json')
        #   {
        #     "GachaID": 2050,
        #     "GachaType": "AvatarUp",
        #     "SortID": 5,
        #     "StartTime": "",
        #     "EndTime": "",
        #     "PrefabPath": "UI/Drawcard/GachaPanelTemplate/AvatarGacha_Aventurine.prefab",
        #     "PoolName": {
        #       "Hash": 11965228283396127320
        #     },
        #     "PoolDesc": {
        #       "Hash": 12575760539773716760
        #     },
        #     "PoolLabelIcon": "SpriteOutput/DrawCardPic/GachaTabIcon/TabIcon_Aventurine_00.png",
        #     "PoolLabelIconSelected": "SpriteOutput/DrawCardPic/GachaTabIcon/TabIcon_Aventurine_00_Selected.png",
        #     "TypeTitle": {
        #       "Hash": 16335421618088345187
        #     }
        #   },
        pool = {}
        for row in data:
            gacha_type = row.get('GachaType')
            if gacha_type not in ['AvatarUp', 'WeaponUp']:
                continue
            gacha_id = row.get('GachaID')
            # AvatarUp 2072, WeaponUp 3072
            gacha_id %= 1000
            name = self.icon_to_name(row.get('PoolLabelIcon', ''))
            deep_set(pool, [gacha_id, gacha_type], name)

        from tasks.character.keywords import CharacterList
        # Build character -> cone
        out = {}
        for row in pool.values():
            try:
                character = row['AvatarUp']
                cone = row['WeaponUp']
            except KeyError:
                continue
            try:
                character = CharacterList.find(character)
            except ScriptError:
                print(f'Character cone gets unknown character {character}')
                continue
            out[cone] = character.name

        return out

    def iter_keywords(self) -> t.Iterable[dict]:
        cone_to_character = self.cone_to_character
        cones = {}
        for row in self.data:
            cone_id = row.get('ID', 0)
            rarity = row.get('Rarity', 'Unknown')
            visible = row.get('isVisible')
            if not visible:
                continue
            text_id = deep_get(row, ['ItemName', 'Hash'])
            character = cone_to_character.get(cone_id, '')
            cones[cone_id] = {
                'id': cone_id,
                'text_id': text_id,
                'rarity': rarity,
                'character_name': character,
            }

        # sort by cone if
        cones = sorted(cones.items(), key=lambda kv: kv[0])
        for _, cone in cones:
            yield cone


def generate_cone():
    GenerateCone()()
