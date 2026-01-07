from typing import Dict, Iterable, List

from dev_tools.keywords.base import GenerateKeyword, SHARE_DATA, UI_LANGUAGES
from module.base.decorator import cached_property
from module.config.deep import deep_get, deep_set
from module.config.utils import read_file, write_file

# Converts relic stat names in game internal to SRC keyword names
DICT_STATS_CONVERT = {
    "HPDelta": 'HPd',
    "AttackDelta": 'ATKd',
    "DefenceDelta": 'DEFd',
    "HPAddedRatio": 'HP',
    "AttackAddedRatio": 'ATK',
    "DefenceAddedRatio": 'DEF',
    "CriticalChanceBase": 'CRITRate',
    "CriticalDamageBase": 'CRITDMG',
    "HealRatioBase": 'OutgoingHealingBoost',
    "StatusProbabilityBase": 'EffectHitRate',
    "StatusResistanceBase": 'EffectRES',
    "SpeedDelta": 'SPD',
    "PhysicalAddedRatio": 'PhysicalDMGBoost',
    "FireAddedRatio": 'FireDMGBoost',
    "IceAddedRatio": 'IceDMGBoost',
    "ThunderAddedRatio": 'LightningDMGBoost',
    "WindAddedRatio": 'WindDMGBoost',
    "QuantumAddedRatio": 'QuantumDMGBoost',
    "ImaginaryAddedRatio": 'ImaginaryDMGBoost',
    "BreakDamageAddedRatioBase": 'BreakEffect',
    "SPRatioBase": 'EnergyRegenerationRate',
}


class RelicBase(GenerateKeyword):
    def convert_name(self, text: str, keyword: dict) -> str:
        return super().convert_name(text, keyword).replace('_', '')

    @cached_property
    def mainstat(self) -> List[str]:
        """
        All mainstats that relics can have
        """
        # JSON that defines what mainstats each relic part can have
        data = self.read_file('./ExcelOutput/RelicBaseType.json')
        for row in data:
            icon = row.get('BaseTypeIconPath', '')
            if 'AllIcon' in icon:
                return row.get('ValidPropertyList', [])

    @cached_property
    def substat(self) -> List[str]:
        """
        All substats that relics can have
        """
        out = []
        # JSON that defines what mainstats each relic part can have
        data = self.read_file('./ExcelOutput/RelicSubAffixBaseValue.json')
        for row in data:
            try:
                name = row['RelicSubAffix']
            except KeyError:
                continue
            out.append(name)
        return out

    @cached_property
    def dic_stat_to_textid(self) -> Dict[str, int]:
        """
        Dict that converts relic stat names in game internal to text id
        """
        out = {}
        # Json that defines all base stats of a character
        data = self.read_file('./ExcelOutput/AvatarPropertyConfig.json')
        for row in data:
            name = row.get('PropertyType', '')
            if not name:
                continue
            text_id = deep_get(row, ['PropertyName', 'Hash'])
            out[name] = text_id
        return out


class GenerateMainStat(RelicBase):
    output_file = './tasks/relics/keywords/mainstat.py'

    def iter_keywords(self) -> Iterable[dict]:
        for stat in self.mainstat:
            text_id = self.dic_stat_to_textid[stat]
            name = DICT_STATS_CONVERT[stat]
            yield {
                'text_id': text_id,
                'name': name,
            }


class GenerateSubStat(RelicBase):
    output_file = './tasks/relics/keywords/substat.py'

    def iter_keywords(self) -> Iterable[dict]:
        for stat in self.substat:
            text_id = self.dic_stat_to_textid[stat]
            name = DICT_STATS_CONVERT[stat]
            yield {
                'text_id': text_id,
                'name': name,
            }


class GenerateRelicSet(RelicBase):
    output_file = './tasks/relics/keywords/relicset.py'

    def iter_keywords(self):
        dict_set = {}
        for row in SHARE_DATA.ItemConfig:
            if row.get('ItemSubType', None) != 'RelicSetShowOnly':
                continue
            setid = deep_get(row, ['CustomDataList', 0], default=0)
            if setid in dict_set:
                continue
            # rarity = row.get('Rarity', 'Unknown')
            text_id = deep_get(row, ['ItemName', 'Hash'], default='')
            # text = self.find_keyword(text_id, lang='cn')[1]
            dict_set[setid] = text_id
            yield {
                'text_id': text_id,
                'setid': setid,
            }

    def generate(self):
        super().generate()
        self.update_relicset_nickname()

    @cached_property
    def RelicConfig(self) -> "dict[int, dict]":
        """
        Contains info of each part of each relic
        {
            "ID": 61012,
            "SetID": 101,
            "Type": "HAND",
            "Rarity": "CombatPowerRelicRarity5",
            "MainAffixGroup": 52,
            "SubAffixGroup": 5,
            "MaxLevel": 15,
            "ExpType": 4,
            "ExpProvide": 1500,
            "CoinCost": 2250,
            "Mode": "BASIC"
        },
        """
        data = {}
        for row in self.read_file('./ExcelOutput/RelicConfig.json'):
            try:
                itemid = row['ID']
            except KeyError:
                continue
            data[itemid] = row
        return data

    @cached_property
    def ItemComeFrom(self) -> "dict[int, dict]":
        """
        Contains items and the dungeon to farm this item (key "GotoParam")
        {
            "ID": 61012,
            "ComefromID": 1,
            "Sort": 1,
            "Desc": {
                "Hash": 2905305945211970818
            },
            "GotoID": 5602,
            "GotoParam": [
                1203
            ]
        },
        """
        data = {}
        for row in self.read_file('./ExcelOutput/ItemComeFrom.json'):
            try:
                itemid = row['ID']
            except KeyError:
                continue
            data[itemid] = row
        return data

    def relicset_to_dungeonid(self, relicset):
        itemid = -1
        for itemid, row in self.RelicConfig.items():
            try:
                setid = row['SetID']
            except KeyError:
                continue
            if setid == relicset:
                break
        if itemid <= 0:
            print(f'Error | no relic item belongs relicset {relicset}')
            return -1

        comefrom = self.ItemComeFrom.get(itemid, {})
        dungeon_id = deep_get(comefrom, ['GotoParam', 0], default=-1)
        return dungeon_id

    def update_relicset_nickname(self):
        """
        Maintain structure of /tasks/relics/keywords/relicset_nickname.json
        """
        file = 'tasks/relics/keywords/relicset_nickname.json'
        old = read_file(file)
        new = {}
        for row in self.iter_rows():
            try:
                name = row['name']
            except KeyError:
                continue

            # setid
            setid = row['setid']
            deep_set(new, [name, 'setid'], setid)
            # dungeon_id
            dungeon_id = self.relicset_to_dungeonid(setid)
            if dungeon_id < 100:
                # ornament extraction, convert 1, 2, 3 to 230, 240, 250
                dungeon_id = 220 + dungeon_id * 10
            deep_set(new, [name, 'dungeon_id'], dungeon_id)
            # original name
            for lang in UI_LANGUAGES:
                lang_name = row.get(lang, '')
                deep_set(new, [name, f'{lang}_origin'], lang_name)
            # nickname
            for lang in UI_LANGUAGES:
                key = [name, lang]
                old_name = deep_get(old, key, default='')
                if not old_name:
                    old_name = row.get(lang, '')
                deep_set(new, key, old_name)

        write_file(file, new)


def generate_relics():
    GenerateMainStat()()
    GenerateSubStat()()
    GenerateRelicSet()()
