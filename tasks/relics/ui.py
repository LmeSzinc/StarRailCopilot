from module.logger import logger
from tasks.base.assets.assets_base_page import CLOSE
from tasks.base.page import page_item
from tasks.item.keywords import KEYWORDS_ITEM_TAB
from tasks.item.ui import ItemUI
from tasks.relics.assets.assets_relics_ui import *


class RelicsUI(ItemUI):
    def is_in_relics_enhance(self, interval=0):
        if self.appear(ENHANCE_CHECK, interval=interval):
            return True
        return False

    def is_in_relics_salvage(self, interval=0):
        if self.appear(SALVAGE_CHECK_OFF, interval=interval):
            return True
        if self.appear(SALVAGE_CHECK_ON, interval=interval):
            return True
        return False

    def is_filter_active(self, button, interval=0) -> bool:
        """
        Args:
            button: ENHANCE_FILTER or SALVAGE_FILTER
            interval:

        Returns:
            bool:
        """
        self.device.stuck_record_add(button)

        if interval and not self.interval_is_reached(button, interval=interval):
            return False

        appear = self.image_color_count(button, color=(242, 158, 56), threshold=180, count=20)

        if appear and interval:
            self.interval_reset(button, interval=interval)

        return appear

    def is_filter_appear(self, button, interval=0) -> bool:
        if self.appear(button, interval=interval):
            return True
        if self.is_filter_active(button, interval=interval):
            return True
        return False

    def is_filter_opened(self, interval=0) -> bool:
        return self.appear(FILTER_CONFIRM, interval=interval)

    def handle_filter_confirm(self, button, interval=2) -> bool:
        """
        Confirm filter aside

        Args:
            button: ENHANCE_FILTER or SALVAGE_FILTER
            interval:

        Returns:
            bool: If clicked
        """
        if self.appear(button):
            if self.appear_then_click(FILTER_CONFIRM, interval=interval):
                self.interval_clear(FILTER_RESET)
                return True
        return False

    def handle_filter_reset(self, button, interval=2):
        """
        Reset filter aside

        Args:
            button: ENHANCE_FILTER or SALVAGE_FILTER
            interval:

        Returns:
            bool: If clicked
        """
        if self.is_filter_active(button):
            if self.appear_then_click(FILTER_RESET, interval=interval):
                self.interval_clear(FILTER_CONFIRM)
                return True
        return False

    def handle_filter_close(self, opened=None, interval=2):
        """
        Args:
            opened: ENHANCE_FILTER or SALVAGE_FILTER
                Keep this filter opened
            interval:

        Returns:
            bool: If clicked
        """
        # If filter opened, reset it
        if self.handle_filter_reset(SALVAGE_FILTER, interval=interval):
            self.interval_reset([SALVAGE_FILTER], interval=interval)
            return True
        if self.handle_filter_reset(ENHANCE_FILTER, interval=interval):
            self.interval_reset([ENHANCE_FILTER], interval=interval)
            return True
        # If filter opened, close it
        if opened != SALVAGE_FILTER:
            if self.handle_filter_confirm(SALVAGE_FILTER, interval=interval):
                self.interval_clear([FILTER_CONFIRM, SALVAGE_CHECK_OFF, SALVAGE_CHECK_ON], interval=interval)
                return True
        if opened != ENHANCE_FILTER:
            if self.handle_filter_confirm(ENHANCE_FILTER, interval=interval):
                self.interval_clear([FILTER_CONFIRM, ENHANCE_CHECK], interval=interval)
                return True
        # If filter activated, open it
        if self.is_filter_active(SALVAGE_FILTER, interval=interval):
            logger.info(f'is_filter_active -> {SALVAGE_FILTER}')
            self.device.click(SALVAGE_FILTER)
            self.interval_reset([FILTER_CONFIRM, SALVAGE_CHECK_OFF, SALVAGE_CHECK_ON], interval=interval)
            return True
        if self.is_filter_active(ENHANCE_FILTER, interval=interval):
            logger.info(f'is_filter_active -> {ENHANCE_FILTER}')
            self.device.click(ENHANCE_FILTER)
            self.interval_reset([FILTER_CONFIRM, ENHANCE_CHECK], interval=interval)
            return True
        return False

    def relics_goto_salvage_filter(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_item, any subpage of relics
            out: salvage filter, with filter reset
        """
        logger.info('Relics goto salvage filter')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_filter_opened() and self.appear(SALVAGE_FILTER):
                logger.info('Arrive SALVAGE_FILTER')
                break

            # Close filter
            if self.handle_filter_close(opened=SALVAGE_FILTER):
                continue
            # Open filter
            if not self.is_filter_opened():
                # if self.is_filter_appear(ENHANCE_FILTER, interval=2):
                #     self.device.click(ENHANCE_FILTER)
                #     continue
                if self.is_filter_appear(SALVAGE_FILTER, interval=2):
                    self.device.click(SALVAGE_FILTER)
                    continue
            # UI switch
            if self.is_in_relics_enhance(interval=2):
                self.device.click(ENHANCE_GOTO_SALVAGE)
                continue
            # if self.is_in_relics_salvage(interval=2):
            #     logger.info(f'is_in_relics_salvage -> {CLOSE}')
            #     self.device.click(CLOSE)
            #     continue

    def relics_goto_salvage(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_item, any subpage of relics
            out: salvage, with filter reset
        """
        logger.info('Relics goto salvage')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_in_relics_salvage() and self.appear(SALVAGE_FILTER):
                logger.info('Arrive is_in_relics_salvage')
                break

            # Close filter
            if self.handle_filter_close():
                continue
            # UI switch
            if self.is_in_relics_enhance(interval=2):
                self.device.click(ENHANCE_GOTO_SALVAGE)
                continue

    def relics_goto_enhance_filter(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_item, any subpage of relics
            out: enhance filter, with filter reset
        """
        logger.info('Relics goto enhance filter')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_filter_opened() and self.appear(ENHANCE_FILTER):
                logger.info('Arrive ENHANCE_FILTER')
                break

            # Close filter
            if self.handle_filter_close(opened=ENHANCE_FILTER):
                continue
            # Open filter
            if not self.is_filter_opened():
                if self.is_filter_appear(ENHANCE_FILTER, interval=2):
                    self.device.click(ENHANCE_FILTER)
                    continue
            # UI switch
            if self.is_in_relics_salvage(interval=2):
                logger.info(f'is_in_relics_salvage -> {CLOSE}')
                self.device.click(CLOSE)
                continue

    def relics_goto_enhance(self, skip_first_screenshot=True):
        """
        Pages:
            in: page_item, any subpage of relics
            out: enhance, with filter reset
        """
        logger.info('Relics goto enhance')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_in_relics_enhance() and self.appear(ENHANCE_FILTER):
                logger.info('Arrive is_in_relics_enhance')
                break

            # Close filter
            if self.handle_filter_close():
                continue
            # UI switch
            if self.is_in_relics_salvage(interval=2):
                logger.info(f'is_in_relics_salvage -> {CLOSE}')
                self.device.click(CLOSE)
                continue

    def ui_goto_relics(self):
        self.ui_ensure(page_item)
        self.item_goto(KEYWORDS_ITEM_TAB.Relics, wait_until_stable=False)


if __name__ == '__main__':
    self = RelicsUI('src')
    self.device.screenshot()
    self.relics_goto_salvage_filter()
