import re

from module.base.timer import Timer
from module.logger import logger
from tasks.base.ui import UI
from tasks.combat.assets.assets_combat_team import *


def button_to_index(button: ButtonWrapper) -> int:
    res = re.search(r'(\d)', button.name)
    if res:
        return int(res.group(1))
    else:
        logger.warning(f'Cannot convert team button to index: {button}')
        return 0


class CombatTeam(UI):
    def _get_team(self) -> int:
        """
        Returns:
            int: Current team index, or 0 if current team is not insight
        """
        team = 0
        for button in [
            TEAM_1_CHECK, TEAM_2_CHECK, TEAM_3_CHECK, TEAM_4_CHECK, TEAM_5_CHECK,
            TEAM_6_CHECK, TEAM_7_CHECK, TEAM_8_CHECK, TEAM_9_CHECK
        ]:
            button.load_search(TEAM_SEARCH.area)
            if self.appear(button, similarity=0.92):
                if self.image_color_count(button.button, color=(255, 234, 191), threshold=180, count=50):
                    team = button_to_index(button)
                    break

        return team

    def team_set(self, index: int = 1, skip_first_screenshot=True) -> bool:
        """
        Args:
            index: Team index, 1 to 9.
            skip_first_screenshot:

        Returns:
            bool: If clicked

        Pages:
            in: page_team
        """
        logger.info(f'Team set: {index}')
        # Wait teams show up
        timeout = Timer(1, count=5).start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if timeout.reached():
                logger.warning('Wait current team timeout')
                break
            current = self._get_team()
            if current == index:
                logger.attr('Team', current)
                logger.info(f'Already selected to the correct team')
                return False
            else:
                break

        # Set team
        retry = Timer(2, count=10)
        skip_first_screenshot = True
        clicked = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            current = self._get_team()
            logger.attr('Team', current)
            if current == index:
                logger.info(f'Selected to the correct team')
                return clicked
            # Click
            if retry.reached():
                diff = index - current
                right = diff % 9
                left = -diff % 9
                if right <= left:
                    self.device.multi_click(TEAM_NEXT, right)
                    clicked = True
                else:
                    self.device.multi_click(TEAM_PREV, left)
                    clicked = True
                retry.reset()
                continue

        return clicked

    def handle_combat_team_prepare(self, team: int = 1) -> bool:
        """
        Set team and click prepare before dungeon combat.

        Args:
            team: Team index, 1 to 9.

        Returns:
            int: If clicked
        """
        if self.appear(COMBAT_TEAM_PREPARE, interval=5):
            self.team_set(team)
            self.device.click(COMBAT_TEAM_PREPARE)
            return True

        return False
