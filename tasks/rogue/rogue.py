from module.exception import RequestHumanTakeover
from module.logger import logger
from tasks.base.assets.assets_base_main_page import ROGUE_LEAVE_FOR_NOW
from tasks.base.assets.assets_base_page import MAP_EXIT
from tasks.battle_pass.keywords import KEYWORDS_BATTLE_PASS_QUEST
from tasks.daily.keywords import KEYWORDS_DAILY_QUEST
from tasks.rogue.assets.assets_rogue_ui import BLESSING_CONFIRM
from tasks.rogue.assets.assets_rogue_weekly import ROGUE_REPORT
from tasks.rogue.entry.entry import RogueEntry
from tasks.rogue.exception import RogueReachedWeeklyPointLimit, RogueTeamNotPrepared
from tasks.rogue.route.loader import RouteLoader


class Rogue(RouteLoader, RogueEntry):
    def rogue_leave(self, skip_first_screenshot=True):
        logger.hr('Rogue leave', level=1)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_page_rogue_main():
                logger.info('Rogue left')
                break

            # Re-enter
            if self.handle_combat_interact():
                continue
            # From ui_leave_special
            if self.is_in_map_exit(interval=2):
                self.device.click(MAP_EXIT)
                continue
            if self.handle_popup_confirm():
                continue
            if self.appear_then_click(ROGUE_LEAVE_FOR_NOW, interval=2):
                continue
            # Blessing
            if self.handle_blessing():
                continue
            # _domain_exit_wait_next()
            if self.match_template_color(ROGUE_REPORT, interval=2):
                logger.info(f'{ROGUE_REPORT} -> {BLESSING_CONFIRM}')
                self.device.click(BLESSING_CONFIRM)
                continue
            if self.handle_reward():
                continue
            if self.handle_get_character():
                continue

    def route_error_postprocess(self):
        """
        When having route error, leave for now and re-enter
        May be another trial would fix it
        """
        self.rogue_leave()
        return True

    def rogue_run(self, skip_first_screenshot=True):
        """
        Do a complete rogue run, no error handle yet.

        Pages:
            in: page_rogue, is_page_rogue_launch()
            out: page_rogue, is_page_rogue_main()
        """
        count = 1
        self.character_is_ranged = None
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            logger.hr(f'Route run: {count}', level=1)
            self.clear_blessing()
            self.character_switch_to_ranged(update=True)

            self.route_run()
            # if not success:
            #     self.device.image_save()
            #     continue

            # End
            if self.is_page_rogue_main():
                break

            count += 1

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
            raise RequestHumanTakeover
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
