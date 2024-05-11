import typing as t

from dev_tools.keywords.base import GenerateKeyword, SHARE_DATA
from module.base.decorator import cached_property
from module.config.utils import deep_get


class GenerateItemBase(GenerateKeyword):
    purpose_type = []

    def iter_items(self) -> t.Iterable[dict]:
        for data in SHARE_DATA.ItemConfig.values():
            item_id = data.get('ID', 0)
            text_id = deep_get(data, keys='ItemName.Hash')
            subtype = data.get('ItemSubType', 0)
            rarity = data.get('Rarity', 0)
            purpose = data.get('PurposeType', 0)
            item_group = data.get('ItemGroup', 0)
            yield dict(
                text_id=text_id,
                rarity=rarity,
                item_id=item_id,
                item_group=item_group,
                dungeon_id=-1,
                subtype=subtype,
                purpose=purpose,
            )

    def iter_keywords(self) -> t.Iterable[dict]:
        for data in self.iter_items():
            if data['subtype'] == 'Material' and data['purpose'] in self.purpose_type:
                data['dungeon_id'] = self.dict_itemid_to_dungeonid.get(data['item_id'], -1)
                yield data

    def iter_rows(self) -> t.Iterable[dict]:
        for data in super().iter_rows():
            data.pop('subtype')
            data.pop('purpose')
            yield data

    @cached_property
    def dict_itemid_to_dungeonid(self):
        """
        MappingInfo is like
            dungeon_id:
                dungeon_level:
                    data
        """
        dic = {}
        for level_data in SHARE_DATA.MappingInfo.values():
            # Use the highest level
            # And must contain:
            #       "Type": "FARM_ENTRANCE",
            #       "FarmType": "COCOON",
            for dungeon_data in level_data.values():
                if dungeon_data.get('Type') != 'FARM_ENTRANCE':
                    continue
                # parse
                dungeon_id = dungeon_data.get('ID', 0)
                for item_data in dungeon_data.get('DisplayItemList', []):
                    item_id = item_data.get('ItemID', 0)
                    if item_id < 100:
                        continue
                    dic.setdefault(item_id, dungeon_id)

        return dic


class GenerateItemCurrency(GenerateItemBase):
    output_file = './tasks/planner/keywords/item_currency.py'

    def iter_keywords(self) -> t.Iterable[dict]:
        for data in self.iter_items():
            if data['subtype'] == 'Virtual' and data['item_id'] < 100:
                yield data


class GenerateItemExp(GenerateItemBase):
    output_file = './tasks/planner/keywords/item_exp.py'
    purpose_type = [1, 5, 6]


class GenerateItemAscension(GenerateItemBase):
    output_file = './tasks/planner/keywords/item_ascension.py'
    purpose_type = [2]


class GenerateItemTrace(GenerateItemBase):
    output_file = './tasks/planner/keywords/item_trace.py'
    purpose_type = [3]


class GenerateItemWeekly(GenerateItemBase):
    output_file = './tasks/planner/keywords/item_weekly.py'
    purpose_type = [4]


class GenerateItemCalyx(GenerateItemBase):
    output_file = './tasks/planner/keywords/item_calyx.py'
    purpose_type = [7]


def generate_items():
    GenerateItemCurrency()()
    GenerateItemExp()()
    GenerateItemAscension()()
    GenerateItemTrace()()
    GenerateItemWeekly()()
    GenerateItemCalyx()()
