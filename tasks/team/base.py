import cv2
import numpy as np
from scipy import signal
from module.base.utils import crop, load_image, rgb2luma


def ensure_character_selection(raw):

    # 50px-width area starting from the right edge of HP bars
    area = (1101, 151, 1151, 459)
    # Y coordinates where the color peaks should be when character is selected
    expected_peaks = np.array([201, 279, 357, 436]) - area[1]
    # Use Luminance to fit H264 video stream
    image = rgb2luma(crop(raw, area))
    # Remove character names
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    image = cv2.erode(image, kernel)
    # To find peaks along Y
    line = cv2.reduce(image, 1, cv2.REDUCE_AVG).flatten().astype(int)

    # Find color peaks
    parameters = {
        'height': (60, 255),
        'prominence': 30,
        'distance': 5,
    }
    peaks, _ = signal.find_peaks(line, **parameters)
    # Remove smooth peaks
    parameters = {
        'height': (5, 255),
        'prominence': 5,
        'distance': 5,
    }
    diff = -np.diff(line)
    diff_peaks, _ = signal.find_peaks(diff, **parameters)

    def is_steep_peak(y, threshold=5):
        return np.abs(diff_peaks - y).min() <= threshold

    def peak_to_selected(y, threshold=5):
        distance = np.abs(expected_peaks - y)
        return np.argmin(distance) + 1 if distance.min() < threshold else 0

    selected = [peak_to_selected(peak) for peak in peaks if peak_to_selected(peak) and is_steep_peak(peak)]

    return selected
