from module.base.base import ModuleBase
from module.logger import logger
from tasks.freebies.code import RedemptionCode
from tasks.freebies.mail import MailReward
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

        # To actually get RedemptionCode rewards, you need to receive the mail
        if self.config.Freebies_RedemptionCode or self.config.Freebies_MailReward:
            logger.hr('Mail Reward', level=1)
            MailReward(config=self.config, device=self.device).mail_claim_all()

        self.config.task_delay(server_update=True)
