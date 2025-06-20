from datetime import timedelta

from module.base.decorator import set_cached_property
from module.config.stored.classes import now
from module.logger import logger
from tasks.battle_pass.keywords import KEYWORDS_BATTLE_PASS_QUEST
from tasks.combat.combat import Combat
from tasks.daily.keywords import KEYWORDS_DAILY_QUEST
from tasks.dungeon.event import DungeonEvent
from tasks.dungeon.keywords import DungeonList, KEYWORDS_DUNGEON_LIST, KEYWORDS_DUNGEON_NAV, KEYWORDS_DUNGEON_TAB
from tasks.dungeon.stamina import DungeonStamina
from tasks.freebies.code_used import CodeManager
from tasks.item.synthesize import Synthesize


class Dungeon(Combat, DungeonStamina, DungeonEvent):
    # Value cleared in Dungeon.run()
    daily_quests = []
    weekly_quests = []
    # Value cleared in Dungeon.run()
    # Value set in _dungeon_run()
    called_daily_support = False
    achieved_daily_quest = False
    achieved_weekly_quest = False
    # Whether is running a double dungeon
    # Value set in Dungeon.run()
    running_double = False
    # True to use support once and run rest without support
    # False to use support til the end
    # In most cases to be true to use support less often but False is Ornament.
    # because a game bug that support characters override your 4th character and empty the 4th slot when you dismiss
    # the support. To avoid that, use support til the end in Ornament combats.
    support_once = True

    def _dungeon_run(self, dungeon: DungeonList, team: int = None, wave_limit: int = 0, support_character: str = None,
                     skip_ui_switch: bool = False):
        """
        Args:
            dungeon:
            team: 1 to 6.
            wave_limit: Limit combat runs, 0 means no limit.
            support_character: Support character name
            skip_ui_switch: True if already at dungeon aside

        Returns:
            int: Run count

        Pages:
            in: page_main, DUNGEON_COMBAT_INTERACT
                or COMBAT_PREPARE
            out: page_main
        """
        if team is None:
            team = self.config.Dungeon_Team
        if support_character is None and self.config.DungeonSupport_Use == 'always_use':
            support_character = self.config.DungeonSupport_Character

        logger.hr('Dungeon run', level=1)
        logger.info(f'Dungeon: {dungeon}, team={team}, wave_limit={wave_limit}, support_character={support_character}')

        if not skip_ui_switch:
            interact = self.get_dungeon_interact()
            if interact is not None and interact == dungeon:
                logger.info('Already nearby dungeon')
            else:
                self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Survival_Index)
                self.dungeon_goto(dungeon)

        self.combat_enter_from_map()
        # Check double event remain before combat
        # Conservatively prefer the smaller result
        if (dungeon.is_Calyx_Golden or dungeon.is_Calyx_Crimson) and \
                self.running_double and self.config.stored.DungeonDouble.calyx > 0:
            calyx = self.get_double_event_remain_at_combat()
            if calyx is not None and calyx < self.config.stored.DungeonDouble.calyx:
                self.config.stored.DungeonDouble.calyx = calyx
                wave_limit = calyx
            if calyx == 0:
                return 0
        if dungeon.is_Cavern_of_Corrosion and self.running_double and \
                self.config.stored.DungeonDouble.relic > 0:
            relic = self.get_double_event_remain_at_combat()
            if relic is not None and relic < self.config.stored.DungeonDouble.relic:
                self.config.stored.DungeonDouble.relic = relic
                wave_limit = relic
            if relic == 0:
                return 0
        # No need, already checked in Survival_Index
        # if dungeon.is_Ornament_Extraction and self.running_double and \
        #         self.config.stored.DungeonDouble.rogue > 0:
        #     rogue = self.get_double_event_remain_at_combat()
        #     if rogue is not None and rogue < self.config.stored.DungeonDouble.rogue:
        #         self.config.stored.DungeonDouble.rogue = rogue
        #         wave_limit = rogue
        #     if rogue == 0:
        #         return 0

        # Combat
        self.dungeon = dungeon
        count = self.combat(team=team, wave_limit=wave_limit, support_character=support_character)
        self.dungeon = None

        # Update quest states
        with self.config.multi_set():
            # Calyx_Golden
            if dungeon.is_Calyx_Golden:
                if KEYWORDS_DAILY_QUEST.Clear_Calyx_Golden_1_times in self.daily_quests:
                    logger.info('Achieved daily quest Clear_Calyx_Golden_1_times')
                    self.achieved_daily_quest = True
                if KEYWORDS_BATTLE_PASS_QUEST.Clear_Calyx_1_times in self.weekly_quests:
                    logger.info('Done weekly quest Clear_Calyx_1_times once')
                    self.config.stored.BattlePassQuestCalyx.add()
                    if self.config.stored.BattlePassQuestCalyx.is_full():
                        logger.info('Achieved weekly quest BattlePassQuestCalyx')
                        self.achieved_weekly_quest = True
            # Calyx_Crimson
            if dungeon.is_Calyx_Crimson:
                if KEYWORDS_DAILY_QUEST.Clear_Calyx_Crimson_1_times in self.daily_quests:
                    logger.info('Achieve daily quest Clear_Calyx_Crimson_1_times')
                    self.achieved_daily_quest = True
                if KEYWORDS_BATTLE_PASS_QUEST.Clear_Calyx_1_times in self.weekly_quests:
                    logger.info('Done weekly quest Clear_Calyx_1_times once')
                    self.config.stored.BattlePassQuestCalyx.add()
                    if self.config.stored.BattlePassQuestCalyx.is_full():
                        logger.info('Achieved weekly quest BattlePassQuestCalyx')
                        self.achieved_weekly_quest = True
            # Stagnant_Shadow
            if dungeon.is_Stagnant_Shadow:
                if KEYWORDS_DAILY_QUEST.Clear_Stagnant_Shadow_1_times in self.daily_quests:
                    logger.info('Achieve daily quest Clear_Stagnant_Shadow_1_times')
                    self.achieved_daily_quest = True
                if KEYWORDS_BATTLE_PASS_QUEST.Clear_Stagnant_Shadow_1_times in self.weekly_quests:
                    logger.info('Done weekly quest Clear_Stagnant_Shadow_1_times once')
                    self.config.stored.BattlePassQuestStagnantShadow.add()
                    if self.config.stored.BattlePassQuestStagnantShadow.is_full():
                        logger.info('Achieved weekly quest Clear_Stagnant_Shadow_1_times')
                        self.achieved_weekly_quest = True
            # Cavern_of_Corrosion
            if dungeon.is_Cavern_of_Corrosion:
                if KEYWORDS_DAILY_QUEST.Clear_Cavern_of_Corrosion_1_times in self.daily_quests:
                    logger.info('Achieve daily quest Clear_Cavern_of_Corrosion_1_times')
                    self.achieved_daily_quest = True
                if KEYWORDS_BATTLE_PASS_QUEST.Clear_Cavern_of_Corrosion_1_times in self.weekly_quests:
                    logger.info('Done weekly quest Clear_Cavern_of_Corrosion_1_times once')
                    self.config.stored.BattlePassQuestCavernOfCorrosion.add()
                    if self.config.stored.BattlePassQuestCavernOfCorrosion.is_full():
                        logger.info('Achieved weekly quest Clear_Cavern_of_Corrosion_1_times')
                        self.achieved_weekly_quest = True
            # Echo_of_War
            if dungeon.is_Echo_of_War:
                if KEYWORDS_DAILY_QUEST.Complete_Echo_of_War_1_times in self.daily_quests:
                    logger.info('Achieve daily quest Complete_Echo_of_War_1_times')
                    self.achieved_daily_quest = True
                if KEYWORDS_BATTLE_PASS_QUEST.Complete_Echo_of_War_1_times in self.weekly_quests:
                    logger.info('Done weekly quest Complete_Echo_of_War_1_times once')
                    self.config.stored.BattlePassQuestEchoOfWar.add()
                    if self.config.stored.BattlePassQuestEchoOfWar.is_full():
                        logger.info('Achieved weekly quest Complete_Echo_of_War_1_times')
                        self.achieved_weekly_quest = True
            # Ornament_Extraction
            if dungeon.is_Ornament_Extraction:
                if KEYWORDS_BATTLE_PASS_QUEST.Complete_Divergent_Universe_or_Simulated_Universe_1_times in self.weekly_quests:
                    logger.info('Achieved weekly quest Complete_Divergent_Universe_or_Simulated_Universe_1_times')
                    # No need to add since it's 0/1
                    self.achieved_weekly_quest = True
            # Support quest
            if support_character is not None:
                self.called_daily_support = True
                if KEYWORDS_DAILY_QUEST.Obtain_victory_in_combat_with_Support_Characters_1_times in self.daily_quests:
                    logger.info('Achieve daily quest Obtain_victory_in_combat_with_Support_Characters_1_times')
                    self.achieved_daily_quest = True
                    self.pop_daily_support_quest()
            # Stamina quest
            self.check_stamina_quest(self.combat_wave_cost * count)

            # Check trailblaze power, this may stop current task
            if self.is_trailblaze_power_exhausted():
                self.combat_exit()
                # Scheduler
                self.delay_dungeon_task(dungeon)
                self.check_synthesize()
                self.config.task_stop()

        return count

    def dungeon_run(
            self, dungeon: DungeonList, team: int = None, wave_limit: int = 0, support_character: str = None):
        """
        Run dungeon, and handle daily support

        Args:
            dungeon:
            team: 1 to 6.
            wave_limit: Limit combat runs, 0 means no limit.
            support_character: Support character name

        Returns:
            int: Run count

        Pages:
            in: Any
            out: page_main
        """
        require = self.require_compulsory_support()
        if require and self.support_once:
            logger.info('Run once with support')
            count = self._dungeon_run(dungeon=dungeon, team=team, wave_limit=1,
                                      support_character=self.config.DungeonSupport_Character)
            logger.info('Run the rest waves without compulsory support')
            if wave_limit >= 2 or wave_limit == 0:
                # Already at page_name with DUNGEON_COMBAT_INTERACT
                if wave_limit >= 2:
                    wave_limit -= 1
                count += self._dungeon_run(dungeon=dungeon, team=team, wave_limit=wave_limit,
                                           support_character=support_character, skip_ui_switch=True)
            self.combat_exit()
            return count

        elif require and not self.support_once:
            # Run with support all the way
            count = self._dungeon_run(dungeon=dungeon, team=team, wave_limit=0,
                                      support_character=self.config.DungeonSupport_Character)
            self.combat_exit()
            return count

        else:
            # Normal run
            count = self._dungeon_run(dungeon=dungeon, team=team, wave_limit=wave_limit,
                                      support_character=support_character)
            self.combat_exit()
            return count

    def update_double_event_record(self):
        """
        Pages:
            in: Any
            out: page_guide, Survival_Index
        """
        # Update double event records
        if (self.config.stored.DungeonDouble.is_expired()
                or self.config.stored.DungeonDouble.calyx > 0
                or self.config.stored.DungeonDouble.relic > 0
                or self.config.stored.DungeonDouble.rogue > 0):
            update = self.config.stored.DungeonDouble.time
            if update <= now() <= update + timedelta(seconds=5):
                logger.info('Dungeon double just updated, skip')
                return
            logger.info('Get dungeon double remains')
            # UI switches
            switched = self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Survival_Index)
            if not switched and not self._dungeon_survival_index_top_appear():
                logger.info('Reset nav states')
                # Nav must at top, reset nav states
                self.ui_goto_main()
                self.dungeon_tab_goto(KEYWORDS_DUNGEON_TAB.Survival_Index)
            # Check remains
            calyx = 0
            relic = 0
            rogue = 0
            pinned = self.has_pinned_character()
            logger.attr('Pinned character', pinned)
            if self.has_double_rogue_event():
                rogue = self.get_double_rogue_remain()
            if self.has_double_calyx_event():
                self.dungeon_nav_goto(KEYWORDS_DUNGEON_NAV.Calyx_Golden)
                calyx = self.get_double_event_remain()
            if self.has_double_relic_event():
                self.dungeon_nav_goto(KEYWORDS_DUNGEON_NAV.Cavern_of_Corrosion)
                relic = self.get_double_rogue_remain()
            with self.config.multi_set():
                self.config.stored.DungeonDouble.calyx = calyx
                self.config.stored.DungeonDouble.relic = relic
                self.config.stored.DungeonDouble.rogue = rogue

    def pop_daily_support_quest(self):
        """
        Do after calling a support in combat
        so support won't be called again if dungeon task interrupted
        """
        quest = KEYWORDS_DAILY_QUEST.Obtain_victory_in_combat_with_Support_Characters_1_times
        if quest in self.daily_quests:
            logger.info('Pop daily quest Obtain_victory_in_combat_with_Support_Characters_1_times')
            self.daily_quests = [q for q in self.daily_quests if q != quest]
            self.config.stored.DailyQuest.write_quests(self.daily_quests)

    def run(self):
        self.sync_config_traiblaze_power('Ornament')
        self.config.update_battle_pass_quests()
        self.config.update_daily_quests()
        self.check_synthesize()
        self.called_daily_support = False
        self.achieved_daily_quest = False
        self.achieved_weekly_quest = False
        self.running_double = False
        self.daily_quests = self.config.stored.DailyQuest.load_quests()
        self.weekly_quests = self.config.stored.BattlePassWeeklyQuest.load_quests()
        self.update_double_event_record()

        # Run double events
        planner = self.planner.get_dungeon(double_calyx=True)
        # Double calyx
        if self.config.stored.DungeonDouble.calyx > 0:
            logger.info('Run double calyx')
            dungeon = DungeonList.find(self.config.Dungeon_NameAtDoubleCalyx)
            if planner is not None:
                dungeon = planner
                self.is_doing_planner = True
            self.running_double = True
            self.dungeon_run(dungeon=dungeon, wave_limit=self.config.stored.DungeonDouble.calyx)
            self.is_doing_planner = False
        # Double relic
        if self.config.stored.DungeonDouble.relic > 0:
            logger.info('Run double relic')
            dungeon = DungeonList.find(self.config.Dungeon_NameAtDoubleRelic)
            self.running_double = True
            self.dungeon_run(dungeon=dungeon, wave_limit=self.config.stored.DungeonDouble.relic)
        self.running_double = False

        # Dungeon to clear all trailblaze power
        do_rogue = False
        if self.config.is_task_enabled('Rogue') and not self.config.is_task_enabled('Ornament'):
            if self.config.cross_get('Rogue.RogueWorld.UseStamina'):
                logger.info('Going to use stamina in rogue')
                do_rogue = True
            elif self.config.cross_get('Rogue.RogueWorld.DoubleEvent') \
                    and self.config.stored.DungeonDouble.rogue > 0:
                logger.info('Going to use stamina in double rogue event')
                do_rogue = True
        final = DungeonList.find(self.config.Dungeon_Name)
        # Planner
        planner = self.planner.get_dungeon()
        if planner is not None:
            final = planner
            self.is_doing_planner = True

        # Use all stamina
        if do_rogue:
            # Use support if prioritize rogue
            if self.require_compulsory_support():
                logger.info('Run dungeon with support once as stamina is rogue prioritized')
                self.dungeon_run(dungeon=final, wave_limit=1)
                self.is_doing_planner = False
            # Store immersifiers
            logger.info('Prioritize stamina for simulated universe, skip dungeon')
            amount = 0
            if not self.config.cross_get('Rogue.RogueWorld.UseStamina') \
                    and self.config.cross_get('Rogue.RogueWorld.DoubleEvent') \
                    and self.config.stored.DungeonDouble.rogue > 0:
                amount = self.config.stored.DungeonDouble.rogue
            stored = self.immersifier_store(max_store=amount)
            self.check_stamina_quest(stored * 40)
            # call rogue task if accumulated to 4
            with self.config.multi_set():
                if self.config.stored.Immersifier.value >= 4:
                    # Schedule behind rogue
                    self.config.task_delay(minute=5)
                    self.config.task_call('Rogue')
                # Scheduler
                self.delay_dungeon_task(KEYWORDS_DUNGEON_LIST.Simulated_Universe_World_1)
                self.config.task_stop()
        else:
            # Combat
            self.dungeon_run(final)
            self.is_doing_planner = False
            # Scheduler
            self.delay_dungeon_task(final)
            self.check_synthesize()
            self.config.task_stop()

    def check_synthesize(self):
        logger.info('Check synthesize')
        synthesize = Synthesize(config=self.config, device=self.device, task=self.config.task.command)
        set_cached_property(synthesize, 'planner', self.planner)
        if synthesize.synthesize_needed():
            synthesize.synthesize_planner()

    def delay_dungeon_task(self, dungeon: DungeonList):
        logger.attr('achieved_daily_quest', self.achieved_daily_quest)
        logger.attr('achieved_weekly_quest', self.achieved_weekly_quest)
        with self.config.multi_set():
            # Check battle pass
            if self.achieved_weekly_quest:
                self.config.task_call('BattlePass')
            # Check daily
            if self.achieved_daily_quest:
                self.config.task_call('DailyQuest')
            else:
                # Check future daily
                if KEYWORDS_DAILY_QUEST.Obtain_victory_in_combat_with_Support_Characters_1_times in self.daily_quests:
                    logger.error("Dungeon ran but support daily haven't been finished yet")
                    self.config.task_call('DailyQuest')

            # Delay tasks
            self.dungeon_stamina_delay(dungeon)
            # call redeem code
            CodeManager(self).check_redeem_code()

    def require_compulsory_support(self) -> bool:
        require = False

        if not self.config.stored.DailyActivity.is_full():
            if KEYWORDS_DAILY_QUEST.Obtain_victory_in_combat_with_Support_Characters_1_times \
                    in self.daily_quests:
                require = True

        logger.attr('called_daily_support', self.called_daily_support)
        if self.called_daily_support:
            require = False

        # Not required, cause any dungeon run will achieve the quest
        logger.attr('DungeonSupport_Use', self.config.DungeonSupport_Use)
        if self.config.DungeonSupport_Use == 'always_use':
            require = False

        logger.attr('Require compulsory support', require)
        return require

    def check_stamina_quest(self, stamina_used: int):
        logger.info(f'Used {stamina_used} stamina')

        if KEYWORDS_BATTLE_PASS_QUEST.Consume_a_total_of_1_Trailblaze_Power_1400_Trailblazer_Power_max in self.weekly_quests:
            logger.info(f'Done Consume_a_total_of_1_Trailblaze_Power_1400_Trailblazer_Power_max stamina {stamina_used}')
            self.config.stored.BattlePassQuestTrailblazePower.add(stamina_used)
            if self.config.stored.BattlePassQuestTrailblazePower.is_full():
                logger.info('Achieved weekly quest Consume_a_total_of_1_Trailblaze_Power_1400_Trailblazer_Power_max')
                self.achieved_weekly_quest = True

        if KEYWORDS_DAILY_QUEST.Consume_120_Trailblaze_Power in self.daily_quests:
            logger.info(f'Done Consume_120_Trailblaze_Power stamina {stamina_used}')
            self.achieved_daily_quest = True

    def sync_config_traiblaze_power(self, set_task):
        # Sync Dungeon.TrailblazePower and Ornament.TrailblazePower
        with self.config.multi_set():
            value = self.config.TrailblazePower_ExtractReservedTrailblazePower
            keys = f'{set_task}.TrailblazePower.ExtractReservedTrailblazePower'
            if self.config.cross_get(keys) != value:
                self.config.cross_set(keys, value)
            value = self.config.TrailblazePower_UseFuel
            keys = f'{set_task}.TrailblazePower.UseFuel'
            if self.config.cross_get(keys) != value:
                self.config.cross_set(keys, value)
            value = self.config.TrailblazePower_FuelReserve
            keys = f'{set_task}.TrailblazePower.FuelReserve'
            if self.config.cross_get(keys) != value:
                self.config.cross_set(keys, value)
