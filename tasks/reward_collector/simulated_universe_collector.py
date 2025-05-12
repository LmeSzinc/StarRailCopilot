import time
# import os # No longer needed directly here
# from datetime import datetime # No longer needed directly here
# from PIL import Image # No longer needed directly here

from module.logger import logger
from tasks.dungeon.ui.ui_rogue import DungeonRogueUI
from tasks.reward_collector.assets.assets_index_collector import (
    IndexMark, BlessingsMark, BlessingNextMark, BlessingClaim,
    OccurrenceMark, OccurrenceClaim, CurioMark, CurioClaim
)
from tasks.base.page import page_main
from .debug_utils import DebugHelper

class SimulatedUniverseCollector(DungeonRogueUI):
    # _SCREENSHOT_DIR removed

    def __init__(self, device, config):
        # super().__init__(...) removed
        self.device = device  # Explicitly set device
        self.config = config  # Explicitly set config
        # WARNING: self.appear might not work correctly as super().__init__ (which sets up ButtonManager) is not called.
        self.debug_helper = DebugHelper(self.device, self.appear)

    # Removed _ensure_screenshot_dir_exists
    # Removed capture_and_save_debug_screenshot
    # Removed _debug_match_tester

    def _collect_blessings_index(self):
        logger.info("Attempting to collect Blessings Index rewards...")
        self.device.screenshot()
        if self.appear(BlessingsMark, interval=0):
            logger.info("BlessingsMark found. Clicking it.")
            self.device.click(BlessingsMark)
            time.sleep(1.5)
            self.debug_helper.capture_and_save_debug_screenshot("su_blessings_index_entered")

            claimed_in_blessings = False
            for _ in range(10):
                self.device.screenshot()
                action_taken_this_screen = False
                if self.appear(BlessingClaim, interval=0):
                    logger.info("BlessingClaim found. Clicking.")
                    self.device.click(BlessingClaim)
                    claimed_in_blessings = True
                    action_taken_this_screen = True
                    time.sleep(1.5)
                    self.debug_helper.capture_and_save_debug_screenshot("su_blessing_claimed")
                
                self.device.screenshot()
                if self.appear(BlessingNextMark, interval=0):
                    logger.info("BlessingNextMark found. Clicking to next page.")
                    self.device.click(BlessingNextMark)
                    action_taken_this_screen = True
                    time.sleep(1.5)
                    self.debug_helper.capture_and_save_debug_screenshot("su_blessing_next_page")
                elif not action_taken_this_screen and not self.appear(BlessingClaim, interval=0, static=False): 
                    logger.info("No more claims or next pages for Blessings found on this screen.")
                    break 
                elif not self.appear(BlessingClaim, interval=0, static=False) and not self.appear(BlessingNextMark, interval=0, static=False):
                    logger.info("Neither BlessingClaim nor BlessingNextMark found. Exiting blessings loop.")
                    break
            
            logger.info("Exiting Blessings Index section (going back from blessings list).")
            self.device.adb_shell(['input', 'keyevent', '111'])
            time.sleep(1)
            self.debug_helper.capture_and_save_debug_screenshot("su_blessings_index_exited_to_main_index")
            return claimed_in_blessings
        else:
            logger.info("BlessingsMark not found. Skipping Blessings Index.")
            return False

    def _collect_occurrences_index(self):
        logger.info("Attempting to collect Occurrences Index rewards...")
        self.device.screenshot()
        if self.appear(OccurrenceMark, interval=0):
            logger.info("OccurrenceMark found. Clicking it.")
            self.device.click(OccurrenceMark)
            time.sleep(1.5)
            self.debug_helper.capture_and_save_debug_screenshot("su_occurrences_index_entered")
            claimed_in_occurrences = False
            for _ in range(10):
                self.device.screenshot()
                if self.appear(OccurrenceClaim, interval=0):
                    logger.info("OccurrenceClaim found. Clicking.")
                    self.device.click(OccurrenceClaim)
                    claimed_in_occurrences = True
                    time.sleep(1.5)
                    self.debug_helper.capture_and_save_debug_screenshot("su_occurrence_claimed")
                else:
                    logger.info("No more OccurrenceClaims found.")
                    break
            logger.info("Exiting Occurrences Index section (going back from occurrences list).")
            self.device.adb_shell(['input', 'keyevent', '111'])
            time.sleep(1)
            self.debug_helper.capture_and_save_debug_screenshot("su_occurrences_index_exited_to_main_index")
            return claimed_in_occurrences
        else:
            logger.info("OccurrenceMark not found. Skipping Occurrences Index.")
            return False

    def _collect_curios_index(self):
        logger.info("Attempting to collect Curios Index rewards...")
        self.device.screenshot()
        if self.appear(CurioMark, interval=0):
            logger.info("CurioMark found. Clicking it.")
            self.device.click(CurioMark)
            time.sleep(1.5)
            self.debug_helper.capture_and_save_debug_screenshot("su_curios_index_entered")
            claimed_in_curios = False
            for _ in range(10):
                self.device.screenshot()
                if self.appear(CurioClaim, interval=0):
                    logger.info("CurioClaim found. Clicking.")
                    self.device.click(CurioClaim)
                    claimed_in_curios = True
                    time.sleep(1.5)
                    self.debug_helper.capture_and_save_debug_screenshot("su_curio_claimed")
                else:
                    logger.info("No more CurioClaims found.")
                    break
            logger.info("Exiting Curios Index section (going back from curios list).")
            self.device.adb_shell(['input', 'keyevent', '111'])
            time.sleep(1)
            self.debug_helper.capture_and_save_debug_screenshot("su_curios_index_exited_to_main_index")
            return claimed_in_curios
        else:
            logger.info("CurioMark not found. Skipping Curios Index.")
            return False

    def run_simulated_universe(self):
        #test here
                # here add image tester 
        self.debug_helper.debug_match_tester(IndexMark)


        time.sleep(999999999)

        # Small upward swipe to scroll content down slightly
        try:
            center_x = self.device.width // 2
            center_y = self.device.height // 2
            swipe_distance = int(self.device.height * 0.05) # 5% of screen height

            start_y_swipe = center_y + swipe_distance // 2
            end_y_swipe = center_y - swipe_distance // 2

            # Ensure coordinates are within screen bounds (0 to height-1 or width-1)
            start_y_swipe = max(0, min(start_y_swipe, self.device.height - 1))
            end_y_swipe = max(0, min(end_y_swipe, self.device.height - 1))
            
            # Ensure there's an actual swipe to perform (start_y != end_y)
            if start_y_swipe > end_y_swipe: 
                start_point = (center_x, start_y_swipe)
                end_point = (center_x, end_y_swipe)
                logger.info(f"Performing a small upward swipe (scrolls content down): from {start_point} to {end_point}")
                self.device.swipe(start_point, end_point, duration=(0.1, 0.2), name='SMALL_UPWARD_SWIPE')
                time.sleep(0.5) # Small pause after swipe
            else:
                logger.info("Skipping small swipe, calculated distance is zero or negative.")
        except AttributeError as e:
            logger.error(f"Could not perform small swipe due to AttributeError (device.width/height missing?): {e}")
        except Exception as e:
            logger.error(f"Error during small swipe: {e}")
        #endtest here
        logger.info("Starting Simulated Universe INDEX reward collection...")
        self.debug_helper.capture_and_save_debug_screenshot("su_index_collection_init")
        
        self.device.screenshot()
        self.debug_helper.debug_match_tester(IndexMark) 
        self.debug_helper.debug_match_tester(BlessingsMark, start_sim=0.60, end_sim=0.95, step=0.05)
        self.debug_helper.debug_match_tester(BlessingClaim, start_sim=0.70)

        self.ui_ensure(page_main)
        self.debug_helper.capture_and_save_debug_screenshot("su_index_nav_ensured_main_page")
        
        logger.info("Navigating to Simulated Universe section for Index Collection...")
        self.dungeon_goto_rogue()
        self.debug_helper.capture_and_save_debug_screenshot("su_after_dungeon_goto_rogue_for_index")
        time.sleep(1.5)

        self.device.screenshot()
        if self.appear(IndexMark, interval=0):
            logger.info("IndexMark (entry to SU Index) found. Clicking it.")
            self.device.click(IndexMark)
            time.sleep(2)
            self.debug_helper.capture_and_save_debug_screenshot("su_index_section_entered")

            self._collect_blessings_index()
            time.sleep(0.5) 
            
            self._collect_occurrences_index()
            time.sleep(0.5)
            
            self._collect_curios_index()
            
            logger.info("Finished all SU index collection attempts. Exiting main Index section.")
            self.device.adb_shell(['input', 'keyevent', '111'])
            time.sleep(1)
            self.debug_helper.capture_and_save_debug_screenshot("su_exited_main_index_to_su_page")
        else:
            logger.warning("IndexMark (entry to SU Index) not found on the SU page. Cannot collect SU Index rewards.")

        logger.info("SU Index collection attempt finished. Returning to main page.")
        self.ui_ensure(page_main)
        self.debug_helper.capture_and_save_debug_screenshot("su_index_collection_end_at_main")
        logger.info("Simulated Universe INDEX reward collection finished.") 