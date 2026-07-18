import cv2
import numpy as np


"""Find text rect
"""


class DetectText:

    @classmethod
    def detect_text_areas(cls, image_path):
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        blurred = cv2.GaussianBlur(image, (9, 9), 0)
        subtracted = cv2.subtract(image, blurred)

        _, binary = cv2.threshold(
            subtracted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        kernel = np.ones((9, 9), np.uint8)
        closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        dilated = cv2.dilate(closed, kernel, iterations=1)

        # cv2.RETR_EXTERNAL
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        text_areas = []
        output_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            # 过滤掉太小的区域
            if w > 5 and h > 13:
                text_areas.append((x, y, w, h))
                cv2.rectangle(output_image, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # text_areas, weights = cv2.groupRectangles(text_areas, groupThreshold=1, eps=0.5)
        # for x, y, w, h in text_areas:
        #     cv2.rectangle(output_image, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.imshow("Detected Text Areas", output_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        return text_areas


if __name__ == "__main__":
    image_path = ".\dev_tools\MuMu12-20240709-005243.png"
    DetectText.detect_text_areas(image_path)
