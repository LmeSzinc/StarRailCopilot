import os
import cv2
import numpy as np


class Detector:
    def __init__(self, scale=0.25):
        """
        A detector to detect the circle mark of enemy and item.
        """
        assert scale in [1., 0.25]
        self.scale = scale
        self.ui_mask = cv2.imread(os.path.join(os.path.dirname(__file__), "mask.png"), 0)

    def update(self, frame):
        # apply a mask to every frame to block the UI from interfering detection
        frame_masked = cv2.bitwise_and(frame, frame, mask=self.ui_mask)
        # update the detector with current frame before detection
        self.hsv = cv2.cvtColor(frame_masked, cv2.COLOR_BGR2HSV)

    def detect_item(self):
        filter_params = {
            '1': {
                'lowerb': np.array([0, 0, 230]),
                'upperb': np.array([180, 45, 255]),
            },
            '0.25': {
                'lowerb': np.array([0, 0, 235]),
                'upperb': np.array([120, 65, 255]),
            },
        }
        hough_params = {
            '1': {
                'minDist': 24,
                'param1': 200,
                'param2': 20,
                'minRadius': 5,
                'maxRadius': 12,
            },
            '0.25': {
                'minDist': 8,
                'param1': 200,
                'param2': 8,
                'minRadius': 2,
                'maxRadius': 4,
            },
        }

        # augment the target marker through mask based on HSV color space
        mask = cv2.inRange(self.hsv, **filter_params[f'{self.scale}'])
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)), iterations=1)
        mask = cv2.medianBlur(mask, 5)

        # resize the mask to reduce computational complexity of hough operation
        mask_scaled = cv2.resize(mask, None, fx=self.scale, fy=self.scale)
        circles = cv2.HoughCircles(mask_scaled, cv2.HOUGH_GRADIENT, 1, **hough_params[f'{self.scale}'])

        # if any target exists, return the center coordinates
        return self.get_coordinates(circles) if circles is not None else None

    def detect_enemy(self):
        filter_params = {
            '1': {
                'lowerb': np.array([0, 0, 140]),
                'upperb': np.array([180, 100, 255]),
            },
            '0.25': {
                'lowerb': np.array([0, 62, 209]),
                'upperb': np.array([180, 198, 255]),
            },
        }
        hough_params = {
            '1': {
                'param1': 200,
                'param2': 15,
                'minRadius': 20,
                'maxRadius': 27,
            },
            '0.25': {
                'param1': 200,
                'param2': 8,
                'minRadius': 5,
                'maxRadius': 9,
            },
        }

        mask = cv2.inRange(self.hsv, **filter_params[f'{self.scale}'])
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)), iterations=1)
        mask = cv2.medianBlur(mask, 5)

        mask_scaled = cv2.resize(mask, None, fx=self.scale, fy=self.scale)
        circles = cv2.HoughCircles(mask_scaled, cv2.HOUGH_GRADIENT, 1, 18, **hough_params[f'{self.scale}'])

        return self.get_coordinates(circles) if circles is not None else None

    def get_coordinates(self, circles):
        # convert coordinates to original scale
        circles = np.asarray(np.around(circles / self.scale), dtype=np.uint16).squeeze(0)
        return [circle[:2] for circle in circles]


def generate_ui_mask():
    """
    code to generate ui mask
    """
    mask = np.ones([720, 1280]) * 255
    mask[34:81, 21:61] = 0
    mask[179:220, 21:51] = 0
    mask[35:84, 183:218] = 0
    mask[0:61, 780:1280] = 0
    mask[145:435, 1153:1240] = 0
    cv2.circle(mask, (907, 614), 55, 0, -1)
    cv2.circle(mask, (1033, 542), 67, 0, -1)
    cv2.imwrite("mask.png", mask)


if __name__ == '__main__':
    # how to use
    class YourClass:
        def __init__(self, stream):
            self.stream = stream
            self.detector = Detector(scale=0.25)  # initiate a detector, recommend to set scale=0.25

            self.run()

        def run(self):
            while True:
                # update the detector with current frame before detection
                self.frame = cv2.cvtColor(self.stream.capture(), cv2.COLOR_RGB2BGR)
                self.detector.update(self.frame)

                # return a list of coordinates of corresponding target
                enemies = self.detector.detect_enemy()
                if enemies is not None:
                    self.plot_points(enemies)

                items = self.detector.detect_item()
                if items is not None:
                    self.plot_points(items)

                cv2.imshow("frame", self.frame)
                if cv2.waitKey(1) == ord('q'):
                    cv2.destroyAllWindows()
                    break

        def plot_points(self, points):
            for point in points:
                cv2.circle(self.frame, (point[0], point[1]), 3, (255, 255, 255), -1)
