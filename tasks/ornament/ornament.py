from datetime import timedelta

from module.config.stored.classes import now
from module.config.utils import DEFAULT_TIME
from module.exception import ScriptError
from module.logger import logger
from tasks.dungeon.assets.assets_dungeon_ui_rogue import DIVERGENT_UNIVERSE_SAVE_UNAVAILABLE
from tasks.dungeon.keywords import DungeonList
from tasks.ornament.combat import OrnamentCombat


class Ornament(OrnamentCombat):
    # Reuse support, cause exit and re-enter is so time-wasting in Divergent Universe
    support_once = False

    def _dungeon_wait_until_dungeon_list_loaded(self, skip_first_screenshot=True):

        result = super()._dungeon_wait_until_dungeon_list_loaded(skip_first_screenshot)

        # Check save file before entering
        if self.image_color_count(
                DIVERGENT_UNIVERSE_SAVE_UNAVAILABLE,
                color=(195, 89, 79), threshold=221, count=1000,
        ):
            logger.error(
                'Divergent Universe save unavailable, '
                'please clear Divergent Universe once before running Ornament Extraction'
            )
            self.config.task_delay(server_update=True)
            self.config.task_stop()

        # Always update double rogue
        record = self.config.stored.DungeonDouble.time
        if now() - record < timedelta(seconds=5):
            # Updated just now
            pass
        else:
            if self.has_double_relic_event():
                rogue = self.get_double_rogue_remain()
                self.config.stored.DungeonDouble.rogue = rogue
            else:
                logger.info('No double rogue event')

        # Check stamina
        logger.info('Check stamina')
        stamina = self.combat_get_trailblaze_power()
        if self.config.Ornament_UseStamina:
            if stamina < self.combat_wave_cost:
                logger.info('Current trailblaze power is not enough for a run')
                self.delay_dungeon_task(self.dungeon)
                self.config.task_stop()
        elif self.config.stored.DungeonDouble.rogue > 0:
            if stamina < self.combat_wave_cost:
                logger.info('Doing double rogue, current trailblaze power is not enough for a run')
                self.delay_dungeon_task(self.dungeon)
                self.config.task_stop()
        else:
            if self.config.stored.Immersifier.value <= 0:
                logger.info('Current immersifier is not enough for a run')
                self.config.task_delay(server_update=True)
                self.config.task_stop()

        return result

    def run(self):
        self.config.update_battle_pass_quests()
        self.config.update_daily_quests()
        # self.check_synthesize()
        self.called_daily_support = False
        self.achieved_daily_quest = False
        self.achieved_weekly_quest = False
        self.running_double = False
        self.daily_quests = self.config.stored.DailyQuest.load_quests()
        self.weekly_quests = self.config.stored.BattlePassWeeklyQuest.load_quests()
        self.update_double_event_record()

        # During double event, do it first
        if self.config.stored.DungeonDouble.calyx or self.config.stored.DungeonDouble.relic:
            logger.info('During double calyx or relic event, delay Ornament')
            future = self.config.cross_get('Dungeon.Scheduler.NextRun', default=DEFAULT_TIME)
            future = future + timedelta(minutes=1)
            with self.config.multi_set():
                self.config.task_delay(target=future)
                self.config.task_stop()

        # Run
        dungeon = DungeonList.find(self.config.Ornament_Dungeon)
        self.support_once = False
        self.combat_wave_cost = 40
        self.dungeon = dungeon
        if self.config.Ornament_UseStamina:
            # No limit
            self.dungeon_run(dungeon, wave_limit=0)
            # Stamina should have exhausted in dungeon_run
            raise ScriptError('Ornament finished but stamina was not exhausted')
        elif self.config.stored.DungeonDouble.rogue > 0:
            # Limited in double events
            self.running_double = True
            self.dungeon_run(dungeon, wave_limit=self.config.stored.DungeonDouble.rogue)
            self.running_double = False
            self.dungeon_stamina_delay(dungeon)
        else:
            # Use immersifier only, wave limited in _dungeon_wait_until_dungeon_list_loaded
            self.dungeon_run(dungeon, wave_limit=0)
            self.dungeon_stamina_delay(dungeon)
