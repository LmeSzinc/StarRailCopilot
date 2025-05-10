from module.base.decorator import run_once
from module.exception import RequestHumanTakeover
from module.logger import logger
from tasks.base.page import page_guide
from tasks.combat.assets.assets_combat_finish import COMBAT_AGAIN, COMBAT_EXIT
from tasks.combat.assets.assets_combat_interact import DUNGEON_COMBAT_INTERACT
from tasks.combat.assets.assets_combat_prepare import COMBAT_PREPARE
from tasks.combat.assets.assets_combat_team import COMBAT_TEAM_PREPARE, COMBAT_TEAM_SUPPORT
from tasks.combat.fuel import Fuel
from tasks.combat.interact import CombatInteract
from tasks.combat.obtain import CombatObtain
from tasks.combat.prepare import CombatPrepare
from tasks.combat.skill import CombatSkill
from tasks.combat.support import CombatSupport
from tasks.combat.team import CombatTeam
from tasks.dungeon.keywords import DungeonList
from tasks.map.control.joystick import MapControlJoystick


class Combat(CombatInteract, CombatPrepare, CombatSupport, CombatTeam, CombatSkill, CombatObtain,
             MapControlJoystick, Fuel):
    dungeon: DungeonList | None = None
    is_doing_planner: bool = False

    def handle_combat_prepare(self):
        """
        Returns:
            bool: If able to run a combat

        Pages:
            in: COMBAT_PREPARE
        """
        self.combat_waves = 1
        cost = self.combat_get_wave_cost()
        current = self.combat_get_trailblaze_power()

        # Try to get more stamina
        if cost == 10:
            # To a calyx, always try to redeem 60 stamina first
            if current < cost * 6:
                self._try_get_more_trablaize_power(cost * 6)
                current = self.config.stored.TrailblazePower.value
                # Still not enough to do 1 wave after redeem, exit combat
                if current < cost:
                    logger.info(f'Current has {current}, combat costs {cost}, can not run again')
                    return False
                # Not enough to do 6 waves but able to do some waves,
                # continue as it is, self.combat_waves will be set
                elif current < cost * 6:
                    logger.info('Not enough stamina to do 6 waves')
                # Enough stamina, all good
                else:
                    logger.info('Having enough stamina to do 6 waves after redeem')
        else:
            # To other dungeon, try to get its cost
            if current < cost:
                if self._try_get_more_trablaize_power(cost):
                    current = self.config.stored.TrailblazePower.value
                else:
                    return False

        if cost == 10:
            # Calyx
            self.combat_waves = min(current // cost, 6)
            if self.combat_wave_limit:
                self.combat_waves = min(self.combat_waves, self.combat_wave_limit - self.combat_wave_done)
                logger.info(
                    f'Current has {current}, combat costs {cost}, '
                    f'wave={self.combat_wave_done}/{self.combat_wave_limit}, '
                    f'able to do {self.combat_waves} waves')
            else:
                logger.info(f'Current has {current}, combat costs {cost}, '
                            f'able to do {self.combat_waves} waves')
            if self.combat_waves > 0:
                self.combat_set_wave(self.combat_waves)
        else:
            # Others
            logger.info(f'Current has {current}, combat costs {cost}, '
                        f'do {self.combat_waves} wave')

        # Check limits
        if self.config.stored.TrailblazePower.value < cost:
            return self._try_get_more_trablaize_power(cost)
        if self.combat_waves <= 0:
            logger.info('Combat wave limited, cannot continue combat')
            return False

        return True

    def handle_ascension_dungeon_prepare(self):
        """
        Returns:
            bool: If clicked.
        """
        if self.combat_wave_cost == 30 and self.is_in_main():
            if self.handle_map_A():
                return True

        return False

    def combat_prepare(self, team=1, support_character: str = None):
        """
        Args:
            team: 1 to 6.
            support_character: Support character name

        Returns:
            bool: True if success to enter combat
                False if trialblaze power is not enough

        Pages:
            in: COMBAT_PREPARE
            out: is_combat_executing
        """
        logger.hr('Combat prepare')
        skip_first_screenshot = True
        if support_character:
            # Block COMBAT_TEAM_PREPARE before support set
            support_set = False
        else:
            support_set = True
        logger.info([support_character, support_set])
        combat_trial = 0
        team_trial = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_combat_executing():
                return True
            # Relics full
            # Clicking between COMBAT_PREPARE and COMBAT_TEAM_PREPARE
            if combat_trial > 3:
                logger.critical('Failed to enter dungeon after 3 trial, probably because relics are full')
                raise RequestHumanTakeover
            if team_trial > 3:
                logger.critical('Failed to enter dungeon after 3 trial, probably because relics are full')
                raise RequestHumanTakeover

            # Click
            if support_character and self.appear(COMBAT_TEAM_SUPPORT, interval=2):
                self.team_set(team)
                self.support_set(support_character)
                self.interval_reset(COMBAT_TEAM_SUPPORT)
                support_set = True
                continue
            if support_set and self.appear(COMBAT_TEAM_PREPARE, interval=2):
                self.team_set(team)
                self.device.click(COMBAT_TEAM_PREPARE)
                self.interval_reset(COMBAT_TEAM_PREPARE)
                self.interval_reset(COMBAT_TEAM_SUPPORT)
                team_trial += 1
                continue
            if self.appear(COMBAT_TEAM_PREPARE):
                self.interval_reset(COMBAT_PREPARE)
                self.map_A_timer.reset()
            if self.appear(COMBAT_PREPARE, interval=2):
                if self.is_doing_planner and self.obtained_is_full(self.dungeon, wave_done=self.combat_wave_done):
                    # Update stamina so task can be delayed if both obtained_is_full and stamina exhausted
                    self.combat_get_trailblaze_power()
                    return False
                if not self.handle_combat_prepare():
                    return False
                if self.is_doing_planner and self.combat_wave_cost == 0:
                    logger.info('Free combat gets nothing cannot meet planner needs')
                    return False
                self.device.click(COMBAT_PREPARE)
                self.interval_reset(COMBAT_PREPARE)
                combat_trial += 1
                continue
            if self.appear(DUNGEON_COMBAT_INTERACT):
                if self.handle_combat_interact():
                    self.map_A_timer.reset()
                    continue
            else:
                if self.handle_ascension_dungeon_prepare():
                    continue
            if self.handle_popup_confirm():
                continue

    def combat_execute(self, expected_end=None):
        """
        Args:
            expected_end: A function returns bool, True represents end.

        Pages:
            in: is_combat_executing
            out: COMBAT_AGAIN
        """
        logger.hr('Combat execute')
        skip_first_screenshot = True
        is_executing = True
        self.combat_state_reset()
        self.device.stuck_record_clear()
        self.device.click_record_clear()
        self.device.screenshot_interval_set('combat')
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if callable(expected_end) and expected_end():
                logger.info(f'Combat execute ended at {expected_end.__name__}')
                break
            if (self.appear(COMBAT_AGAIN) and
                    self.image_color_count(COMBAT_AGAIN, color=(227, 227, 228), threshold=221, count=50)):
                logger.info(f'Combat execute ended at {COMBAT_AGAIN}')
                break
            if self.is_in_main():
                logger.info(f'Combat execute ended at page_main')
                break

            # Daemon
            if self.is_combat_executing():
                if not is_executing:
                    logger.info('Combat continues')
                    self.device.stuck_record_clear()
                is_executing = True
            else:
                is_executing = False
            if self.handle_combat_state():
                continue
            # Battle pass popup appears just after combat finished and before blessings
            if self.handle_battle_pass_notification():
                continue

        self.device.stuck_record_clear()
        self.device.click_record_clear()
        self.device.screenshot_interval_set()

    def _combat_can_again(self) -> bool:
        """
        Pages:
            in: COMBAT_AGAIN
        """
        current = self.combat_get_trailblaze_power(expect_reduce=self.combat_wave_cost > 0)
        # Planner
        logger.attr('obtain_frequent_check', self.obtain_frequent_check)
        if self.obtain_frequent_check:
            logger.info('Exit combat to check obtained items')
            return False
        # Wave limit
        if self.combat_wave_limit:
            if self.combat_wave_done + self.combat_waves > self.combat_wave_limit:
                logger.info(f'Combat wave limit: {self.combat_wave_done}/{self.combat_wave_limit}, '
                            f'can not run again')
                return False
        # Cost limit
        if self.combat_wave_cost == 10:
            if current >= self.combat_wave_cost * self.combat_waves:
                logger.info(f'Current has {current}, combat costs {self.combat_wave_cost}, can run again')
                return True
            else:
                return self._try_get_more_trablaize_power(self.combat_wave_cost * self.combat_waves)
        elif self.combat_wave_cost <= 0:
            logger.info(f'Free combat, combat costs {self.combat_wave_cost}, can not run again')
            return False
        else:
            if current >= self.combat_wave_cost:
                logger.info(f'Current has {current}, combat costs {self.combat_wave_cost}, can run again')
                return True
            else:
                return self._try_get_more_trablaize_power(self.combat_wave_cost * self.combat_waves)

    def _try_get_more_trablaize_power(self, cost):
        self.extract_stamina(
            update=False,
            use_reserved=self.config.TrailblazePower_ExtractReservedTrailblazePower,
            use_fuel=self.config.TrailblazePower_UseFuel
        )
        current = self.config.stored.TrailblazePower.value
        if current >= cost:
            return True
        else:
            logger.info(f'Current has {current}, combat costs {self.combat_wave_cost}, can not run again')
            return False

    def _combat_should_reenter(self):
        """
        Returns:
            bool: True to re-enter combat and run with another wave settings
        """
        # Planner
        logger.attr('obtain_frequent_check', self.obtain_frequent_check)
        if self.obtain_frequent_check:
            if self.config.stored.TrailblazePower.value >= self.combat_wave_cost \
                    and (self.combat_wave_limit and self.combat_wave_done < self.combat_wave_limit):
                logger.info(f'Still having some trailblaze power '
                            f'but wave limit not reached {self.combat_wave_done}/{self.combat_wave_limit}, '
                            f'ignore obtain_frequent_check cause will reenter later')
                return False
            else:
                logger.info('Re-enter combat to check obtained items')
                return True
        # Stamina
        if self.config.stored.TrailblazePower.value < self.combat_wave_cost:
            if self.is_doing_planner:
                logger.info('Current trailblaze power is not enough for next run, '
                            're-enter combat to check obtained items')
                return True
            else:
                logger.info('Current trailblaze power is not enough for next run')
                return False
        # Wave limit
        if self.combat_wave_limit:
            if self.combat_wave_done < self.combat_wave_limit:
                logger.info(f'Combat wave limit: {self.combat_wave_done}/{self.combat_wave_limit}, '
                            f'run again with less waves')
                return True
            else:
                return False
        # Cost limit
        if self.config.stored.TrailblazePower.value >= self.combat_wave_cost:
            logger.info('Still having some trailblaze power run with less waves to empty it')
            return True
        return False

    def combat_finish(self) -> bool:
        """
        Returns:
            bool: True if exit, False if again

        Pages:
            in: COMBAT_AGAIN
            out: page_main if exit
                is_combat_executing if again
        """
        logger.hr('Combat finish')

        @run_once
        def add_wave_done():
            self.combat_wave_done += self.combat_waves
            logger.info(f'Done {self.combat_waves} waves at total')

        skip_first_screenshot = True
        combat_can_again = None
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_in_main():
                logger.info('Combat finishes at page_main')
                return True
            if self.appear(COMBAT_PREPARE):
                logger.info('Combat finishes at COMBAT_PREPARE')
                return True
            if self.is_combat_executing():
                logger.info('Combat finishes at another combat')
                return False

            # Click
            # Game client might slow to response COMBAT_AGAIN clicks
            if self.appear(COMBAT_AGAIN, interval=5):
                add_wave_done()
                # Update obtain_frequent_check
                if self.is_doing_planner:
                    self.obtained_is_full(dungeon=self.dungeon, wave_done=self.combat_wave_done, obtain_get=False)
                    # Check obtained every 30 waves to reduce drop predict error
                    if self.combat_waves == 6 and self.combat_wave_done % 30 == 0:
                        logger.info(f'Check obtained at wave {self.combat_wave_done}')
                        self.obtain_frequent_check = True
                # Cache the result of _combat_can_again() as no expected stamina reduce during retry
                if combat_can_again is None:
                    combat_can_again = self._combat_can_again()
                if combat_can_again:
                    self.device.click(COMBAT_AGAIN)
                else:
                    self.device.click(COMBAT_EXIT)
                self.interval_reset(COMBAT_AGAIN)
                continue
            # Dropped light cone from weekly
            if self.handle_get_light_cone():
                continue
            # Having any character died
            if self.handle_popup_confirm():
                continue

    def combat_exit(self, skip_first_screenshot=True):
        """
        Pages:
            in: Any page during combat
            out: page_main
        """
        logger.info('Combat exit')
        self.interval_clear([COMBAT_PREPARE, COMBAT_TEAM_PREPARE, COMBAT_AGAIN])
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.device.screenshot()

            # End
            if self.is_in_main():
                break

            # Click
            if self.handle_ui_close(COMBAT_PREPARE, interval=2):
                continue
            if self.handle_ui_close(COMBAT_TEAM_PREPARE, interval=2):
                continue
            if self.appear(COMBAT_AGAIN, interval=2):
                logger.info(f'{COMBAT_AGAIN} -> {COMBAT_EXIT}')
                self.device.click(COMBAT_EXIT)
                continue
            if self.handle_get_light_cone():
                continue
            if self.handle_ui_close(page_guide.check_button, interval=5):
                continue

    def combat(self, team: int = 1, wave_limit: int = 0, support_character: str = None, skip_first_screenshot=True):
        """
        Combat until trailblaze power runs out.

        Args:
            team: 1 to 6.
            wave_limit: Limit combat runs, 0 means no limit.
            support_character: Support character name
            skip_first_screenshot:

        Returns:
            int: Run count

        Raises:
            RequestHumanTakeover: If relics are full

        Pages:
            in: COMBAT_PREPARE
                or page_main with DUNGEON_COMBAT_INTERACT
            out: page_main
                or COMBAT_PREPARE
        """
        if not skip_first_screenshot:
            self.device.screenshot()

        self.combat_wave_limit = wave_limit
        self.combat_wave_done = 0
        while 1:
            logger.hr('Combat', level=2)
            logger.info(f'Combat, team={team}, wave={self.combat_wave_done}/{self.combat_wave_limit}')
            # Prepare
            prepare = self.combat_prepare(team, support_character)
            if not prepare:
                self.combat_exit()
                break
            # Execute
            self.combat_execute()
            # Finish
            finish = self.combat_finish()
            if self._combat_should_reenter():
                continue
            if finish:
                break
            # Reset combat_wave_cost, so handle_combat_interact() won't activate before handle_combat_prepare()
            self.combat_wave_cost = 10

        logger.attr('combat_wave_done', self.combat_wave_done)
        return self.combat_wave_done
