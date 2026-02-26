import re

from pponnxcr.predict_system import BoxedResult

from module.base.decorator import cached_property, del_cached_property
from module.base.utils import crop, random_rectangle_vector_opted
from module.logger import logger
from module.ocr.ocr import Ocr
from module.ui.scroll import AdaptiveScroll
from tasks.base.ui import UI
from tasks.combat.assets.assets_combat_support_dev import LIST_REFRESH, LIST_REFRESHED
from tasks.combat.assets.assets_combat_support_tab import TEAM_CLICK, TEAM_CHECK
from tasks.combat.support_tab import support_tab
from tasks.ornament.assets.assets_ornament_combat import *
from tasks.ornament.assets.assets_ornament_team import *
from tasks.ornament.assets.assets_ornament_ui import DU_CHECK


class TeamRow:
    def __init__(self, index: int, button, screenshot):
        """
        Args:
            index: 1 to 12
            button:
            screenshot:
        """
        self.index = index
        self.button = button
        self.screenshot = screenshot

    def __str__(self):
        return f'TeamRow(team={self.index})'

    __repr__ = __str__

    @classmethod
    def from_box_result(cls, result: BoxedResult, screenshot) -> "TeamRow | None":
        res = re.search(r'(队伍|Team)\s*(\d+)', result.ocr_text)
        if not res:
            return None

        try:
            index = int(res.group(2))
        except ValueError:
            # this shouldn't happen
            return None
        if not (1 <= index <= 12):
            return None

        return cls(index, button=result.box, screenshot=screenshot)

    @cached_property
    def is_selected(self):
        area = self.button
        left = OCR_TEAM_NAME.area[0]
        # search the left of text
        area = (left + 300, area[1] - 20, left + 500, area[3] + 20)
        image = crop(self.screenshot, area, copy=False)
        return TEAM_ENABLED.match_template_luma(image, direct_match=True)


class OrnamentTeam(UI):
    def _get_teams(self):
        ocr = Ocr(OCR_TEAM_NAME)
        results = ocr.detect_and_ocr(self.device.image)
        rows = []
        for row in results:
            row = TeamRow.from_box_result(row, self.device.image)
            if row is not None:
                rows.append(row)
        logger.info(f'Ornament teams: {rows}')
        return rows

    def ornament_team_set(self, index):
        """
        Args:
            index: 1 to 12

        Returns:
            bool: If success

        Pages:
            in: COMBAT_PREPARE
            out: COMBAT_SUPPORT_LIST
        """
        logger.hr("Ornament team", level=2)
        if not (1 <= index <= 12):
            logger.warning(f'Invalid ornament team: {index}')
            return False

        # COMBAT_PREPARE -> COMBAT_SUPPORT_LIST
        for _ in self.loop():
            # end
            if self.match_template_luma(TEAM_CHECK):
                break
            if self.match_template_luma(TEAM_CLICK):
                break
            # maybe at support page
            if self.match_template_color(LIST_REFRESH, interval=5):
                logger.info(f'{LIST_REFRESH} -> {PREPARE_CLOSE}')
                self.device.click(PREPARE_CLOSE)
                continue
            if self.match_template_color(LIST_REFRESHED, interval=5):
                logger.info(f'{LIST_REFRESHED} -> {PREPARE_CLOSE}')
                self.device.click(PREPARE_CLOSE)
                continue
            # click
            if self.match_template_luma(DU_CHECK, interval=5):
                logger.info(f'{DU_CHECK} -> {OE_SLOT_1}')
                self.device.click(OE_SLOT_1)
                continue

        # select team
        tab = support_tab()
        tab.set('Team', main=self)
        success = self._ornament_team_search(index)

        # no need to close
        # SUPPORT_ADD appears, so support_set() can run
        # COMBAT_PREPARE, so combat_prepare() without support can run
        return success

    def _ornament_team_search(self, index: int):
        """
        Args:
            index: 1 to 12

        Returns:
            bool: True if found

        Pages:
            in: COMBAT_SUPPORT_LIST
        """
        logger.hr('Ornament team search', level=2)
        scroll = AdaptiveScroll(area=TEAM_SCROLL.area, name=TEAM_SCROLL.name)
        while 1:
            teams = self._get_teams()
            found = None
            for team in teams:
                if team.index == index:
                    found = team
                    break
            if found:
                if self._ornament_team_select(found):
                    return True
                else:
                    # wait selected timeout, retry
                    continue

            # team not found, scroll
            # no character, scroll
            if scroll.at_bottom(main=self):
                logger.info("Ornament team not found (scroll at bottom)")
                self.device.click_record_clear()
                return False
            # scroll
            p1, p2 = random_rectangle_vector_opted(
                (0, -320), box=OCR_TEAM_NAME.button, random_range=(-20, -30, 20, 30), padding=0)
            self.device.drag(p1, p2, name=f'ORNAMENT_TEAM_DRAG')
            self.device.screenshot()
            continue

    def _ornament_team_select(self, team: TeamRow):
        """
        Note that this function has no retry, callers should handle retries

        Returns:
            bool: If row selected
        """
        logger.hr("Ornament team select", level=2)

        self.device.click(team)
        for _ in self.loop(timeout=2, skip_first=False):
            # End
            del_cached_property(team, 'is_selected')
            team.screenshot = self.device.image
            if team.is_selected:
                logger.info('Ornament team selected')
                return True
        logger.info('Ornament team not selected')
        return False
