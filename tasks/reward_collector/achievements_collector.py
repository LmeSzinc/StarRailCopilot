import time

from module.base.timer import Timer
from module.device.method import maatouch
from module.logger import logger
from module.base.button import ClickButton
# from tasks.base.assets.assets_base_daemon import * # Likely not needed if not a DaemonBase
from tasks.base.page import page_main 
from tasks.base.assets.assets_base_page import MAIN_GOTO_MENU
from .assets.assets_achievements_collector import ACHIEVEMENT_ACHIEVED_BUTTON, CLAIM_BUTTON # Updated import
from tasks.map.interact.aim import AimDetectorMixin
from tasks.map.minimap.radar import RadarMixin
# from tasks.base.main_page import MainPage # Import if ui_ensure is used here


class AchievementsCollector(RadarMixin, AimDetectorMixin):
    aim_interval = Timer(0.3, count=1)

    def __init__(self, device, config):
        self.device = device
        self.config = config
        # Call super for mixins if they have __init__ and require it
        # RadarMixin.__init__(self)
        # AimDetectorMixin.__init__(self)
        # If you use self.appear directly from a base class like ModuleBase or similar, ensure it's inherited.
        # If not, you might need to instantiate or inherit from a class that provides `appear`.
        # For now, assuming `appear` is available through one of the mixins or a base class not shown.


    def _click_coord_and_attempt_claim(self, main_coord):
        time.sleep(2)
        coord_button_to_click = ClickButton(area=(main_coord[0], main_coord[1], main_coord[0], main_coord[1]), name=f"COORD_CLICK_{main_coord[0]}_{main_coord[1]}")
        self.device.click(coord_button_to_click)
        logger.info(f"Clicked {main_coord} to check for claims.")
        claimed_at_least_once_here = False
        time.sleep(1)

        while True:
            self.device.screenshot()
            # Assuming self.appear is available. If it comes from a base class of RewardCollector,
            # AchievementsCollector might need to inherit from that base or have it passed.
            if self.appear(CLAIM_BUTTON, similarity=0.80, interval=0):
                logger.info(f"CLAIM_BUTTON found near {main_coord}. Attempting click.")
                claim_click_result = self.device.click(CLAIM_BUTTON)

                if claim_click_result is not False:
                    time.sleep(1)
                    
                    fixed_coord_x, fixed_coord_y = 1165, 240
                    fixed_coord_button = ClickButton(area=(fixed_coord_x, fixed_coord_y, fixed_coord_x, fixed_coord_y), name=f"FIXED_COORD_CLICK_{fixed_coord_x}_{fixed_coord_y}")
                    self.device.click(fixed_coord_button)
                    logger.info(f"Clicked fixed coordinates ({fixed_coord_x}, {fixed_coord_y}).")

                    time.sleep(1)
                    middle_x, middle_y = 640, 360
                    middle_button = ClickButton(area=(middle_x, middle_y, middle_x, middle_y), name="MIDDLE_SCREEN_CLICK_AFTER_FIXED")
                    self.device.click(middle_button)
                    logger.info(f"Clicked middle of screen ({middle_x}, {middle_y}).")
                    
                    claimed_at_least_once_here = True
                else:
                    logger.warning(f"CLAIM_BUTTON appeared, but click attempt failed for {main_coord}.")
                    break
            else:
                logger.info(f"CLAIM_BUTTON not found near {main_coord}. Stopping claims here.")
                break
        
        return claimed_at_least_once_here

    def run_achievements(self):
        # Config binding and ui_ensure should ideally be handled by the main RewardCollector
        # or passed in a way that this class can use them if necessary.

        logger.info("Starting achievement collection...")
        # self.ui_ensure(page_main) # Ensure this is called appropriately if needed

        self.device.click(MAIN_GOTO_MENU)
        logger.info("Clicked MAIN_GOTO_MENU for achievements.")
        time.sleep(3)
        self.device.screenshot()

        achieved_button_interaction_success = False
        logger.info("Checking for ACHIEVEMENT_ACHIEVED_BUTTON...")
        if self.appear(ACHIEVEMENT_ACHIEVED_BUTTON, similarity=0.85, interval=0):
            logger.info("ACHIEVEMENT_ACHIEVED_BUTTON found. Attempting to click.")
            click_result = self.device.click(ACHIEVEMENT_ACHIEVED_BUTTON)
            if click_result is not False:
                logger.info("ACHIEVEMENT_ACHIEVED_BUTTON interaction successful.")
                achieved_button_interaction_success = True
            else:
                logger.info("ACHIEVEMENT_ACHIEVED_BUTTON found, but click attempt failed.")
        else:
            logger.info("ACHIEVEMENT_ACHIEVED_BUTTON not found.")

        if achieved_button_interaction_success:
            logger.info("Proceeding with achievement collection steps...")
            
            coord_x, coord_y = 631, 312 # Initial click into the achievement type area
            time.sleep(3)
            coord_button = ClickButton(area=(coord_x, coord_y, coord_x, coord_y), name=f"COORD_CLICK_{coord_x}_{coord_y}")
            self.device.click(coord_button)
            time.sleep(2)

            scroll_count = 2
            logger.info(f"Scrolling up {scroll_count} times to reach the top of achievements list.")
            p_start_scroll = (46, 150) # Scroll area coordinates
            p_end_scroll = (46, 550)
            for i in range(scroll_count):
                self.device.swipe(p_start_scroll, p_end_scroll, duration=(0.2, 0.4), name='SWIPE_DOWN_TO_SCROLL_UP_X46')
                logger.info(f"Scroll up iteration {i+1}/{scroll_count}")
                time.sleep(0.3)
            logger.info("Finished scrolling up.")
     
            logger.info("Starting sequence to click coordinates and claim rewards in achievements.")

            coords_set1 = [
                (58, 163), (58, 255), (58, 344),
                (58, 433), (58, 526), (58, 616)
            ]
            # Coordinates for the second set, after scrolling if no claims were made in the first pass
            coords_set2 = [(58, 403), (58, 489), (58, 587)] 

            any_claim_made_in_first_set = False
            logger.info("Processing first set of achievement coordinates...")
            for coord in coords_set1:
                if self._click_coord_and_attempt_claim(coord):
                    any_claim_made_in_first_set = True
            
            if not any_claim_made_in_first_set:
                logger.info("No claims in first set of achievements. Scrolling down twice.")
                p_start_scroll_down = (46, 550) # Scroll area coordinates for scrolling down
                p_end_scroll_down = (46, 150)
                for _ in range(2): # Scroll down a couple of times
                    self.device.swipe(p_start_scroll_down, p_end_scroll_down, duration=(0.2, 0.4), name='SWIPE_UP_TO_SCROLL_DOWN_X46')
                    time.sleep(0.3)
                logger.info("Finished scrolling down in achievements.")

                logger.info("Processing second set of achievement coordinates after scroll down...")
                for coord in coords_set2:
                    self._click_coord_and_attempt_claim(coord) # Attempt to claim from the new set of coordinates
            else:
                logger.info("Claims made in first set of achievements. Skipping scroll down and second set.")
            
            logger.info("Exiting achievement section...")
            self.device.adb_shell(['input', 'keyevent', '111']) # Press Escape key
            time.sleep(2)

            self.device.adb_shell(['input', 'keyevent', '111']) # Press Escape key again to ensure exit to menu
            time.sleep(2)
            
            logger.info("Finished achievement collection steps.")
        else:
            logger.info("ACHIEVEMENT_ACHIEVED_BUTTON not found or not effectively clicked. No achievement collection actions performed.")
        
        logger.info("AchievementsCollector task run complete.")
        # self.ui_ensure(page_main) # This should be handled by the main RewardCollector after all tasks