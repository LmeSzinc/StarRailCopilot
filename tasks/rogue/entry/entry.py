import re
from datetime import datetime, timedelta

import cv2
import numpy as np

from module.base.timer import Timer
from module.base.utils import color_similarity_2d
from module.exception import RequestHumanTakeover, ScriptError
from module.logger import logger
from module.ocr.ocr import Ocr
from tasks.base.assets.assets_base_main_page import ROGUE_LEAVE_FOR_NOW
from tasks.base.assets.assets_base_page import MAP_EXIT
from tasks.base.page import page_guide, page_item, page_main, page_rogue
from tasks.dungeon.keywords import DungeonList
from tasks.dungeon.keywords.dungeon import Simulated_Universe_World_1
from tasks.dungeon.state import OcrSimUniPoint
from tasks.dungeon.ui import DungeonUI
from tasks.forgotten_hall.assets.assets_forgotten_hall_ui import TELEPORT
from tasks.rogue.assets.assets_rogue_entry import (
    LEVEL_CONFIRM,
    OCR_WEEKLY_POINT,
    OCR_WORLD,
    THEME_DLC,
    THEME_ROGUE,
    THEME_SWITCH,
    WORLD_ENTER,
    WORLD_NEXT,
    WORLD_PREV
)
from tasks.rogue.assets.assets_rogue_path import CONFIRM_PATH
from tasks.rogue.assets.assets_rogue_ui import ROGUE_LAUNCH
from tasks.rogue.assets.assets_rogue_weekly import REWARD_CLOSE, REWARD_ENTER
from tasks.rogue.entry.path import RoguePathHandler
from tasks.rogue.entry.weekly import RogueRewardHandler
from tasks.rogue.exception import RogueReachedWeeklyPointLimit
from tasks.rogue.route.base import RouteBase


def chinese_to_arabic(chinese_number: str) -> int:
    chinese_numerals = {
        '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
        '六': 6, '七': 7, '八': 8, '九': 9, '零': 0
    }
    result = 0
    current_number = 0

    for char in chinese_number:
        if char in chinese_numerals:
            # If the character is a valid Chinese numeral, accumulate the value.
            current_number = chinese_numerals[char]
        else:
            # If it's not a valid Chinese numeral, assume it's a multiplier (e.g., 十 for 10).
            multiplier = 1
            if char == '十':
                multiplier = 10
            elif char == '百':
                multiplier = 100
            elif char == '千':
                multiplier = 1000
            elif char == '万':
                result += current_number * 10000
                current_number = 0
                continue

            result += current_number * multiplier
            current_number = 0

    result += current_number  # Add the last accumulated number.
    return result


class OcrRogueWorld(Ocr):
    def pre_process(self, image):
        # Letter randomly moving up and down
        # Crop to the up/down border of the white letter
        center = color_similarity_2d(image, color=(255, 255, 255))
        cv2.inRange(center, 180, 255, dst=center)
        # print(np.count_nonzero(center, axis=1))
        # World 8
        # [ 0  0  0  0  0  0  0  2 23 24 22 21 23 29 44 47 38 37 31 32 33 33 31 34
        #  34 44 34  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
        #   0  0  0  0  0  0  0  0]
        # In Progress
        # World 8
        # [ 0  0  0  1  0  3  6  5  3  3  3  1  2  0  0  1  2  0  0  0  0  0  0  0
        #   0  0  0  2 22 24 22 21 23 29 45 46 39 36 30 32 32 32 31 34 34 44 34  0
        #   0  0  0  0  0  0  0  0]
        center = np.where(np.count_nonzero(center, axis=1) > 10)[0]
        if len(center) < 2:
            return image
        up, down = center[0], center[-1]
        image = image[up:down, :, :]
        return image

    def format_result(self, result: str) -> int:
        res = re.search(r'第([一二三四五六七八九十])世界', result)
        if res:
            return chinese_to_arabic(res.group(1))
        res = re.search(r'world[\s_]?(\d)', result.lower())
        if res:
            return int(res.group(1))
        return 0


