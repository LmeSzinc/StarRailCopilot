from typing import Union

# Import order matters, DO NOT optimize imports
# 1
import tasks.planner.keywords.item_currency as KEYWORDS_ITEM_CURRENCY
# 2
import tasks.planner.keywords.item_valuable as KEYWORDS_ITEM_VALUABLE
# 3
import tasks.planner.keywords.item_exp as KEYWORDS_ITEM_EXP
# 4
import tasks.planner.keywords.item_ascension as KEYWORDS_ITEM_ASCENSION
# 5
import tasks.planner.keywords.item_trace as KEYWORDS_ITEM_TRACE
# 6
import tasks.planner.keywords.item_weekly as KEYWORDS_ITEM_WEEKLY
# 7
import tasks.planner.keywords.item_calyx as KEYWORDS_ITEM_CALYX

from tasks.planner.keywords.classes import ItemAscension, ItemCalyx, ItemCurrency, ItemExp, ItemTrace, ItemWeekly, ItemValuable

ITEM_CLASSES = [ItemAscension, ItemCalyx, ItemCurrency, ItemExp, ItemTrace, ItemWeekly, ItemValuable]
ITEM_TYPES = Union[ItemAscension, ItemCalyx, ItemCurrency, ItemExp, ItemTrace, ItemWeekly, ItemValuable]
