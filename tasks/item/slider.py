import numpy as np
from scipy import signal

from module.base.button import ButtonWrapper, ClickButton
from module.base.timer import Timer
from module.base.utils import rgb2gray
from module.exception import ScriptError
from module.logger import logger
from tasks.base.ui import UI


class Slider:
    def __init__(
            self,
            main: UI,
            slider: ButtonWrapper,
            parameters: dict = None,
            background=5
    ):
        """
        Args:
            main:
            slider: Slider button
            parameters (dict): Parameters passing to scipy.find_peaks
            background (int):
        """
        self.main = main
        self.slider = slider

        if parameters is None:
            parameters = {}
        self.parameters = parameters
        self.background = background

        # Actual slider area
        self.area = self.slider.area

    def cal_slider(self):
        """
        Slider always have its left side fixed, right side movable depending on the maximum number
        Calculate the right side, similar to AdaptiveScroll.match_color
        """
        area = self.slider.area
        area = (area[0], area[1] - self.background, area[2], area[3] + self.background)
        image = self.main.image_crop(area, copy=False)
        image = rgb2gray(image)
        image = image.flatten('F')
        wlen = area[3] - area[1]
        total = area[2] - area[0]

        parameters = {
            'prominence': 15,
            'wlen': wlen,
            'width': 4,
            'distance': wlen / 2,
        }
        parameters.update(self.parameters)
        peaks, _ = signal.find_peaks(image, **parameters)
        peaks //= wlen

        # Ignore non-continuous peaks, which may be the letter to the right of slider
        try:
            right = np.where(np.diff(peaks) >= 3)[0][0]
            peaks = peaks[:right + 1]
        except IndexError:
            pass
        # Calculate actual slider area
        try:
            length = peaks[-1]
            self.area = (area[0], area[1], area[0] + length + 1, area[3])
        except IndexError:
            length = total
            self.area = self.slider.area
        logger.info(f'Slider length: {length}/{total}')

    def set(self, value: int, total: int, skip_first_screenshot=True):
        """
        Args:
            value: Value to set
            total: Maximum amount of slider
            skip_first_screenshot:

        Returns:
            bool: If success
        """
        logger.info(f'Slider set {value}/{total}')
        if value > total:
            raise ScriptError(f'Slider.set value {value} > total {total}')
        if total <= 0:
            raise ScriptError(f'Slider.set total {total} <= 0')
        if value <= 0:
            raise ScriptError(f'Slider.set value {value} <= 0')
        if value == total == 1:
            logger.info('Slider set total==1, no need to set')
            return True
        # if value == 1:
        #     logger.info('Slider set value==1, no need to set')
        #     return True

        self.cal_slider()

        # 18px is the width of controller
        length = self.area[2] - self.area[0] - 18

        left = int((value - 2) / (total - 1) * length) + self.area[0]
        right = int((value - 1) / (total - 1) * length) + self.area[0]
        if right <= left:
            right = left + 1
        # 10px is the radius of slider controller
        # When you somewhere on the slider, left edge of controller is where you click
        # if right - left < 10:
        #     logger.info('Setting high maximum slider')
        #     left -= 10
        #     right -= 10

        # Limit in slider
        left = max(min(self.area[2] - 1, left), self.area[0])
        right = max(min(self.area[2], right), self.area[0] + 1)
        # Click the right half
        left = int((left + right) / 2)
        button = ClickButton(
            (left, self.area[1], right, self.area[3]),
            name=f'Slider_{value}_{total}')
        # Pad click area to search
        pad = 15
        detect = (right - pad, self.area[1], right + pad, self.area[3])
        logger.info(f'Controller button={button.button}, detect={detect}')

        interval = Timer(1, count=3)
        trial = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.main.device.screenshot()

            # End
            if trial > 3:
                logger.warning('Slider.set failed after 3 trial')
                return False
            if self.main.image_color_count(detect, color=(255, 255, 255), threshold=221, count=50):
                logger.info('Slider set done')
                return True

            # Click
            if interval.reached():
                self.main.device.click(button)
                interval.reset()
                trial += 1