class RogueEntry(RouteBase, RogueRewardHandler, RoguePathHandler, DungeonUI):
    def _rogue_world_wait(self, skip_first_screenshot=True):
        """
        Wait is_page_rogue_main() fully loaded

        Pages:
            out: is_page_rogue_main()
        """
        logger.info(f'Rogue world wait')
        ocr = OcrRogueWorld(OCR_WORLD)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # Additional
            if self.appear_then_click(REWARD_CLOSE, interval=2):
                continue
            if self.handle_ui_close(LEVEL_CONFIRM, interval=2):
                continue

            if self.is_page_rogue_main() \
                    and self.image_color_count(OCR_WORLD, color=(255, 255, 255), threshold=221, count=50):
                current = ocr.ocr_single_line(self.device.image)
                if current:
                    break

    def _rogue_theme_set(self, world: DungeonList, skip_first_screenshot=True):
        """
        Args:
            world: KEYWORDS_DUNGEON_LIST.Simulated_Universe_World_7
            skip_first_screenshot:

        Pages:
            in: is_page_rogue_main()
        """
        logger.info(f'Rogue theme set: {world.rogue_theme}')
        if world.rogue_theme == 'rogue':
            check_button = THEME_ROGUE
        elif world.rogue_theme == 'dlc':
            check_button = THEME_DLC
        else:
            logger.warning(f'Invalid rogue theme: {world}')
            raise RequestHumanTakeover

        interval = Timer(2, count=10)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(check_button):
                logger.info(f'At theme {world.rogue_theme}')
                break
            # Click
            if interval.reached() and self.is_page_rogue_main():
                self.device.click(THEME_SWITCH)
                interval.reset()

    def _rogue_world_set(self, world: int | DungeonList, skip_first_screenshot=True):
        """
        Args:
            world: 7 or KEYWORDS_DUNGEON_LIST.Simulated_Universe_World_7
            skip_first_screenshot:

        Pages:
            in: is_page_rogue_main()
        """
        ocr = OcrRogueWorld(OCR_WORLD)
        if isinstance(world, DungeonList):
            w = ocr.format_result(world.en)
            if w:
                world = w
            else:
                logger.error(f'Invalid rogue world: {world}')
                raise RequestHumanTakeover

        logger.info(f'Rogue world set: {world}')
        interval = Timer(1, count=3)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # Additional
            if self.appear_then_click(REWARD_CLOSE, interval=2):
                continue
            if self.handle_ui_close(LEVEL_CONFIRM, interval=2):
                interval.clear()
                continue

            if self.is_page_rogue_main() \
                    and self.image_color_count(OCR_WORLD, color=(255, 255, 255), threshold=221, count=50):
                current = ocr.ocr_single_line(self.device.image)
                if not current:
                    continue
                # End
                if current == world:
                    logger.info(f'At world {world}')
                    break
                # Click
                if interval.reached():
                    diff = world - current
                    if diff > 0:
                        # 0.5s at min
                        self.device.multi_click(WORLD_NEXT, n=abs(diff), interval=(0.5, 0.7))
                        interval.reset()
                    elif diff < 0:
                        self.device.multi_click(WORLD_PREV, n=abs(diff), interval=(0.5, 0.7))
                        interval.reset()
                    else:
                        logger.error(f'Invalid world diff: {diff}')

    def _rogue_world_enter(self, skip_first_screenshot=True):
        """
        Raises:
            RogueReachedWeeklyPointLimit: Raised if task should stop

        Pages:
            in: is_page_rogue_main()
            out: is_page_rogue_launch()
        """
        logger.info('Rogue world enter')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_page_rogue_launch():
                logger.info('At is_page_rogue_launch()')
                break
            if self.is_in_main():
                logger.info('At is_in_main()')
                break

            # Click
            if self.interval_is_reached(REWARD_ENTER, interval=2) and self.is_page_rogue_main():
                self.device.click(WORLD_ENTER)
                self.interval_reset(REWARD_ENTER, interval=2)
                continue
            if self.match_template_color(LEVEL_CONFIRM, interval=2):
                if not self.image_color_count(LEVEL_CONFIRM, color=(223, 223, 225), threshold=240, count=50):
                    self.interval_clear(LEVEL_CONFIRM)
                    continue
                self.dungeon_update_stamina()
                self.check_stop_condition()
                self.device.click(LEVEL_CONFIRM)
                continue
            if self.appear_then_click(REWARD_CLOSE, interval=2):
                continue

    def rogue_world_exit(self, skip_first_screenshot=True):
        """
        Pages:
            in: is_page_rogue_launch()
            out: is_page_rogue_main()
        """
        logger.info('Rogue world exit')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_page_rogue_main():
                logger.info('At is_page_rogue_main()')
                break

            # Click
            # From _rogue_world_enter()
            if self.handle_ui_close(ROGUE_LAUNCH):
                continue
            if self.handle_ui_back(LEVEL_CONFIRM):
                continue
            if self.appear_then_click(REWARD_CLOSE, interval=2):
                continue
            # From _is_page_rogue_path()
            if self.handle_ui_back(CONFIRM_PATH):
                pass
            if self.handle_ui_back(self._is_page_rogue_path):
                continue
            # From ui_leave_special()
            if self.is_in_map_exit(interval=2):
                self.device.click(MAP_EXIT)
                continue
            if self.handle_popup_confirm():
                continue
            if self.appear_then_click(ROGUE_LEAVE_FOR_NOW, interval=2):
                continue

    def _rogue_teleport(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_guide, Survival_Index, Simulated_Universe
            out: page_rogue, is_page_rogue_main()
        """
        logger.info('Rogue teleport')
        self.interval_clear(page_guide.check_button)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.ui_page_appear(page_rogue):
                break

            if self.appear_then_click(REWARD_CLOSE, interval=2):
                continue
            if self.appear(page_guide.check_button, interval=2):
                buttons = TELEPORT.match_multi_template(self.device.image)
                if len(buttons):
                    buttons = sorted(buttons, key=lambda x: x.area[1])
                    self.device.click(buttons[0])
                    continue

        self.interval_clear(page_guide.check_button)

    def check_stop_condition(self):
        """
        Raises:
            RogueReachedWeeklyPointLimit: Raised if task should stop
        """
        logger.info(f'RogueWorld_UseImmersifier={self.config.RogueWorld_UseImmersifier}, '
                    f'RogueWorld_UseStamina={self.config.RogueWorld_UseStamina}, '
                    f'RogueWorld_DoubleEvent={self.config.RogueWorld_DoubleEvent}, '
                    f'RogueWorld_WeeklyFarming={self.config.RogueWorld_WeeklyFarming}, '
                    f'RogueDebug_DebugMode={self.config.RogueDebug_DebugMode}')
        # This shouldn't happen
        if self.config.RogueWorld_UseStamina and not self.config.RogueWorld_UseImmersifier:
            logger.error('Invalid rogue reward settings')
            raise ScriptError
        if self.config.RogueWorld_DoubleEvent and not self.config.RogueWorld_UseImmersifier:
            logger.error('Invalid rogue reward settings')
            raise ScriptError

        if self.config.RogueDebug_DebugMode:
            # Always run
            return
        
        if self.config.stored.SimulatedUniverseFarm.is_expired():
            # Expired, reset farming counter
            self.config.stored.SimulatedUniverseFarm.set(0)
        
        if self.config.stored.SimulatedUniverse.is_expired():
            # Expired, do rogue
            pass
        elif self.config.stored.SimulatedUniverse.is_full():
            if self.config.RogueWorld_UseImmersifier and self.config.stored.Immersifier.value > 0:
                logger.info(
                    'Reached weekly point limit but still have immersifiers left, continue to use them')
            elif self.config.RogueWorld_WeeklyFarming and not self.config.stored.SimulatedUniverseFarm.is_full():
                logger.info(
                    'Reached weekly point limit but still continue to farm materials')
                logger.attr(
                    "Farming Counter", self.config.stored.SimulatedUniverseFarm.to_counter())
            else:
                raise RogueReachedWeeklyPointLimit
        else:
            # Not full, do rogue
            pass

    def rogue_world_enter(self, world: int | DungeonList = None):
        """
        Args:
            world: 7 or KEYWORDS_DUNGEON_LIST.Simulated_Universe_World_7

        Raises:
            RogueReachedWeeklyPointLimit: Raised if task should stop

        Pages:
            in: page_rogue
            out: is_page_rogue_launch()
                or is_page_rogue_main() if RogueReachedWeeklyPointLimit raised
        """
        logger.hr('Rogue world enter', level=1)
        if world is None:
            world = DungeonList.find(self.config.RogueWorld_World)
        # Check stop condition
        self.check_stop_condition()

        def is_rogue_entry():
            if self.is_page_rogue_main():
                logger.info('At is_page_rogue_main()')
                return True
            if not self.ui_page_appear(page_item) and self.appear(LEVEL_CONFIRM):
                logger.info('At LEVEL_CONFIRM')
                return True
            return False

        self.ui_get_current_page()
        if self.ui_current == page_rogue:
            if is_rogue_entry():
                # At rogue page but haven't entered it
                self.rogue_world_exit()
                self.ui_get_current_page()
            else:
                # Already started a rogue, do the preparation
                if self._is_page_rogue_path():
                    logger.info('At _is_page_rogue_path()')
                    self.rogue_path_select(self.config.RogueWorld_Path)
                if self.appear(CONFIRM_PATH):
                    logger.info('At CONFIRM_PATH')
                    self.rogue_path_select(self.config.RogueWorld_Path)
                # Team prepared
                if self.is_page_rogue_launch():
                    logger.info('At is_page_rogue_launch()')
                    self.rogue_path_select(self.config.RogueWorld_Path)
                logger.info('At any page_rogue')
                self.clear_blessing()
                self.ui_get_current_page()
        if self.ui_current == page_main:
            self.handle_lang_check(page=page_main)
            # Already in a rogue domain, no UI switching required, continue the rogue
            if self.plane.rogue_domain:
                logger.info('At rogue domain')
                return
            # In Herta's Office, interact to enter rogue
            if self.get_dungeon_interact() == Simulated_Universe_World_1:
                logger.info('At rogue entry')
                self.combat_enter_from_map()
        # Not in page_rogue, goto
        if not is_rogue_entry():
            self.dungeon_goto_rogue()
            self._rogue_teleport()

        # is_page_rogue_main()
        self._rogue_theme_set(world)
        self._rogue_world_wait()

        # Update rogue points
        if datetime.now() - self.config.stored.SimulatedUniverse.time > timedelta(minutes=2):
            ocr = OcrSimUniPoint(OCR_WEEKLY_POINT)
            value, _, total = ocr.ocr_single_line(self.device.image)
            if total and value <= total:
                logger.attr('SimulatedUniverse', f'{value}/{total}')
                self.config.stored.SimulatedUniverse.set(value, total)
            else:
                logger.warning(f'Invalid SimulatedUniverse points: {value}/{total}')

        self.rogue_reward_claim()
        # Check stop condition again as weekly reward updated
        self.check_stop_condition()

        # Enter
        self._rogue_world_set(world)
        # Check stop condition again as immersifier updated
        try:
            self._rogue_world_enter()
        except RogueReachedWeeklyPointLimit:
            self.rogue_world_exit()
            raise
        self.rogue_path_select(self.config.RogueWorld_Path)
