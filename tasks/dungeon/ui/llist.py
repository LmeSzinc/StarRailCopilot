import re
from copy import copy

import cv2
from pponnxcr.predict_system import BoxedResult

from module.base.base import ModuleBase
from module.base.button import ClickButton
from module.base.decorator import run_once, set_cached_property
from module.base.timer import Timer
from module.base.utils import area_center, area_limit, area_offset, color_similarity_2d, crop, image_size
from module.logger import logger
from module.ocr.ocr import Ocr, OcrResultButton
from module.ocr.utils import merge_result_button, split_and_pair_button_attr
from module.ui.draggable_list import DraggableList
from module.ui.switch import Switch
from tasks.base.page import page_guide
from tasks.base.ui import UI
from tasks.combat.assets.assets_combat_obtain import ITEM_CLOSE
from tasks.combat.assets.assets_combat_prepare import COMBAT_PREPARE, ENEMY_INFO_CHECK
from tasks.dungeon.assets.assets_dungeon_ui_list import *
from tasks.dungeon.keywords import (
    DungeonList,
    KEYWORDS_DUNGEON_ENTRANCE,
    KEYWORDS_DUNGEON_LIST
)
from tasks.dungeon.keywords.classes import DungeonEntrance
from tasks.map.keywords import MapPlane

LIST_SORTING = Switch('DUNGEON_LIST_SORTING', is_selector=True)
LIST_SORTING.add_state('Ascending', check_button=LIST_ASCENDING)
LIST_SORTING.add_state('Descending', check_button=LIST_DESCENDING)
LIST_SORTING.Ascending = 'Ascending'
LIST_SORTING.Descending = 'Descending'


class OcrDungeonName(Ocr):
    def after_process(self, result):
        # 乙太之蕾•雅利洛-Ⅵ
        result = re.sub(r'-[VⅤ][IⅠ]', '-Ⅵ', result)

        # 苏乐达™热砂海选会场
        result = re.sub(r'(苏乐达|蘇樂達|SoulGlad|スラーダ|FelizAlma)[rtT]*M*', r'\1', result)
        result = re.sub(r'["\']', '', result)
        result = re.sub('Aud[it]+on', 'Audition', result)

        result = super().after_process(result)

        if self.lang == 'cn':
            result = result.replace('翼', '巽')  # 巽风之形
            result = result.replace('皖A0', '50').replace('皖', '')
            # 燔灼之形•凝滞虚影
            result = re.sub('[熠蟠]灼', '燔灼', result)
            result = re.sub('^灼之形', '燔灼之形', result)
            # 偃偶之形•凝滞虚影
            result = re.sub('^偶之形', '偃偶之形', result)
            # 嗔怒之形•凝滞虚影
            result = re.sub('^怒之形', '嗔怒之形', result)
            # 烬日之形•凝滞虚影
            result = re.sub('^日之形', '烬日之形', result)
            # 蛀星的旧·历战余响
            result = re.sub(r'蛀星的旧.?历战.+$', '蛀星的旧魇•历战的余响', result)
            result = re.sub(r'蛀星的旧.?历战?$', '蛀星的旧魇•历战', result)
            result = re.sub(r'蛀星的旧.?$', '蛀星的旧魇', result)
            # 蠹役饥肠
            result = re.sub('[鑫蠢]役', '蠹役', result)
            # 「呓语密林」神悟树庭
            result = re.sub('[艺吃]语', '呓语', result)
            # 9支援仓段
            for word in 'Q9α':
                result = result.removeprefix(word)
            # 铁的锈家 -> 铁骸的锈冢
            result = result.replace('锈家', '锈冢')
            result = result.replace('铁的', '铁骸的')
        elif self.lang == 'en':
            # O Supply Zone
            result = re.sub(r'^[Oo0] S', 'S', result)
        # ①收容舱段
        result = re.sub(r'[①②③④⑤⑥⑦⑧⑨⑩]', '', result)
        return result


