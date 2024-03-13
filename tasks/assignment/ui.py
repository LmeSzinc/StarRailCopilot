import re
from collections.abc import Iterator
from datetime import timedelta
from enum import Enum
from functools import cached_property

from module.base.base import ModuleBase
from module.base.timer import Timer
from module.exception import ScriptError
from module.logger import logger
from module.ocr.ocr import DigitCounter, Duration, Ocr
from module.ui.draggable_list import DraggableList
from tasks.assignment.assets.assets_assignment_claim import CLAIM
from tasks.assignment.assets.assets_assignment_dispatch import EMPTY_SLOT
from tasks.assignment.assets.assets_assignment_ui import *
from tasks.assignment.keywords import *
from tasks.base.ui import UI
from tasks.dungeon.ui import DungeonTabSwitch as Switch


class AssignmentStatus(Enum):
    CLAIMABLE = 0
    DISPATCHED = 1
    DISPATCHABLE = 2
    LOCKED = 3


class AssignmentOcr(Ocr):
    # EN has names in multiple rows
    merge_thres_y = 20
    merge_thres_x = 20

    OCR_REPLACE = {
        'cn': [
            (KEYWORDS_ASSIGNMENT_ENTRY.Destruction_of_the_Destroyer.name,
             '[毁没]?[灭火]者的(覆[灭火])?'),
            (KEYWORDS_ASSIGNMENT_ENTRY.Winter_Soldiers.name, '[黑]冬的战[士工土]们'),
            (KEYWORDS_ASSIGNMENT_ENTRY.Born_to_Obey.name, '[牛]而服从'),
            (KEYWORDS_ASSIGNMENT_ENTRY.Root_Out_the_Turpitude.name,
             '根除恶[擎薯尊掌鞋]?'),
            (KEYWORDS_ASSIGNMENT_ENTRY.A_Startling_Night_Terror.name, '^梦惊魂'),
            (KEYWORDS_ASSIGNMENT_ENTRY.Akashic_Records.name, '阿[未][夏复]记录'),
            (KEYWORDS_ASSIGNMENT_ENTRY.The_Blossom_in_the_Storm.name,
             '[风凡]?暴中[怒慈][放方]?的[花化]'),
            (KEYWORDS_ASSIGNMENT_ENTRY.Legend_of_the_Puppet_Master.name, '^师传说'),
            (KEYWORDS_ASSIGNMENT_ENTRY.The_Wages_of_Humanity.name, '[赠]?养人类'),
            (KEYWORDS_ASSIGNMENT_ENTRY.Scalpel_and_Screwdriver.name, '手术刀与.丝刀')
        ],
        'en': [
            (KEYWORDS_ASSIGNMENT_EVENT_ENTRY.Food_Improvement_Plan.name,
             'Food\s*[I]{0}mprovement Plan'),
        ]
    }

    @cached_property
    def ocr_regex(self) -> re.Pattern | None:
        rules = AssignmentOcr.OCR_REPLACE.get(self.lang)
        if rules is None:
            return None
        return re.compile('|'.join('(?P<%s>%s)' % pair for pair in rules))

    def filter_detected(self, result) -> bool:
        # Drop duration rows
        res = Duration.timedelta_regex(self.lang).search(result.ocr_text)
        if res.group('hours') or res.group('seconds'):
            return False
        # Locked event assignments
        locked_pattern = {
            'cn': '解锁$',
            'en': 'Locked$',
        }[self.lang]
        res = re.search(locked_pattern, result.ocr_text)
        return not res

    def after_process(self, result: str):
        result = super().after_process(result)

        if self.ocr_regex is None:
            return result
        matched = self.ocr_regex.fullmatch(result)
        if matched is None:
            return result
        keyword_lang = self.lang
        for keyword_class in (
            KEYWORDS_ASSIGNMENT_ENTRY,
            KEYWORDS_ASSIGNMENT_EVENT_ENTRY,
        ):
            matched = getattr(keyword_class, matched.lastgroup, None)
            if matched is not None:
                break
        else:
            raise ScriptError(f'No keyword found for {matched.lastgroup}')
        matched = getattr(matched, keyword_lang)
        if result != matched:
            logger.attr(name=f'{self.name} after_process',
                        text=f'{result} -> {matched}')
        return matched


