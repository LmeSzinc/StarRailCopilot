from typing import Dict, Iterable, List

from dev_tools.keywords.base import GenerateKeyword, SHARE_DATA
from module.base.decorator import cached_property
from module.config.utils import deep_get

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

    def iter_keywords(self) -> Iterable[dict]:
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


class GenerateRelicPart(RelicBase):
    output_file = './tasks/relics/keywords/relicpart.py'

    def iter_keywords(self) -> Iterable[dict]:
        # JSON that defines what mainstats each relic part can have
        data = self.read_file('./ExcelOutput/RelicBaseType.json')
        for row in data:
            if 'Type' not in row:
                continue
            text_id = deep_get(row, ['BaseTypeText', 'Hash'], default=0)
            yield {
                'text_id': text_id
            }

    def convert_name(self, text: str, keyword: dict) -> str:
        # Hands -> Hand
        return super().convert_name(text, keyword).removesuffix('s')


def generate_relics():
    GenerateMainStat()()
    GenerateSubStat()()
    GenerateRelicSet()()
    GenerateRelicPart()()
