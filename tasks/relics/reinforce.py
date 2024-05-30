from module.base.timer import Timer
from module.logger import logger
from tasks.item.keywords import KEYWORDS_ITEM_TAB
from tasks.relics.ui import RelicsUI


class RelicsReinforce(RelicsUI):
    def reinforce(self, skip_first_screenshot=True) -> bool:
        """Reinforce relics.

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

        raise NotImplementedError
