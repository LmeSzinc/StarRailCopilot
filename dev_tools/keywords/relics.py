from typing import Dict, Iterable, List

from dev_tools.keywords.base import GenerateKeyword
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


def generate_relics():
    GenerateMainStat()()
    GenerateSubStat()()
