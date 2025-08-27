import typing as t

from dev_tools.keywords.base import GenerateKeyword, SHARE_DATA
from module.base.decorator import cached_property
from module.config.deep import deep_get
from module.logger import logger


class GenerateItemBase(GenerateKeyword):
    purpose_type = []
    blacklist = []

    def iter_items(self) -> t.Iterable[dict]:
        for data in SHARE_DATA.ItemConfig:
            item_id = data.get('ID', 0)
            text_id = deep_get(data, keys='ItemName.Hash')
            maintype = data.get('ItemMainType', 0)
            rarity = data.get('Rarity', 0)
            purpose = data.get('PurposeType', 0)
            item_group = data.get('ItemGroup', 0)
            yield dict(
                text_id=text_id,
                rarity=rarity,
                item_id=item_id,
                item_group=item_group,
                dungeon_id=-1,
                maintype=maintype,
                purpose=purpose,
            )

    def iter_keywords(self) -> t.Iterable[dict]:
        for data in self.iter_items():
            if data['maintype'] == 'Material' and data['purpose'] in self.purpose_type:
                if data['item_id'] in self.blacklist:
                    continue
                data['dungeon_id'] = self.dict_itemid_to_dungeonid.get(data['item_id'], -1)
                yield data

    def iter_rows(self) -> t.Iterable[dict]:
        for data in super().iter_rows():
            data.pop('maintype')
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
        for dungeon_data in SHARE_DATA.MappingInfo:
            # Use the highest level
            # And must contain:
            #       "Type": "FARM_ENTRANCE",
            #       "FarmType": "COCOON",
            if dungeon_data.get('Type') != 'FARM_ENTRANCE':
                continue
            # parse
            dungeon_id = dungeon_data.get('ID', 0)
            for item_data in dungeon_data.get('DisplayItemList', []):
                item_id = item_data.get('ItemID', 0)
                if item_id < 100:
                    continue
                dic.setdefault(item_id, dungeon_id)

        # Credict
        dic.setdefault(2, 1003)
        return dic


class GenerateItemCurrency(GenerateItemBase):
    output_file = './tasks/planner/keywords/item_currency.py'
    # Leave 'Credit' and `Trailblaze_EXP`
    whitelist = [2, 22]

    def iter_keywords(self) -> t.Iterable[dict]:
        for data in self.iter_items():
            if data['maintype'] == 'Virtual' and data['item_id'] < 100:
                if data['item_id'] not in self.whitelist:
                    continue
                data['dungeon_id'] = self.dict_itemid_to_dungeonid.get(data['item_id'], -1)
                yield data


class GenerateItemExp(GenerateItemBase):
    output_file = './tasks/planner/keywords/item_exp.py'
    purpose_type = [1, 5, 6]
    # 'Lost_Essence' is not available in game currently
    blacklist = [234]


class GenerateItemAscension(GenerateItemBase):
    output_file = './tasks/planner/keywords/item_ascension.py'
    purpose_type = [2]
    # 'Enigmatic_Ectostella' is not available in game currently
    blacklist = [110400]


class GenerateItemTrace(GenerateItemBase):
    output_file = './tasks/planner/keywords/item_trace.py'
    purpose_type = [3]
    # Can't farm Tears_of_Dreams
    blacklist = [110101]


class GenerateItemWeekly(GenerateItemBase):
    output_file = './tasks/planner/keywords/item_weekly.py'
    purpose_type = [4]


class GenerateItemCalyx(GenerateItemBase):
    output_file = './tasks/planner/keywords/item_calyx.py'
    purpose_type = [7]

    # Can't farm Tears_of_Souls
    blacklist = [111000]

    def iter_keywords(self) -> t.Iterable[dict]:
        items = list(super().iter_keywords())

        # Copy dungeon_id from green item to all items in group
        dic_group_to_dungeonid = {}
        for item in items:
            dungeon = item['dungeon_id']
            if dungeon > 0:
                dic_group_to_dungeonid[item['item_group']] = dungeon
        for item in items:
            item_group = item['item_group']
            try:
                dungeon = dic_group_to_dungeonid[item_group]
            except KeyError:
                logger.warning(f'No dungeon drops item {item}')
                dungeon = -1
            item['dungeon_id'] = dungeon

        yield from items


class GenerateItemValuable(GenerateItemBase):
    output_file = './tasks/planner/keywords/item_valuable.py'

    purpose_type = [10]

    def iter_keywords(self) -> t.Iterable[dict]:
        data = {}
        for row in super().iter_keywords():
            # 自塑尘脂, 遂愿尘脂, 变量骰子
            if row['item_id'] not in [236, 237, 238]:
                continue
            data[row['item_id']] = row

        # 遂愿尘脂 first
        try:
            yield data.pop(237)
        except KeyError:
            pass
        for row in data.values():
            yield row


def generate_items():
    GenerateItemCurrency()()
    GenerateItemExp()()
    GenerateItemAscension()()
    GenerateItemTrace()()
    GenerateItemWeekly()()
    GenerateItemCalyx()()
    GenerateItemValuable()()
