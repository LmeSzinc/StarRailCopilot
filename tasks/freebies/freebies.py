from module.base.base import ModuleBase
from module.logger import logger
from tasks.freebies.code import RedemptionCode
from tasks.freebies.support_reward import SupportReward


class Freebies(ModuleBase):
    def run(self):
        """
        Run all freebie tasks
        """
        if self.config.Freebies_SupportReward:
            logger.hr('Support Reward', level=1)
            SupportReward(config=self.config, device=self.device).run()

        if self.config.Freebies_RedemptionCode:
            logger.hr('Redemption Code', level=1)
            RedemptionCode(config=self.config, device=self.device).run()

        self.config.task_delay(server_update=True)
