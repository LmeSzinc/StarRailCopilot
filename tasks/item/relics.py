from module.boundary_detection import utils
from module.base.timer import Timer
from module.logger import logger
from tasks.base.assets.assets_base_page import CLOSE
from tasks.base.assets.assets_base_popup import GET_REWARD
from tasks.item.assets.assets_item_relics import *
from tasks.item.keywords import KEYWORD_ITEM_TAB
from tasks.item.ui import ItemUI

import time

class RelicsUI(ItemUI):

    def _is_in_salvage(self) -> bool:
        return self.appear(ORDER_ASCENDING) or self.appear(ORDER_DESCENDING)


    def salvage_relic(self, skip_first_screenshot=True) -> bool:
        logger.hr('Salvage Relic', level=2)
        self.item_goto(KEYWORD_ITEM_TAB.Relics, wait_until_stable=False)
        while 1:  # relic tab -> salvage
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._is_in_salvage():
                logger.info('_is_in_salvage')
                break
            if self.appear_then_click(GOTO_SALVAGE, interval=2):
                continue

        skip_first_screenshot = True
        interval = Timer(1)
        relics_selected_count = 0
        relics_selected_sign = None
        while 1:  # salvage -> first relic selected
            logger.info("Start Iteration")
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            h_bound, v_bound = utils.get_object_rectangles(self.device.image, RELICS_SAVAGE_AREA.area)

            if len(h_bound) == 0 or len(v_bound) == 0:
                continue

            relics_v_index = relics_selected_count % len(v_bound)
            relics_h_index = (int)((relics_selected_count - relics_v_index) / len(v_bound))

            relics_v = v_bound[relics_v_index]
            relics_h = h_bound[relics_h_index]
            relic= RelicsUI._get_relics_button(relics_v, relics_h)

            # The first frame entering relic page, SALVAGE is a white button as it's the default state.
            # At the second frame, SALVAGE is disabled since no items are selected.
            # So here uses the minus button on the first relic.
            if relics_selected_sign is not None and self.image_color_count(relics_selected_sign, color=(245, 245, 245), threshold=221, count=100):
                logger.info('First relic selected')
                break

            if self.appear_then_click(ORDER_DESCENDING, interval=2):
                continue

            if interval.reached() and self.appear(ORDER_ASCENDING) \
                    and self.image_color_count(relic, (233, 192, 108)):
                self.device.click(relic)

                relics_selected_count += 1
                logger.info(f"Trying to find the savagable relics for the {relics_selected_count} time")

                time.sleep(3)
                relics_selected_sign = RelicsUI._get_relics_selected_button(relics_v, relics_h)

                interval.reset()
                continue

        skip_first_screenshot = True
        while 1:  # selected -> rewards claimed
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(GET_REWARD):
                logger.info("Relic salvaged")
                break
            if self.appear_then_click(SALVAGE, interval=2):
                continue
            if self.handle_popup_confirm():
                continue

        skip_first_screenshot = True
        interval = Timer(1)
        while 1:  # rewards claimed -> relic tab page
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(GOTO_SALVAGE):
                logger.info("Salvage page exited")
                break
            if self.handle_reward(interval=2):
                continue
            if interval.reached() and self._is_in_salvage():
                logger.info(f'_is_in_salvage -> {CLOSE}')
                self.device.click(CLOSE)
                interval.reset()
                continue
        return True


    @staticmethod
    def _get_relics_button(relics_v_bound, relics_h_bound):
        area = (relics_v_bound[0], relics_h_bound[0], relics_v_bound[1], relics_h_bound[1])
        search = (area[0] - 20, area[1] - 20, area[2] + 20, area[3] + 20)
        return Button(
            file='./assets/share/item/relics/FIRST_RELIC.png',
            area=area,
            search=search,
            color=(72, 92, 124),
            button=area,
        )


    @staticmethod
    def _get_relics_selected_button(relics_v_bound, relics_h_bound):
        area = (relics_v_bound[0] - 10, relics_h_bound[0] - 24, relics_v_bound[0] + 18, relics_h_bound[0] + 4)
        search = (area[0] - 20, area[1] - 20, area[2] + 20, area[3] + 20)
        return Button(
            file='./assets/share/item/relics/FIRST_RELIC_SELECTED.png',
            area=area,
            search=search,
            color=(193, 194, 198),
            button=area,
        )
