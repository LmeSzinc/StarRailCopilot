from module.logger import logger
from module.base.base import ModuleBase
from tasks.freebies.support_reward import SupportReward
from tasks.freebies.gift_of_odyssey import GiftofOdyssey


class Freebies(ModuleBase):
    def run(self):
        """
        Run all freebie tasks
        """
        if self.config.SupportReward_Collect:
            logger.hr('Support Reward')
            SupportReward(config=self.config, device=self.device).run()
        if self.config.GiftofOdyssey_Collect:
            logger.hr('Gift of Odyssey')
            if self.config.stored.GiftofOdysseyClaimed == 7:
                logger.hr('All Claimed in this patch')
            else:
                GiftofOdyssey(config=self.config, device=self.device).run()

        self.config.task_delay(server_update=True)

