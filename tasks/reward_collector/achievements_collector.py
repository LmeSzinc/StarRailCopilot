import time
from module.base.timer import Timer
from module.device.method import maatouch
from module.logger import logger
from module.base.button import ClickButton
from tasks.base.page import page_main 
from tasks.base.assets.assets_base_page import MAIN_GOTO_MENU
from .assets.assets_reward_collector_Achievement import Achieved, Claim, Achieved_Click
from tasks.map.interact.aim import AimDetectorMixin
from tasks.map.minimap.radar import RadarMixin

class AchievementsCollector(RadarMixin, AimDetectorMixin):
    aim_interval = Timer(0.3, count=1)

    def __init__(self, device, config):
        self.device = device
        self.config = config

    def _click_coord_and_attempt_claim(self, main_coord):
        coord_button_to_click = ClickButton(area=(main_coord[0], main_coord[1], main_coord[0], main_coord[1]), name=f"COORD_CLICK_{main_coord[0]}_{main_coord[1]}")
        self.device.click(coord_button_to_click)
        logger.info(f"Checking achievement coordinate: {main_coord}")

        while True:
            self.device.screenshot()

            if self.appear(Claim, similarity=0.80, interval=0):
                logger.info(f"Claim button found near {main_coord}, attempting click.")
                claim_click_result = self.device.click(Claim)

                if claim_click_result is not False:              
                    fixed_coord_x, fixed_coord_y = 1165, 240
                    fixed_coord_button = ClickButton(area=(fixed_coord_x, fixed_coord_y, fixed_coord_x, fixed_coord_y), name=f"FIXED_COORD_CLICK_{fixed_coord_x}_{fixed_coord_y}")
                    logger.info(f"Clicking fixed coordinate ({fixed_coord_x}, {fixed_coord_y}).")
                    self.device.click(fixed_coord_button)

                    middle_x, middle_y = 640, 360
                    middle_button = ClickButton(area=(middle_x, middle_y, middle_x, middle_y), name="MIDDLE_SCREEN_CLICK_AFTER_FIXED")
                    logger.info(f"Clicking middle of screen ({middle_x}, {middle_y}).")
                    self.device.click(middle_button)
                
                else:
                    logger.warning(f"Claim button click failed for coordinate {main_coord}.")
                    break
            else:
                logger.info(f"No Claim button found near {main_coord}.")
                break
        
    def run_achievements(self):
        logger.info("Starting Achievement reward collection...")

        logger.info("Clicking main menu button for achievements access.")
        self.device.click(MAIN_GOTO_MENU)

        achieved_button_interaction_success = False

        achieved_timeout = Timer(5, count=20)
        achieved_timeout.start()

        while not achieved_timeout.reached():
            self.device.screenshot()

            appear_result = self.appear(Achieved, similarity=0.80, interval=0)

            if appear_result is True: 
                logger.info("Achieved button found, attempting click.")
                self.device.click(Achieved)
                achieved_button_interaction_success = True
                break

        if achieved_button_interaction_success:
            logger.info("Achieved button clicked successfully, proceeding to collection.")
            
            clicked_achieved_click = False

            achieved_click_timeout = Timer(5, count=20)
            achieved_click_timeout.start()

            while not achieved_click_timeout.reached():
                self.device.screenshot()

                appear_result = self.appear(Achieved_Click, similarity=0.80, interval=0)

                if appear_result is True:
                    logger.info("Achieved_Click button found, attempting click.")
                    self.device.click(Achieved_Click)
                    clicked_achieved_click = True
                    break 

            if not clicked_achieved_click:
                logger.info("Achieved_Click button not found within timeout period.")
                logger.info("Achievement Collector task complete.")
                return
            else:
                scroll_count = 2
                logger.info(f"Scrolling up {scroll_count} times to reach top of achievements list.")
                p_start_scroll = (46, 150)
                p_end_scroll = (46, 550)
                for i in range(scroll_count):
                    self.device.swipe(p_start_scroll, p_end_scroll, duration=(0.2, 0.4), name='SWIPE_DOWN_TO_SCROLL_UP_X46')
                    logger.info(f"Scroll {i+1}/{scroll_count} complete")

                logger.info("Starting Achievement reward collection sequence.")

                coords_set1 = [
                    (58, 163), (58, 255), (58, 344),
                    (58, 433), (58, 526), (58, 616)
                ]

                coords_set2 = [(58, 403), (58, 489), (58, 587)] 

                any_claim_made_in_first_set = False
                logger.info(f"Processing first set of {len(coords_set1)} achievement coordinates...")
                for coord in coords_set1:
                    if self._click_coord_and_attempt_claim(coord):
                        any_claim_made_in_first_set = True
                
                if not any_claim_made_in_first_set:
                    logger.info("No rewards claimed in first set, scrolling down to check second set.")
                    p_start_scroll_down = (46, 550)
                    p_end_scroll_down = (46, 150)
                    for i in range(2):
                        self.device.swipe(p_start_scroll_down, p_end_scroll_down, duration=(0.2, 0.4), name='SWIPE_UP_TO_SCROLL_DOWN_X46')
                        logger.info(f"Scroll down {i+1}/2 complete")

                    logger.info(f"Processing second set of {len(coords_set2)} achievement coordinates...")
                    for coord in coords_set2:
                        self._click_coord_and_attempt_claim(coord)
                else:
                    logger.info("Rewards claimed in first set, skipping second set.")
                
                logger.info("Achievement collection complete, returning to main page.")

                time.sleep(2)
                self.device.adb_shell(['input', 'keyevent', '111'])

                time.sleep(2)   
                self.device.adb_shell(['input', 'keyevent', '111'])
                
                logger.info("Achievement Collector task complete.")
                return
        else:
            logger.info("Achieved button not found or no achievements to collect.")
            logger.info("Achievement Collector task complete.")
            return