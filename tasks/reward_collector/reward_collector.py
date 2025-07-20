from datetime import datetime
from module.base.button import ClickButton
from module.base.timer import Timer
from tasks.base.ui import UI
from module.device.method import maatouch
from module.logger import logger
from tasks.base.main_page import MainPage
from tasks.base.page import page_main
from tasks.reward_collector.assets.assets_reward_collector_Achievement import Achieved, Achieved_Click, Claim
from tasks.reward_collector.assets.assets_reward_collector_Simulated import BlessingClaim, BlessingClaim2
from .achievements_collector import AchievementsCollector
from .simulated_universe_collector import SimulatedUniverseCollector

class SecondaryMaatouchBuilder(maatouch.MaatouchBuilder):
    def __init__(self, device, contact=0, handle_orientation=False):
        """
        Click on secondary contact to avoid interruption of real-person contact
        """
        if contact == 0:
            contact = 2
        super().__init__(device, contact=contact, handle_orientation=handle_orientation)


maatouch.MaatouchBuilder = SecondaryMaatouchBuilder

class RewardCollector(UI):

    def __init__(self, device, config, task=None):
        super().__init__(config=config, device=device, task=task)
        self.device.disable_stuck_detection()
        self.achievements_collector = AchievementsCollector(device, config)
        self.simulated_universe_collector = SimulatedUniverseCollector(device, config)

    def run(self):
        self.config.bind('RewardCollector')

        builder = self.device.maatouch_builder
        if builder.contact >= 1:
            logger.info(f'Maatouch contact on {builder.contact}')
        else:
            logger.warning(f'Maatouch contact on {builder.contact}, may cause interruptions')
          
        self.ui_ensure(page_main)

        collect_achievements = self.config.RewardCollector_CollectAchievements
        collect_simulated_universe = self.config.RewardCollector_CollectSimulatedUniverse

        if collect_achievements:
            self.ui_ensure(page_main)
            logger.info("Starting Achievement reward collection (enabled in config)...")
            self.achievements_collector.run_achievements()
            logger.info("Achievement collection complete.")
        else:
            logger.info("Achievement collection disabled in config.")

        if collect_simulated_universe:
            self.ui_ensure(page_main)
            logger.info("Starting Simulated Universe reward collection (enabled in config)...")
            self.simulated_universe_collector.run_simulated_universe()
            logger.info("Simulated Universe collection complete.")
        else:
            logger.info("Simulated Universe collection disabled in config.")

        self.ui_ensure(page_main)

        self.config.task_delay(server_update=True)

        logger.info("RewardCollector task complete.")