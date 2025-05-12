import os
from datetime import datetime
from PIL import Image
from module.logger import logger

class DebugHelper:
    _SCREENSHOT_DIR = "temp_screenshots/reward_debugger"  # Moved and defined here

    def __init__(self, device, appear_method):
        """
        Initializes the DebugHelper.
        Args:
            device: The device object for interacting with the game.
            appear_method: The bound 'appear' method from the calling class (e.g., collector.appear).
        """
        self.device = device
        self.appear = appear_method
        # self.screenshot_dir is no longer passed, uses self._SCREENSHOT_DIR
        self._ensure_screenshot_dir_exists()

    def _ensure_screenshot_dir_exists(self):
        """Ensures the screenshot directory exists, creates it if not."""
        if not os.path.exists(self._SCREENSHOT_DIR): # Uses class variable
            try:
                os.makedirs(self._SCREENSHOT_DIR)
                logger.info(f"Created screenshot directory: {self._SCREENSHOT_DIR}")
            except OSError as e:
                logger.error(f"Failed to create screenshot directory {self._SCREENSHOT_DIR}: {e}")

    def capture_and_save_debug_screenshot(self, filename_prefix="debug_shot"):
        """
        Captures the current screen and saves it to the debug screenshot directory.
        The filename will include the prefix and a timestamp.
        """
        try:
            self.device.screenshot()

            if self.device.image is None:
                logger.error("Failed to capture screenshot (self.device.image is None).")
                return

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{filename_prefix}_{timestamp}.png"
            filepath = os.path.join(self._SCREENSHOT_DIR, filename) # Uses class variable

            image_pil = Image.fromarray(self.device.image)
            image_pil.save(filepath)
            logger.info(f"Debug screenshot saved to: {filepath}")

        except Exception as e:
            logger.error(f"Error during capture_and_save_debug_screenshot: {e}")

    def debug_match_tester(self, asset_to_test, start_sim=0.50, end_sim=0.99, step=0.01):
        """
        Debug function to test asset matching with varying similarity thresholds.
        Args:
            asset_to_test: The asset object (e.g., IndexMark) to test.
            start_sim: The starting similarity threshold.
            end_sim: The ending similarity threshold.
            step: The increment for the similarity threshold.
        """
        logger.info(f"--- Starting Debug Match Test for: {asset_to_test.name} ---")
        self.device.screenshot()
        current_sim = start_sim
        while current_sim <= end_sim:
            current_sim_rounded = round(current_sim, 2)
            logger.info(f"Testing {asset_to_test.name} with similarity: {current_sim_rounded:.2f}")

            if self.appear(asset_to_test, similarity=current_sim_rounded, interval=0, static=False):
                logger.info(f"    MATCH FOUND for {asset_to_test.name} at similarity {current_sim_rounded:.2f}")
            else:
                logger.info(f"    No match for {asset_to_test.name} at similarity {current_sim_rounded:.2f}")
            current_sim += step
            if current_sim > end_sim + (step / 2):
                break
        logger.info(f"--- Finished Debug Match Test for: {asset_to_test.name} ---") 