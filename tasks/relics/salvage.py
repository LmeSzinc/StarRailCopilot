from module.base.timer import Timer
from module.logger import logger
from tasks.item.keywords import KEYWORDS_ITEM_TAB
from tasks.relics.ui import RelicsUI

class RelicsSalvage(RelicsUI):
    """Component of Relics class.
    Contains methods of relic salvage.
    """
    def salvage(self, skip_first_screenshot=True) -> bool:
        """Salvages useless relics.

        Args:
            skip_first_screenshot (bool, optional): Defaults to True.

        Returns:
            bool: If success
            
        Pages:
            in: Any
            out: page_item
        """
        logger.hr('Salvage Relic', level=2)
        self.item_goto(KEYWORDS_ITEM_TAB.Relics, wait_until_stable=False)

        self.item_goto_salvage(skip_first_screenshot)

        self.salvage_goto_filter()

        self.relic_filter_reset()

        # TODO: Set the filter

        self.relic_filter_confirm()

        self.salvage_selected()

        self.salvage_exit()


