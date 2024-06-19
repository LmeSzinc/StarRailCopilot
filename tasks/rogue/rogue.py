from module.exception import ScriptError
from module.logger import logger
from tasks.battle_pass.keywords import KEYWORDS_BATTLE_PASS_QUEST
from tasks.daily.keywords import KEYWORDS_DAILY_QUEST
from tasks.rogue.entry.entry import RogueEntry
from tasks.rogue.exception import RogueReachedWeeklyPointLimit, RogueTeamNotPrepared
from tasks.rogue.route.loader import RouteLoader


class Rogue(RouteLoader, RogueEntry):
    def rogue_once(self):
        """
        Do a complete rogue run.

        Pages:
            in: Any
            out: page_rogue, is_page_rogue_main()
        """
        try:
            self.rogue_world_enter()
        except RogueTeamNotPrepared:
            logger.error(f'Please prepare your team in {self.config.RogueWorld_World} '
                         f'and start rogue task at team preparation page')
            raise ScriptError
        except RogueReachedWeeklyPointLimit:
            logger.hr('Reached rogue weekly point limit')
            return False

        self.rogue_run()
        self.rogue_reward_claim()
        return True

    def run(self):
        self.config.update_battle_pass_quests()
        self.config.update_daily_quests()
        if self.config.stored.DungeonDouble.is_expired():
            self.config.task_call('Dungeon')
            self.config.task_stop()

        # Run
        success = self.rogue_once()

        # Scheduler
        with self.config.multi_set():
            # Task switched
            if self.config.task_switched():
                self.config.task_stop()
            # Archived daily quest
            if success:
                quests = self.config.stored.DailyQuest.load_quests()
                if KEYWORDS_DAILY_QUEST.Complete_Divergent_Universe_or_Simulated_Universe_1_times in quests:
                    logger.info('Achieve daily quest Complete_Divergent_Universe_or_Simulated_Universe_1_times')
                    self.config.task_call('DailyQuest')
                    self.config.task_stop()
                quests = self.config.stored.BattlePassWeeklyQuest.load_quests()
                if KEYWORDS_BATTLE_PASS_QUEST.Complete_Divergent_Universe_or_Simulated_Universe_1_times in quests:
                    logger.info('Achieve battle pass quest Complete_Divergent_Universe_or_Simulated_Universe_1_times')
                    self.config.task_call('BattlePass')
                    self.config.task_stop()
            # End
            if success:
                logger.info('Rogue run success')
                # Call rogue itself, so multiple rogue runs are considered as separated tasks
                # which won't trigger failure count >= 3 when clearing 100 elites
                self.config.task_call('Rogue')
            else:
                logger.info('Rogue run failed')
                self.config.task_delay(server_update=True)


if __name__ == '__main__':
    self = Rogue('src', task='Rogue')
    self.device.screenshot()
    self.rogue_once()
