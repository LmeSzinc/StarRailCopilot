import typing as t
from datetime import datetime
from functools import partial

from pydantic import BaseModel, ValidationError, WrapValidator, field_validator, model_validator

from module.base.decorator import cached_property, del_cached_property
from module.config.stored.classes import now
from module.config.utils import DEFAULT_TIME
from module.exception import ScriptError
from module.logger import logger
from tasks.base.ui import UI
from tasks.dungeon.keywords import DungeonList
from tasks.planner.keywords import ITEM_TYPES
from tasks.planner.keywords.classes import ItemBase


class PlannerResultRow(BaseModel):
    """
    A row of data from planner result page
    """
    item: ITEM_TYPES
    total: int
    synthesize: int
    demand: int

    def __eq__(self, other):
        return self.item == other.item


class ObtainedAmmount(BaseModel):
    """
    A row of data from DungeonObtain detection
    """
    item: ITEM_TYPES
    value: int


def _fallback_to_default_validator(
        get_default: t.Callable[[], t.Any],
        v: t.Any,
        next_: t.Callable[[t.Any], t.Any],
) -> t.Any:
    try:
        return next_(v)
    except ValueError as e:
        logger.error(e)
        return get_default()


class BaseModelWithFallback(BaseModel):
    """
    Pydantic model that fallbacks to default on error
    https://github.com/pydantic/pydantic/discussions/8579
    """

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: t.Any) -> None:
        for field in cls.model_fields.values():
            if not field.is_required():
                validator = WrapValidator(partial(_fallback_to_default_validator, field.get_default))
                field.metadata.append(validator)

        cls.model_rebuild(force=True)


class MultiValue(BaseModelWithFallback):
    green: int = 0
    blue: int = 0
    purple: int = 0