class DraggableAssignmentList(DraggableList):
    """
    Draggable list for assignments
    Different from other draggable lists:
    1. When dragged to the bottom/top, the rows will be dragged
       upside/downside a little bit before bouncing back to the
       final position, so it costs extra time to wait for animation
       to complete.
    2. Row orders change after dispatching, making solely using
       `cur_min` and `cur_max` to determine whether a row is in sight
       or not unreliable.
    """
    ROWS_IN_ONE_PAGE = 6    # One page can fit 6 rows at most
    SPECIAL_GROUP = KEYWORDS_ASSIGNMENT_GROUP.EXP_Materials_Credits

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.known_rows = [
            kw for kc in self.keyword_class
            for kw in kc.instances.values()
        ]
        self.row_changed: bool = True
        self.at_top: bool = True    # Remain unchanged when changing group

    def load_rows(self, main: ModuleBase):
        super().load_rows(main)
        self.row_changed = False

    @property
    def cur_indexes(self):
        return [index for row in self.cur_buttons
                if (index := self.keyword2index(row.matched_keyword))]

    def _ensure_top_hack(self, main: 'AssignmentUI'):
        """
        Returns:
            bool: if succeeded
        """
        if len(self.SPECIAL_GROUP.entries) > self.ROWS_IN_ONE_PAGE:
            return False
        old_group = ASSIGNMENT_GROUP_SWITCH.get(main=main)
        ASSIGNMENT_GROUP_SWITCH.set(self.SPECIAL_GROUP, main=main)
        ASSIGNMENT_GROUP_SWITCH.set(old_group, main=main)
        main._wait_until_entry_loaded()
        self.row_changed = True
        self.at_top = True
        return True

    def ensure_top(self, main: ModuleBase, skip_first_screenshot=True):
        """
        Returns:
            bool: if changed
        """
        if self.at_top:
            return False
        if self._ensure_top_hack(main=main):
            return True
        timeout = Timer(5, count=5).start()
        first_row_index: int = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            if timeout.reached():
                logger.warning(f'{self} ensure_top timeout')
                break

            if self.at_top:
                if main.image_color_count(LIST_TOP_BOX, (199, 178, 144), count=200):
                    logger.info(f'{self} is dragged to the top')
                    break
                continue

            if self.row_changed:
                self.load_rows(main=main)
            cur_indexes = self.cur_indexes
            if first_row_index == cur_indexes[0]:
                self.at_top = True
                if main.image_color_count(LIST_TOP_BOX, (199, 178, 144), count=200):
                    logger.info(f'{self} is dragged to the top')
                    break
                continue
            first_row_index = cur_indexes[0]
            self.drag_page(self.reverse_direction(
                self.drag_direction), main=main)
            self.row_changed = True
        return True

    def insight_row(self, row: AssignmentEntry, main: ModuleBase, skip_first_screenshot=True) -> bool:
        row_index = self.keyword2index(row)
        if not row_index:
            logger.warning(f'Insight row {row} but index unknown')
            return False

        logger.info(f'Insight row: {row}, index={row_index}')
        if len(row.group.entries) <= self.ROWS_IN_ONE_PAGE:
            self.at_top = True

        first_loop: bool = True
        last_row_index: int = 0
        cur_indexes: list[int] = []
        seen_indexes: set[int] = set()
        if not skip_first_screenshot:
            main.device.screenshot()
        while 1:
            if self.row_changed:
                self.load_rows(main=main)
            cur_indexes = self.cur_indexes
            seen_indexes.update(cur_indexes)

            # End
            if self.cur_buttons and row_index in cur_indexes:
                break

            # Go to top only in first loop
            if first_loop:
                first_loop = False
                if self.ensure_top(main=main):
                    seen_indexes.clear()
                    continue

            # Drag pages
            self.drag_page(self.drag_direction, main=main)
            self.row_changed = True
            self.at_top = False

            # Wait for bottoming out
            main.wait_until_stable(self.search_button, timer=Timer(
                0, count=0), timeout=Timer(1.5, count=5))
            if cur_indexes and last_row_index == cur_indexes[-1]:
                if len(row.group.entries) == len(seen_indexes):
                    logger.warning(f'No more rows in {self}')
                    return False
                if self.ensure_top(main=main):
                    last_row_index = 0
                    seen_indexes.clear()
                    continue
            last_row_index = cur_indexes[-1]
        # Not at bottom
        if isinstance(row, AssignmentEventEntry) or \
                len(row.group.entries) <= self.ROWS_IN_ONE_PAGE or \
                len(row.group.entries) > len(seen_indexes):
            return True
        # Wait for rows bouncing back
        skip_first_screenshot = True
        timeout = Timer(1, count=2).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()
            if timeout.reached():
                logger.warning(f'{self} wait for stable rows timeout')
                break
            if main.image_color_count(LIST_BOTTOM_SHADOW, (190, 190, 190), count=1000):
                logger.info(f'{self} rows stabled')
                self.load_rows(main=main)
                break
        return True


