import time
import os
from datetime import datetime

from module.base.timer import Timer
from tasks.base.ui import UI
from module.device.method import maatouch
from module.logger import logger
from tasks.base.main_page import MainPage
from tasks.base.page import page_main
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
    # Remove aim_interval if AimDetectorMixin is no longer part of this class
    # aim_interval = Timer(0.3, count=1)

    def __init__(self, device, config, task=None):
        super().__init__(config=config, device=device, task=task)
        self.device.disable_stuck_detection()
        self.achievements_collector = AchievementsCollector(device, config)
        self.simulated_universe_collector = SimulatedUniverseCollector(device, config)

    # _click_coord_and_attempt_claim method has been moved to AchievementsCollector

    def run(self):
        self.simulated_universe_collector.run_simulated_universe()
        time.sleep(1000000000)
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
            logger.info("Collect Achievements is enabled. Starting achievements collection...")
            self.achievements_collector.run_achievements()
            logger.info("Achievements collection finished.")
        else:
            logger.info("Collect Achievements is disabled.")

        if collect_simulated_universe:
            self.ui_ensure(page_main)
            logger.info("Collect Simulated Universe is enabled. Starting SU collection...")
            self.simulated_universe_collector.run_simulated_universe()
            logger.info("Simulated Universe collection finished.")
        else:
            logger.info("Collect Simulated Universe is disabled.")

        self.ui_ensure(page_main)
        logger.info("RewardCollector main run cycle finished.")
                