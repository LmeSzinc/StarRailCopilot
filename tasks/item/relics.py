from module.base.timer import Timer
from module.logger import logger
from tasks.base.assets.assets_base_popup import CONFIRM_POPUP
from tasks.item.assets.assets_item_relics import *
from tasks.item.keywords import KEYWORD_ITEM_TAB
from tasks.item.ui import ItemUI


class RelicsUI(ItemUI):
    def salvage_relic(self, skip_first_screenshot=True) -> bool:
        self.item_goto(KEYWORD_ITEM_TAB.Relics)
        interval = Timer(1)
        while 1:  # relic tab -> salvage
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(REVERSE_ORDER):
                break
            if self.appear_then_click(GOTO_SALVAGE):
                continue

        skip_first_screenshot = True
        while 1:  # salvage -> first relic selected
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.appear(SALVAGE):
                break
            if self.appear_then_click(REVERSE_ORDER):
                continue
            if interval.reached() and self.appear_then_click(FIRST_RELIC):
                interval.reset()
                continue

        skip_first_screenshot = True
        while 1:  # selected -> rewards claimed
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            if self.handle_reward():
                logger.info("Relic salvaged")
                break
            if self.appear_then_click(SALVAGE):
                continue
            if self.appear_then_click(CONFIRM_POPUP):
                continue
        return True