ASSIGNMENT_GROUP_SWITCH = Switch(
    'AssignmentGroupSwitch',
    is_selector=True
)
ASSIGNMENT_GROUP_SWITCH.add_state(
    KEYWORDS_ASSIGNMENT_EVENT_GROUP.Space_Station_Task_Force,
    check_button=SPACE_STATION_TASK_FORCE_CHECK,
    click_button=SPACE_STATION_TASK_FORCE_CLICK
)
ASSIGNMENT_GROUP_SWITCH.add_state(
    KEYWORDS_ASSIGNMENT_GROUP.Character_Materials,
    check_button=CHARACTER_MATERIALS_CHECK,
    click_button=CHARACTER_MATERIALS_CLICK
)
ASSIGNMENT_GROUP_SWITCH.add_state(
    KEYWORDS_ASSIGNMENT_GROUP.EXP_Materials_Credits,
    check_button=EXP_MATERIALS_CREDITS_CHECK,
    click_button=EXP_MATERIALS_CREDITS_CLICK
)
ASSIGNMENT_GROUP_SWITCH.add_state(
    KEYWORDS_ASSIGNMENT_GROUP.Synthesis_Materials,
    check_button=SYNTHESIS_MATERIALS_CHECK,
    click_button=SYNTHESIS_MATERIALS_CLICK
)
ASSIGNMENT_ENTRY_LIST = DraggableAssignmentList(
    'AssignmentEntryList',
    keyword_class=[AssignmentEntry, AssignmentEventEntry],
    ocr_class=AssignmentOcr,
    search_button=OCR_ASSIGNMENT_ENTRY_LIST,
    check_row_order=False,
    active_color=(40, 40, 40)
)