class StoredPlannerProxy(BaseModelWithFallback):
    item: ITEM_TYPES
    value: int | MultiValue = 0
    total: int | MultiValue = 0
    synthesize: int | MultiValue = 0
    progress: float = 0.
    time: datetime = DEFAULT_TIME

    @field_validator('item', mode='before')
    def val_item(cls, v, info):
        if isinstance(v, str):
            v = ItemBase.find_name(v)
        return v

    @model_validator(mode='after')
    def val_value(self):
        if self.item.has_group_base:
            if not isinstance(self.value, MultiValue):
                self.value = MultiValue()
            if not isinstance(self.total, MultiValue):
                self.total = MultiValue()
            if not isinstance(self.synthesize, MultiValue):
                self.synthesize = MultiValue()
        else:
            if not isinstance(self.value, int):
                self.value = 0
            if not isinstance(self.total, int):
                self.total = 0
            if not isinstance(self.synthesize, int):
                self.synthesize = 0
        return self

    def update_synthesize(self):
        if self.item.has_group_base:
            green = self.value.green - self.total.green
            blue = self.value.blue - self.total.blue
            purple = self.value.purple - self.total.purple
            syn_blue = 0
            syn_purple = 0
            if green >= 3 and blue < 0:
                syn = min(green // 3, -blue)
                syn_blue += syn
                green -= syn * 3
                # blue += syn
            if blue >= 3 and purple < 0:
                syn = min(blue // 3, -purple)
                syn_purple += syn
                blue -= syn * 3
                purple += syn
            if green >= 9 and purple < 0:
                syn = min(green // 9, -purple)
                syn_purple += syn
                syn_blue += syn * 3
                green -= syn * 9
                # purple += syn
            self.synthesize.green = 0
            self.synthesize.blue = syn_blue
            self.synthesize.purple = syn_purple
        else:
            self.synthesize = 0

    def revert_synthesize(self):
        if self.item.has_group_base:
            self.value.green += self.synthesize.blue * 3
            if self.synthesize.blue > 0:
                self.value.green += self.synthesize.purple * 9
            else:
                self.value.blue += self.synthesize.purple * 3

    def update_progress(self):
        if self.item.has_group_base:
            total = self.total.green + self.total.blue * 3 + self.total.purple * 9
            green = min(self.value.green, self.total.green)
            blue = min(self.value.blue + self.synthesize.blue, self.total.blue)
            purple = min(self.value.purple + self.synthesize.purple, self.total.purple)
            value = green + blue * 3 + purple * 9
            progress = value / total * 100
            self.progress = round(min(max(progress, 0), 100), 2)
        else:
            progress = self.value / self.total * 100
            self.progress = round(min(max(progress, 0), 100), 2)

    def update(self):
        self.update_synthesize()
        self.update_progress()
        self.time = now()

    def load_value_total(self, item: ItemBase, value=None, total=None, synthesize=None):
        """
        Update data from PlannerResultRow to self
        """
        if self.item.has_group_base:
            if item.group_base != self.item:
                raise ScriptError(
                    f'load_value_total: Trying to load {item} into {self} but they are different items')
        else:
            if item != self.item:
                raise ScriptError(
                    f'load_value_total: Trying to load {item} into {self} but they are different items')
        if self.item.has_group_base:
            if not self.item.is_rarity_purple:
                raise ScriptError(
                    f'load_value_total: Trying to load {item} into {self} but self is not in rarity purple')
            if item.is_rarity_green:
                if value is not None:
                    self.value.green = value
                if total is not None:
                    self.total.green = total
                # if synthesize is not None:
                #     self.synthesize.green = synthesize
            elif item.is_rarity_blue:
                if value is not None:
                    self.value.blue = value
                if total is not None:
                    self.total.blue = total
                if synthesize is not None:
                    self.synthesize.blue = synthesize
            elif item.is_rarity_purple:
                if value is not None:
                    self.value.purple = value
                if total is not None:
                    self.total.purple = total
                if synthesize is not None:
                    self.synthesize.purple = synthesize
            else:
                raise ScriptError(
                    f'load_value_total: Trying to load {item} in to {self} but item is in invalid rarity')
        else:
            if value is not None:
                self.value = value
            if total is not None:
                self.total = total

    def need_farm(self):
        return self.progress < 100

    def need_synthesize(self):
        if self.item.has_group_base:
            return self.synthesize.green > 0 or self.synthesize.blue > 0 or self.synthesize.purple > 0
        else:
            return self.synthesize > 0

    def load_planner_result(self, row: PlannerResultRow):
        """
        Update data from PlannerResultRow to self
        """
        # Approximate value, accurate value can be update in DungeonObtain
        value = row.total - row.synthesize - row.demand
        self.load_value_total(item=row.item, value=value, total=row.total, synthesize=row.synthesize)

    def load_item_amount(self, row: ObtainedAmmount):
        """
        Update data from ObtainedAmmount to self
        """
        value = row.value
        self.load_value_total(item=row.item, value=value)


class PlannerProgressParser:
    def __init__(self):
        self.rows: dict[str, StoredPlannerProxy] = {}

    def from_planner_results(self, results: list[PlannerResultRow]):
        self.rows = {}
        # Create objects of base items first
        # them load value and total
        for row in results:
            base = row.item.group_base
            if base.name not in self.rows:
                try:
                    obj = StoredPlannerProxy(item=base)
                except ScriptError as e:
                    logger.error(e)
                    continue
                self.rows[base.name] = obj
            else:
                obj = self.rows[base.name]
            obj.load_planner_result(row)

        rows = {}
        for name, row in self.rows.items():
            row.revert_synthesize()
            row.update()
            if row.need_farm() or row.need_synthesize():
                rows[name] = row
        self.rows = rows
        return self

    def load_obtained_amount(self, results: list[ObtainedAmmount]):
        for row in results:
            base = row.item.group_base
            try:
                obj = self.rows[base.name]
            except KeyError:
                logger.warning(
                    f'load_obtained_amount() drops {row} because no need to farm')
                continue
            obj.load_item_amount(row)
            obj.update()
        return self

    def from_config(self, data):
        self.rows = {}
        for row in data.values():
            if not row:
                continue
            try:
                row = StoredPlannerProxy(**row)
            except (ScriptError, ValidationError) as e:
                logger.error(e)
                continue
            if not row.item.is_group_base:
                logger.error(f'from_config: item is not group base {row}')
                continue
            row.update_synthesize()
            row.update_progress()
            self.rows[row.item.name] = row
        return self

    def to_config(self) -> dict:
        data = {}
        for row in self.rows.values():
            name = f'Item_{row.item.name}'
            dic = row.model_dump()
            dic['item'] = row.item.name
            data[name] = dic
        return data

    def iter_row_to_farm(self, need_farm=True) -> t.Iterable[StoredPlannerProxy]:
        """
        Args:
            need_farm: True if filter rows that need farm

        Yields:

        """
        if need_farm:
            rows = [row for row in self.rows.values() if row.need_farm()]
        else:
            rows = self.rows.values()

        for row in rows:
            if row.item.is_ItemWeekly:
                yield row
        for row in rows:
            if row.item.is_ItemAscension:
                yield row
        for row in rows:
            if row.item.is_ItemTrace:
                yield row
        for row in rows:
            if row.item.is_ItemExp:
                yield row
        for row in rows:
            if row.item.is_ItemCurrency:
                yield row

    def get_dungeon(self, double_calyx=False) -> DungeonList | None:
        """
        Get dungeon to farm, or None if planner finished or the remaining items cannot be farmed
        """
        for row in self.iter_row_to_farm():
            item = row.item
            if item.is_ItemWeekly:
                continue
            dungeon = item.dungeon
            if dungeon is None:
                logger.error(f'Item {item} has nowhere to be farmed')
                continue
            if double_calyx:
                if dungeon.is_Calyx:
                    logger.info(f'Planner farm (double_calyx): {dungeon}')
                    return dungeon
            else:
                logger.info(f'Planner farm: {dungeon}')
                return dungeon

        logger.info('Planner farm empty')
        return None

    def get_weekly(self) -> DungeonList | None:
        for row in self.iter_row_to_farm():
            item = row.item
            if not item.is_ItemWeekly:
                continue
            dungeon = item.dungeon
            if dungeon is None:
                logger.error(f'Item {item} has nowhere to be farmed')
                continue
            logger.info(f'Planner farm: {dungeon}')
            return dungeon

        logger.info('Planner farm empty')
        return None

    def row_come_from_dungeon(self, dungeon: DungeonList | None) -> StoredPlannerProxy | None:
        """
        If any items in planner is able to be farmed from given dungeon
        """
        if dungeon is None:
            return None
        for row in self.iter_row_to_farm(need_farm=False):
            if row.item.dungeon == dungeon:
                logger.info(f'Planner {row} come from {dungeon}')
                return row
        return None


class PlannerMixin(UI):
    def planner_write_results(self, results: list[PlannerResultRow]):
        """
        Write planner detection results info user config
        """
        planner = PlannerProgressParser().from_planner_results(results)
        self.planner_write(planner)

    @cached_property
    def planner(self) -> PlannerProgressParser:
        data = self.config.cross_get('Dungeon.Planner', default={})
        model = PlannerProgressParser().from_config(data)
        logger.hr('Planner')
        for row in model.rows.values():
            logger.info(row)
        return model

    def planner_write(self, planner=None):
        """
        Write planner into user config, delete planner object
        """
        if planner is None:
            planner = self.planner

        data = planner.to_config()

        with self.config.multi_set():
            for key, value in data.items():
                self.config.cross_set(f'Dungeon.Planner.{key}', value)
        del_cached_property(self, 'planner')
