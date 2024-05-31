from module.base.timer import Timer
from module.logger import logger
from tasks.base.assets.assets_base_page import CLOSE
from tasks.relics.assets.assets_relics import *
from tasks.item.keywords import KEYWORDS_ITEM_TAB
from tasks.item.ui import ItemUI


class RelicsUI(ItemUI):
    def _is_in_salvage(self) -> bool:
        if self._is_in_relic_filter:
            return False
        else:
            return self.appear(SALVAGE_ORDER_ASCENDING) or self.appear(SALVAGE_ORDER_DESCENDING)

    def salvage_exit(self, skip_first_screenshot=True):
        """
        Pages:
            in: rewards claimed
                or _is_in_salvage()
            out: GOTO_SALVAGE
        """
        interval = Timer(1)
        while 1:
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

    def _is_in_relic_filter(self) -> bool:
        return self.appear(FILTER_CONFIRM) and self.appear(FILTER_RESET)

    def item_goto_salvage(self, skip_first_screenshot=True) -> bool:
        """item/relic -> salvage

        Args:
            skip_first_screenshot (bool, optional): Defaults to True.

        Returns:
            bool: True means reached salvage

        Pages:
            in: item/relic
            out: salvage
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._is_in_salvage():
                logger.info('_is_in_salvage')
                return True
            if self.appear_then_click(GOTO_SALVAGE, interval=2):
                continue

    def salvage_goto_filter(self, skip_first_screenshot=True) -> bool:
        """salvage -> salvage relic filter

        Args:
            skip_first_screenshot (bool, optional): Defaults to True.

        Returns:
            bool: True means reached salvage filter

        Pages:
            in: salvage
            out: salvage filter
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._is_in_relic_filter():
                logger.info('_is_in_relic_filter')
                return True
            if self.appear_then_click(GOTO_SALVAGE_FILTER, interval=2):
                continue

    def relic_goto_enhance_filter(self, skip_first_screenshot=True) -> bool:
        """item/relic -> relic enhance filter

        Args:
            skip_first_screenshot (bool, optional): Defaults to True.

        Returns:
            bool: True means reached enhance filter

        Pages:
            in: item/relic
            out: enhance filter
        """
        # Enhance filter button is in a different location compared to salvage filter.
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._is_in_relic_filter():
                logger.info('_is_in_relic_filter')
                return True
            if self.appear_then_click(GOTO_ENHANCE_FILTER, interval=2):
                continue

    def relic_filter_confirm(self, skip_first_screenshot=True) -> bool:
        """Click confirm button of the relic filter.

        Args:
            skip_first_screenshot (bool, optional): Defaults to True.

        Returns:
            bool: True means confirm button clicked.

        Pages:
            in: (enhance or salvage) relic filter
            out: (enhance or salvage) relic selection
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._is_in_relic_filter():
                logger.info('_is_in_relic_filter')
            else:
                logger.info('Not in relic filter panel, retrying...')
                continue
            if self.appear_then_click(FILTER_CONFIRM, interval=2):
                return True

    def relic_filter_reset(self, skip_first_screenshot=True) -> bool:
        """Click reset button of the relic filter.

        Args:
            skip_first_screenshot (bool, optional): Defaults to True.

        Returns:
            bool: True means reset button clicked.

        Pages:
            in: (enhance or salvage) relic filter
            out: (enhance or salvage) relic filter
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self._is_in_relic_filter():
                logger.info('_is_in_relic_filter')
            else:
                logger.info('Not in relic filter panel, retrying...')
                continue
            if self.appear_then_click(FILTER_RESET, interval=2):
                return True

    def salvage_selected(self, skip_first_screenshot=True) -> bool:
        """Click salvage button.

        Args:
            skip_first_screenshot (bool, optional): Defaults to True.

        Returns:
            bool: True means salvage button clicked.

        Pages:
            in: relic salvage
            out: relic salvage
        """
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.reward_appear():
                logger.info("Relic salvaged")
                return True
            if self.appear_then_click(SALVAGE, interval=2):
                continue
            if self.handle_popup_confirm():
                continue



if __name__ == '__main__':
    ui = RelicsUI('src')
    ui.image_file = r"Screenshot_2024.05.31_02.00.56.554.png"
    print(ui.appear(SUB_STAT_SELECT))