class AssignmentUI(UI):
    def goto_group(self, group: AssignmentGroup):
        """
        Args:
            group (AssignmentGroup):

        Examples:
            self = AssignmentUI('src')
            self.device.screenshot()
            self.goto_group(KEYWORDS_ASSIGNMENT_GROUP.Character_Materials)
        """
        if ASSIGNMENT_GROUP_SWITCH.get(self) == group:
            return
        logger.hr('Assignment group goto', level=3)
        if not ASSIGNMENT_ENTRY_LIST.cur_buttons:
            ASSIGNMENT_ENTRY_LIST.load_rows(main=self)
        old_rows = set(ASSIGNMENT_ENTRY_LIST.cur_buttons)
        if ASSIGNMENT_GROUP_SWITCH.set(group, self):
            if len(group.entries) <= ASSIGNMENT_ENTRY_LIST.ROWS_IN_ONE_PAGE:
                ASSIGNMENT_ENTRY_LIST.at_top = True
            self._wait_until_entry_loaded(old_rows)

    def goto_entry(self, entry: AssignmentEntry, insight: bool = True):
        """
        Args:
            entry (AssignmentEntry):
            insight (bool): skip ocr to save time if insight is False

        Examples:
            self = AssignmentUI('src')
            self.device.screenshot()
            self.goto_entry(KEYWORDS_ASSIGNMENT_ENTRY.Nameless_Land_Nameless_People)
        """
        if entry.group is None:
            err_msg = f'{entry} is not in any group, please inform developers if possible'
            logger.warning(err_msg)
            for group in self._iter_groups():
                self.goto_group(group)
                if ASSIGNMENT_ENTRY_LIST.select_row(entry, self):
                    return
            raise ScriptError(err_msg)
        else:
            self.goto_group(entry.group)
            ASSIGNMENT_ENTRY_LIST.select_row(entry, self, insight=insight)

    def _set_row_changed(self, changed=True):
        """
        Should be called when order of rows changes,
        Typically after dispatching or claiming
        """
        ASSIGNMENT_ENTRY_LIST.row_changed = changed

    def _wait_until_group_loaded(self):
        skip_first_screenshot = True
        timeout = Timer(2, count=3).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Wait group loaded timeout')
                break
            if self.image_color_count(GROUP_SEARCH, (40, 40, 40), count=25000) and \
                    self.image_color_count(GROUP_SEARCH, (240, 240, 240), count=8000):
                logger.info('Group loaded')
                break

    def _wait_until_entry_loaded(self, old_rows: set = None):
        skip_first_screenshot = True
        load_interval = Timer(0.3, count=1).start()
        timeout = Timer(2, count=3).start()
        changed = (old_rows is None)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning('Wait entry loaded timeout')
                break
            if not changed and load_interval.reached_and_reset():
                ASSIGNMENT_ENTRY_LIST.load_rows(main=self)
                new_rows = set(ASSIGNMENT_ENTRY_LIST.cur_buttons)
                changed = (new_rows != old_rows)
            if changed and self.image_color_count(ENTRY_LOADED, (82, 82, 82), count=1000):
                logger.info('Entry loaded')
                break

    @property
    def _limit_status(self) -> tuple[int, int, int]:
        self.device.screenshot()
        current, remain, total = DigitCounter(
            OCR_ASSIGNMENT_LIMIT).ocr_single_line(self.device.image)
        if total and current <= total:
            logger.attr('Assignment', f'{current}/{total}')
            self.config.stored.Assignment.set(current, total)
        else:
            logger.warning(f'Invalid assignment limit: {current}/{total}')
            self.config.stored.Assignment.set(0, 0)
        return current, remain, total

    def _check_assignment_status(self) -> AssignmentStatus:
        skip_first_screenshot = True
        timeout = Timer(2, count=3).start()
        ret = AssignmentStatus.LOCKED
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if timeout.reached():
                logger.warning(
                    'Check assignment status timeout, assume LOCKED'
                )
                break
            if self.appear(CLAIM):
                ret = AssignmentStatus.CLAIMABLE
                break
            if self.appear(DISPATCHED):
                ret = AssignmentStatus.DISPATCHED
                break
            if self.appear(EMPTY_SLOT):
                ret = AssignmentStatus.DISPATCHABLE
                break
            if self.appear(LOCKED):
                ret = AssignmentStatus.LOCKED
                break
        logger.attr('AssignmentStatus', ret.name)
        return ret

    def _get_assignment_time(self) -> timedelta:
        return Duration(OCR_ASSIGNMENT_TIME).ocr_single_line(self.device.image)

    def _iter_groups(self) -> Iterator[AssignmentGroup]:
        self._wait_until_group_loaded()
        # Yield special group first to ensure top
        yield ASSIGNMENT_ENTRY_LIST.SPECIAL_GROUP
        for state in ASSIGNMENT_GROUP_SWITCH.state_list:
            if state['state'] == ASSIGNMENT_ENTRY_LIST.SPECIAL_GROUP:
                continue
            check = state['check_button']
            click = state['click_button']
            if self.appear(check) or self.appear(click):
                yield state['state']

    def _iter_entries(self) -> Iterator[AssignmentEntry]:
        """
        Iterate entries from top to bottom on top page
        """
        ASSIGNMENT_ENTRY_LIST.ensure_top(main=self)
        if ASSIGNMENT_ENTRY_LIST.row_changed:
            ASSIGNMENT_ENTRY_LIST.load_rows(main=self)
        # Freeze ocr results here
        yield from [
            button.matched_keyword
            for button in ASSIGNMENT_ENTRY_LIST.cur_buttons
        ]


if __name__ == "__main__":
    t = AssignmentUI('src')
    t.device.screenshot()
    import random
    l = list(AssignmentEntry.instances.values())
    while 1:
        e = random.choice(l)
        print(e.ch)
        t.goto_entry(e)
