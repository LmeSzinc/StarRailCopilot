import time
from module.logger import logger
from tasks.dungeon.ui.ui_rogue import DungeonRogueUI
from module.base.button import ClickButton
from .assets.assets_reward_collector_Simulated import (
    BlessingClaim2, IndexMark, BlessingMark, BlessingClaim,
    OccurrenceMark, OccurrenceClaim, CurioMark, CurioClaim
)
from tasks.forgotten_hall.assets.assets_forgotten_hall_ui import TELEPORT
from tasks.base.page import page_main
from module.base.timer import Timer

class SimulatedUniverseCollector(DungeonRogueUI):

    def __init__(self, device, config):
        super().__init__(config=config, device=device)

    def _click_blessing_coord_and_attempt_claim(self, coord):
            logger.info(f"Checking blessing coordinate: {coord}")
            coord_button = ClickButton(area=(coord[0], coord[1], coord[0], coord[1]), name=f"BLESSING_COORD_{coord[0]}_{coord[1]}")
            self.device.click(coord_button)

            claim_made = False

            claim_check_timeout = Timer(2)
            claim_check_timeout.start()

            while not claim_check_timeout.reached():
                self.device.screenshot()
                if self.appear(BlessingClaim, similarity=0.80, interval=0):
                    logger.info(f"BlessingClaim found near {coord}, attempting click.")
                    self.device.click(BlessingClaim)
                    logger.info("BlessingClaim clicked successfully.")
                    claim_made = True
                    break
                
            if claim_made is True:
                blessing_claim2_clicked = False

                blessing_claim2_timeout = Timer(5)
                blessing_claim2_timeout.start()

                while not blessing_claim2_timeout.reached():
                    self.device.screenshot()
                    if self.appear(BlessingClaim2, similarity=0.80, interval=0):
                        logger.info("BlessingClaim2 found, attempting click.")
                        self.device.click(BlessingClaim2)
                        time.sleep(2)
                        blessing_claim2_clicked = True
                        middle_x, middle_y = 640, 360
                        middle_button = ClickButton(area=(middle_x, middle_y, middle_x, middle_y), name="MIDDLE_SCREEN_CLICK_AFTER_BLESSING_CLAIM2")
                        logger.info(f"Clicking middle of screen ({middle_x}, {middle_y}) after blessing claim.")
                        self.device.click(middle_button)
                        time.sleep(2)
                        self.device.adb_shell(['input', 'keyevent', '111'])
                        break
                
                if not blessing_claim2_clicked:
                    logger.warning("BlessingClaim2 not found within timeout period.")

            if not claim_made and claim_check_timeout.reached():
                logger.debug(f"No BlessingClaim found near {coord} within timeout period.")

            return claim_made

    def _collect_blessings_index(self):
        logger.info("Starting Blessings Index reward collection...")

        blessing_coords = [
            (79, 124), (175, 124), (271, 124), (367, 124),
            (482, 124), (578, 124), (683, 124), (778, 124)
        ]

        claimed_in_blessings = False
        logger.info(f"Processing {len(blessing_coords)} blessing coordinates...")
        for coord in blessing_coords:
            if self._click_blessing_coord_and_attempt_claim(coord):
                claimed_in_blessings = True

        if claimed_in_blessings:
            logger.info("Blessings collection: At least one reward claimed.")
        else:
            logger.info("Blessings collection: No rewards claimed.")
        
        self.device.adb_shell(['input', 'keyevent', '111'])
        return claimed_in_blessings

    def _click_occurrence_coord_and_attempt_claim(self, coord):
        logger.info(f"Checking occurrence coordinate: {coord}")
        coord_button = ClickButton(area=(coord[0], coord[1], coord[0], coord[1]), name=f"OCCURRENCE_COORD_{coord[0]}_{coord[1]}")
        self.device.click(coord_button)

        claim_successful = False
        claim_check_timeout = Timer(3.0)
        logger.debug(f"Waiting for OccurrenceClaim near {coord}...")
        claim_check_timeout.start()
        while not claim_check_timeout.reached():
            self.device.screenshot()
            if self.appear(OccurrenceClaim, similarity=0.60, interval=0):
                logger.info(f"OccurrenceClaim found near {coord}, attempting click.")
                self.device.click(OccurrenceClaim)
                logger.info("OccurrenceClaim clicked successfully.")
                claim_successful = True
                time.sleep(1)                 
                middle_x, middle_y = 640, 600
                middle_button = ClickButton(area=(middle_x, middle_y, middle_x, middle_y), name="MIDDLE_SCREEN_CLICK_AFTER_OCCURRENCE_CLAIM")
                logger.info(f"Clicking middle of screen ({middle_x}, {middle_y}) after occurrence claim.")
                self.device.click(middle_button)
                time.sleep(1) 
                break
        
        if not claim_successful and claim_check_timeout.reached():
            logger.debug(f"No OccurrenceClaim found near {coord} within timeout period.")
        return claim_successful

    def _collect_occurrences_index(self):
        logger.info("Starting Occurrences Index reward collection...")
        occurrence_coords = [
            (232, 119),
            (232, 209), (232, 297), (232, 372),
            (232, 457), (232, 531), (232, 605)
        ]
        any_claim_made_overall = False

        while True: 
            logger.info("Processing current occurrences screen...")
            claims_made_on_this_screen = False
            for coord in occurrence_coords:
                if self._click_occurrence_coord_and_attempt_claim(coord):
                    claims_made_on_this_screen = True
                    any_claim_made_overall = True
                else:
                    logger.info(f"No OccurrenceClaim found for coordinate {coord}, stopping current screen check.")
                    break

            if not claims_made_on_this_screen:
                logger.info("Occurrences collection: No rewards claimed on current screen.")
                break

            logger.info("Occurrences claimed on current screen, checking for more occurrences...")
            self.device.adb_shell(['input', 'keyevent', '111'])

            logger.info("Attempting to find OccurrenceMark again...")
            re_entered_successfully = False
            occurrence_mark_recheck_timeout = Timer(3.0)
            occurrence_mark_recheck_timeout.start()
            while not occurrence_mark_recheck_timeout.reached():
                self.device.screenshot()
                if self.appear(OccurrenceMark, similarity=0.60, interval=0):
                    logger.info("OccurrenceMark found, re-entering occurrences section.")
                    self.device.click(OccurrenceMark)
                    re_entered_successfully = True
                    break
                    
            if not re_entered_successfully:
                logger.info("OccurrenceMark not found, no more occurrences to process.")
                break
            else:
                logger.info("Successfully re-entered OccurrenceMark, continuing collection...")

        logger.info("Occurrences collection complete, returning to main index.")
        self.device.adb_shell(['input', 'keyevent', '111'])
        time.sleep(1.0)

        if any_claim_made_overall:
            logger.info("Occurrences collection: At least one reward claimed overall.")
        else:
            logger.info("Occurrences collection: No rewards claimed overall.")
        return any_claim_made_overall

    def _click_curio_coord_and_attempt_claim(self, coord):
        logger.info(f"Checking curio coordinate: {coord}")
        coord_button = ClickButton(area=(coord[0], coord[1], coord[0], coord[1]), name=f"CURIO_COORD_{coord[0]}_{coord[1]}")
        self.device.click(coord_button)

        claim_successful = False
        claim_check_timeout = Timer(3.0)
        logger.debug(f"Waiting for CurioClaim near {coord}...")
        claim_check_timeout.start()
        while not claim_check_timeout.reached():
            self.device.screenshot()
            if self.appear(CurioClaim, similarity=0.80, interval=0):
                logger.info(f"CurioClaim found near {coord}, attempting click.")
                self.device.click(CurioClaim)
                logger.info("CurioClaim clicked successfully.")
                claim_successful = True
                time.sleep(1.5)                    
                middle_x, middle_y = 640, 600
                middle_button = ClickButton(area=(middle_x, middle_y, middle_x, middle_y), name="MIDDLE_SCREEN_CLICK_AFTER_CURIO_CLAIM")
                logger.info(f"Clicking middle of screen ({middle_x}, {middle_y}) after curio claim.")
                self.device.click(middle_button)
          
        if not claim_successful and claim_check_timeout.reached():
            logger.debug(f"No CurioClaim found near {coord} within timeout period.")
        return claim_successful

    def _collect_curios_index(self):
        logger.info("Starting Curios Index reward collection...")
        curio_coords = [
            (124, 285), (323, 285), (521, 285), (719, 285)
        ]
        any_claim_made_overall = False

        while True: 
            logger.info("Processing current curios screen...")
            for coord in curio_coords: 
                if self._click_curio_coord_and_attempt_claim(coord):
                    any_claim_made_overall = True
                else:
                    logger.info(f"No CurioClaim found for coordinate {coord} on this screen.")
            
            logger.info("Finished processing current curios screen.")

            logger.info("Going back to SU Index to check for more curio pages...")
            self.device.adb_shell(['input', 'keyevent', '111'])
            time.sleep(1.0)

            logger.info("Attempting to find CurioMark again...")
            re_entered_successfully = False
            curio_mark_recheck_timeout = Timer(3.0)
            curio_mark_recheck_timeout.start()
            while not curio_mark_recheck_timeout.reached():
                self.device.screenshot()
                if self.appear(CurioMark, similarity=0.60, interval=0):
                    logger.info("CurioMark found, re-entering curios section.")
                    self.device.click(CurioMark)
                    time.sleep(1.5)
                    re_entered_successfully = True
                    break
            
            if not re_entered_successfully:
                logger.info("CurioMark not found, no more curio pages to process.")
                break
            else:
                logger.info("Successfully re-entered CurioMark, continuing collection...")

        logger.info("Curios collection complete, returning to main index.")
        self.device.adb_shell(['input', 'keyevent', '111'])
        time.sleep(1.0)

        if any_claim_made_overall:
            logger.info("Curios collection: At least one reward claimed overall.")
        else:
            logger.info("Curios collection: No rewards claimed overall.")
        return any_claim_made_overall

    def run_simulated_universe(self):
        logger.info("Starting Simulated Universe reward collection...")
        
        self.dungeon_goto_rogue() 

        teleport_successful = False

        teleport_timeout = Timer(5, count=20)
        teleport_timeout.start()
        
        while not teleport_timeout.reached():
            self.device.screenshot()

            if self.appear(TELEPORT, similarity=0.80, interval=0):
                logger.info("TELEPORT button found, attempting click.")
                self.device.click(TELEPORT)
                teleport_successful = True
                break 

        if not teleport_successful:
            logger.error("Failed to find TELEPORT button within timeout period.")
            logger.info("Simulated Universe Collector task complete.")
            return
        else:
            logger.info("TELEPORT clicked successfully, proceeding to SU collection.")
            
            index_mark_clicked = False

            index_mark_timeout = Timer(5, count=20)
            index_mark_timeout.start()

            while not index_mark_timeout.reached():
                self.device.screenshot()
                if self.appear(IndexMark, similarity=0.80, interval=0):
                    logger.info("IndexMark found, attempting click.")
                    self.device.click(IndexMark, control_check=True)
                    index_mark_clicked = True
                    break
            if not index_mark_clicked:
                logger.info("IndexMark not found or already collected.")
                logger.info("Simulated Universe Collector task complete.")
                return
            else:
                logger.info("IndexMark clicked successfully, proceeding to sub-sections.")

            blessing_mark_clicked = False
            blessing_mark_timeout = Timer(3)
            blessing_mark_timeout.start()

            while not blessing_mark_timeout.reached():
                self.device.screenshot()
                if self.appear(BlessingMark, similarity=0.60, interval=0):
                    logger.info("BlessingMark found, attempting click.")
                    self.device.click(BlessingMark)
                    blessing_mark_clicked = True
                    break 

            if not blessing_mark_clicked:
                logger.info("BlessingMark not found or already collected.")
            else:
                logger.info("BlessingMark clicked successfully, proceeding to Blessings collection.")
                self._collect_blessings_index()
                
            occurrences_mark_clicked = False
            occurrences_mark_timeout = Timer(3)
            occurrences_mark_timeout.start()

            while not occurrences_mark_timeout.reached():
                self.device.screenshot()
                if self.appear(OccurrenceMark, similarity=0.60, interval=0):
                    logger.info("OccurrenceMark found, attempting click.")
                    self.device.click(OccurrenceMark)
                    occurrences_mark_clicked = True
                    break 

            if not occurrences_mark_clicked:
                logger.info("OccurrenceMark not found or already collected.")
            else:
                logger.info("OccurrenceMark clicked successfully, proceeding to Occurrences collection.")
                self._collect_occurrences_index()

            curios_mark_clicked = False
            curios_mark_timeout = Timer(3)
            curios_mark_timeout.start()

            while not curios_mark_timeout.reached():
                self.device.screenshot()
                if self.appear(CurioMark, similarity=0.60, interval=0):
                    logger.info("CurioMark found, attempting click.")
                    self.device.click(CurioMark)
                    curios_mark_clicked = True
                    break 

            if not curios_mark_clicked:
                logger.info("CurioMark not found or already collected.")
            else:
                logger.info("CurioMark clicked successfully, proceeding to Curios collection.")
                self._collect_curios_index()

            logger.info("Simulated Universe Index collection complete.")

        logger.info("Returning to main page.")
        logger.info("Simulated Universe Collector task complete.")
        return