class OcrDungeonList(OcrDungeonName):
    # Keep __init__ parameter unused
    def __init__(self, button: ButtonWrapper = None, lang=None, name=None):
        super().__init__(button=button, lang=lang, name='OcrDungeonList')
        # target_dungeon: Dungeon attribute to use map planes to predict dungeons only.
        self.target_dungeon = None
        # limit_entrance: True to ensure the teleport button is insight
        self.limit_entrance = False

    def detect_and_ocr(self, image, direct_ocr=False) -> list[BoxedResult]:
        if self.button == OCR_DUNGEON_NAME:
            return self.detect_and_ocr_with_teleport(
                image, OCR_DUNGEON_NAME, OCR_DUNGEON_TELEPORT, direct_ocr=direct_ocr)
        if self.button == OCR_DUNGEON_NAME_ROGUE:
            return self.detect_and_ocr_with_teleport(
                image, OCR_DUNGEON_NAME_ROGUE, OCR_DUNGEON_TELEPORT_ROGUE, direct_ocr=direct_ocr)
        # Classic detect_and_ocr
        if self.limit_entrance:
            self.button = ClickButton((*self.button.area[:3], self.button.area[3] - 70))
        return super().detect_and_ocr(image, direct_ocr=direct_ocr)

    def detect_and_ocr_with_teleport(
            self,
            image,
            ocr_name: ButtonWrapper,
            ocr_teleport: ButtonWrapper,
            direct_ocr=False
    ) -> list[BoxedResult]:
        # Concat OCR_DUNGEON_NAME and OCR_DUNGEON_TELEPORT
        # so they can be OCRed at one time
        left = crop(image, ocr_name.area, copy=False)
        right = crop(image, ocr_teleport.area, copy=False)
        lw, lh = image_size(left)
        rw, rh = image_size(right)
        if lh != rh:
            logger.error('OCR_DUNGEON_NAME and OCR_DUNGEON_TELEPORT does not have same height, image cannot concat')
        image = cv2.hconcat([left, right])

        if self.limit_entrance:
            w, h = image_size(image)
            image = crop(image, (0, 0, w, h - 70), copy=False)

        results = super().detect_and_ocr(image, direct_ocr=True)

        # Move box
        for result in results:
            x, _ = area_center(result.box)
            # Belongs to right image
            if x >= lw:
                result.box = area_offset(result.box, offset=(-lw, 0))
                result.box = area_offset(result.box, offset=ocr_teleport.area[:2])
            # Belongs to left image
            else:
                result.box = area_offset(result.box, offset=ocr_name.area[:2])

        before = copy(results)
        # Calyx_Crimson_The_Hunt_Penacony_SoulGladScorchsandAuditionVenue
        merge_result_button(results, 'Audition', 'Venue', 'SoulGladScorchsandAuditionVenue')
        merge_result_button(results, 'Sanctum', 'Janusopo', 'SanctumofProphecyJanusopolis')
        merge_result_button(results, 'Murmuring', 'Epiphany', 'MurmuringWoodsGroveofEpiphany')
        merge_result_button(results, 'Sanctumo', 'Janusopoli', 'SanctumofProphecyJanusopolis')
        merge_result_button(results, 'Castrum', 'Kremno', 'StrifeRuinsCastrumKremnos')

        if results != before:
            logger.attr(name=self.name,
                        text=str([result.ocr_text for result in results]))
        return results

    def _match_result(self, *args, **kwargs):
        """
        Convert MapPlane object to their corresponding DungeonList object
        """
        matched = super()._match_result(*args, **kwargs)
        if self.target_dungeon is not None and matched is not None:
            if self.target_dungeon.is_Calyx_Golden:
                # convert MapPlane and ignore DungeonList
                if isinstance(matched, DungeonList):
                    return
                for dungeon in DungeonList.instances.values():
                    if dungeon.is_Calyx_Golden and dungeon.plane == matched:
                        return dungeon
            if self.target_dungeon.is_Calyx_Crimson:
                if isinstance(matched, DungeonList):
                    return
                for dungeon in DungeonList.instances.values():
                    if dungeon.is_Calyx_Crimson and dungeon.plane == matched:
                        return dungeon
            else:
                if isinstance(matched, MapPlane):
                    return

        return matched


class DraggableDungeonList(DraggableList):
    teleports: list[OcrResultButton] = []
    navigates: list[OcrResultButton] = []

    # target_dungeon: Dungeon attribute to use map planes to predict dungeons only.
    target_dungeon = None
    # limit_entrance: True to ensure the teleport button is insight
    limit_entrance = False

    def wait_bottom_appear(self, main: "DungeonUIList", skip_first_screenshot=True):
        """
        Returns:
            bool: If waited
        """
        return main.dungeon_list_wait_list_end(skip_first_screenshot=skip_first_screenshot)

    def load_rows(self, main: ModuleBase):
        """
        Args:
            main:
        """
        relative_area = (0, -40, 1280, 120)

        # Passing to OcrDungeonList
        ocr = OcrDungeonList(self.search_button)
        ocr.target_dungeon = self.target_dungeon
        ocr.limit_entrance = self.limit_entrance

        set_cached_property(self, 'ocr', ocr)
        super().load_rows(main=main)

        # Replace dungeon.button with teleport
        self.teleports = list(split_and_pair_button_attr(
            self.cur_buttons,
            split_func=lambda x: x != KEYWORDS_DUNGEON_ENTRANCE.Teleport,
            relative_area=relative_area
        ))
        self.teleports += list(split_and_pair_button_attr(
            self.cur_buttons,
            split_func=lambda x: x != KEYWORDS_DUNGEON_ENTRANCE.Enter,
            relative_area=relative_area
        ))
        self.navigates = list(split_and_pair_button_attr(
            self.cur_buttons,
            split_func=lambda x: x != KEYWORDS_DUNGEON_ENTRANCE.Navigate,
            relative_area=relative_area
        ))


DUNGEON_LIST = DraggableDungeonList(
    'DungeonList', keyword_class=[DungeonList, DungeonEntrance, MapPlane],
    ocr_class=OcrDungeonList, search_button=OCR_DUNGEON_NAME)


class DungeonUIList(UI):

    def _dungeon_list_reset(self):
        """
        Reset list to top

        Returns:
            bool: If success
        """
        logger.info('Dungeon list reset')
        current = LIST_SORTING.get(main=self)
        if current == LIST_SORTING.Descending:
            another = LIST_SORTING.Ascending
        elif current == LIST_SORTING.Ascending:
            another = LIST_SORTING.Descending
        else:
            logger.warning('Unknown dungeon LIST_SORTING')
            return False

        LIST_SORTING.set(another, main=self)
        LIST_SORTING.set(current, main=self)
        return True

    def dungeon_list_wait_list_end(self, skip_first_screenshot=True):
        """
        When swiping down at list end, wait until list rebound

        Returns:
            bool: If waited
        """
        logger.info('dungeon_list_wait_list_end')
        timeout = Timer(1, count=3).start()
        empty = False
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if timeout.reached():
                logger.warning('Wait dungeon_list_wait_list_end timeout')
                return True
            # Check color
            image = self.image_crop(LIST_END_CHECK, copy=False)
            mask = color_similarity_2d(image, (255, 255, 255))
            cv2.inRange(mask, 0, 235, dst=mask)
            mean = cv2.mean(mask)[0]
            if mean > 30:
                if empty:
                    # rebound, having rows at bottom now
                    return True
                else:
                    # Not at bottom from the very beginning
                    return False
            else:
                # Blank background
                empty = True
                continue

    def _dungeon_insight_index(self, dungeon: DungeonList):
        """
        Insight a dungeon using pre-defined dungeon indexes from DUNGEON_LIST

        Pages:
            in: page_guide, Survival_Index, nav including dungeon
            out: page_guide, Survival_Index, nav including dungeon, dungeon insight
        """
        logger.hr('Dungeon insight (index)', level=2)
        if dungeon.is_Ornament_Extraction:
            # Limit drag area in Ornament_Extraction
            # v4.0 banner disappear if having OE save
            DUNGEON_LIST.search_button = OCR_DUNGEON_NAME
        elif dungeon.is_Echo_of_War:
            DUNGEON_LIST.search_button = OCR_DUNGEON_LIST
        else:
            DUNGEON_LIST.search_button = OCR_DUNGEON_NAME
        # Predict dungeon by plane name in calyxes where dungeons share the same names
        DUNGEON_LIST.target_dungeon = dungeon
        DUNGEON_LIST.check_row_order = True

        # Insight dungeon
        DUNGEON_LIST.insight_row(dungeon, main=self)
        self.device.click_record_clear()
        # Check if dungeon unlocked
        for entrance in DUNGEON_LIST.navigates:
            entrance: OcrResultButton = entrance
            logger.warning(f'Teleport {entrance.matched_keyword} is not unlocked')
            if entrance == dungeon:
                logger.error(f'Trying to enter dungeon {dungeon}, but teleport is not unlocked')
                return False

        # Find teleport button
        if dungeon not in [tp.matched_keyword for tp in DUNGEON_LIST.teleports]:
            # Dungeon name is insight but teleport button is not
            logger.info('Dungeon name is insight, swipe down a little bit to find the teleport button')
            if dungeon.is_Forgotten_Hall:
                DUNGEON_LIST.drag_vector = (-0.4, -0.2)  # Keyword loaded is reversed
            elif dungeon.is_Ornament_Extraction:
                # Having banner, smaller list, drag more
                DUNGEON_LIST.drag_vector = (0.2, 0.4)
            else:
                DUNGEON_LIST.drag_vector = (0.2, 0.4)
            DUNGEON_LIST.limit_entrance = True
            DUNGEON_LIST.insight_row(dungeon, main=self)
            self.device.click_record_clear()
            DUNGEON_LIST.drag_vector = DraggableList.drag_vector
            DUNGEON_LIST.limit_entrance = False
            DUNGEON_LIST.load_rows(main=self)
            # Check if dungeon unlocked
            for entrance in DUNGEON_LIST.navigates:
                if entrance.matched_keyword == dungeon:
                    logger.error(f'Trying to enter dungeon {dungeon}, but teleport is not unlocked')
                    return False

        return True

    def _dungeon_insight_sort(self, dungeon: DungeonList):
        """
        Insight a dungeon using sorter and plain drag, reset list on error
        """
        logger.hr('Dungeon insight (sort)', level=2)
        logger.info(f'Dungeon insight: {dungeon}')
        DUNGEON_LIST.search_button = OCR_DUNGEON_NAME
        DUNGEON_LIST.target_dungeon = dungeon
        DUNGEON_LIST.check_row_order = False

        for _ in range(3):
            visited = set()
            end_count = 0
            self.device.click_record_clear()
            while 1:
                visited_count = len(visited)
                # Load
                DUNGEON_LIST.load_rows(main=self)
                for entrance in DUNGEON_LIST.teleports:
                    if entrance.matched_keyword == dungeon:
                        logger.info(f'Found dungeon {dungeon}')
                        return True
                for entrance in DUNGEON_LIST.navigates:
                    if entrance.matched_keyword == dungeon:
                        logger.error(f'Trying to enter dungeon {dungeon}, but teleport is not unlocked')
                        return False

                # Check end
                for entrance in DUNGEON_LIST.cur_buttons:
                    visited.add(entrance.matched_keyword.name)
                if len(visited) <= visited_count:
                    logger.warning('No more rows loaded')
                    end_count += 1
                if end_count >= 3:
                    logger.error('Dungeon list reached end but target dungeon not found')
                    break

                # Drag down
                DUNGEON_LIST.drag_page('down', main=self)
                self.dungeon_list_wait_list_end(skip_first_screenshot=False)
                self.wait_until_stable(
                    DUNGEON_LIST.search_button, timer=Timer(0, count=0),
                    timeout=Timer(1.5, count=5)
                )

            self._dungeon_list_reset()

        logger.error('Failed to insight dungeon after 3 trial')
        return False

    def dungeon_insight(self, dungeon: DungeonList):
        """
        Insight a dungeon

        Pages:
            in: page_guide, Survival_Index, nav including dungeon
            out: page_guide, Survival_Index, nav including dungeon, dungeon insight
        """
        if dungeon.is_Calyx_Crimson or dungeon.is_Stagnant_Shadow:
            # Having dungeon sorting and early access
            self._dungeon_insight_sort(dungeon)
        else:
            self._dungeon_insight_index(dungeon)

    def _dungeon_enter(self, dungeon, enter_check_button=COMBAT_PREPARE, skip_first_screenshot=True):
        """
        Pages:
            in: page_guide, Survival_Index, nav including dungeon
            out: COMBAT_PREPARE, FORGOTTEN_HALL_CHECK
        """
        logger.hr('Dungeon enter', level=2)
        DUNGEON_LIST.target_dungeon = dungeon
        skip_first_load = skip_first_screenshot

        @run_once
        def screenshot_interval_set():
            self.device.screenshot_interval_set('combat')

        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.appear(enter_check_button):
                logger.info(f'Arrive {enter_check_button.name}')
                break

            # Additional
            # Popup that confirm character switch
            if self.handle_popup_confirm():
                self.interval_reset(page_guide.check_button)
                continue
            # Close obtain info
            if self.appear_then_click(ITEM_CLOSE):
                continue
            # Close enemy info
            if self.handle_ui_close(ENEMY_INFO_CHECK, interval=5):
                continue

            # Click teleport
            if self.appear(page_guide.check_button, interval=1):
                if skip_first_load:
                    skip_first_load = False
                else:
                    DUNGEON_LIST.load_rows(main=self)
                entrance = DUNGEON_LIST.keyword2button(dungeon)
                if entrance is not None:
                    # Avoid clicking the soring button
                    entrance.button = area_limit(entrance.button, OCR_DUNGEON_TELEPORT.area)
                    self.device.click(entrance)
                    screenshot_interval_set()
                    self.interval_reset(page_guide.check_button)
                    continue
                else:
                    logger.warning(f'Cannot find dungeon entrance of {dungeon}')
                    continue

        self.device.screenshot_interval_set()


if __name__ == '__main__':
    self = DungeonUIList('src')
    self.device.screenshot()
    self.dungeon_insight(KEYWORDS_DUNGEON_LIST.Echo_of_War_Divine_Seed)
