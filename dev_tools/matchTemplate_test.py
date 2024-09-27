import cv2
import numpy as np
import os

"""Find text rect
"""
template_folder = 'D:/Code_Work/antec/StarRailCopilot/assets/cn/relics/name'

class DetectText:

    @classmethod
    def detect_text_areas(cls, image_path):
        imagea = cv2.imread(image_path)
        hsv = cv2.cvtColor(imagea, cv2.COLOR_BGR2HSV)

        # 定义白色的 HSV 范围，并生成白色掩膜
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 30, 255])
        white_mask = cv2.inRange(hsv, lower_white, upper_white)

        # 定义橙色的 HSV 范围，并生成橙色掩膜
        lower_orange = np.array([10, 100, 100])
        upper_orange = np.array([25, 255, 255])
        orange_mask = cv2.inRange(hsv, lower_orange, upper_orange)

        # 将两个掩膜进行结合
        combined_mask = cv2.bitwise_or(white_mask, orange_mask)
        result = cv2.bitwise_not(combined_mask)
        # cv2.imshow("result", result)


        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        # blurred = cv2.GaussianBlur(image, (9, 9), 0)
        # subtracted = cv2.subtract(image, blurred)
        #
        # _, binary = cv2.threshold(
        #     subtracted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        # )


        result_inv=cv2.bitwise_not(result)
        kernel = np.ones((9, 9), np.uint8)
        closed = cv2.morphologyEx(result_inv, cv2.MORPH_CLOSE, kernel)

        dilated = cv2.dilate(closed, kernel, iterations=2)

        # cv2.RETR_EXTERNAL
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        text_areas = []
        output_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        point=(887,500)
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            # 过滤掉太小的区域
            if w > 5 and h > 13:
                text_areas.append((x, y, w, h))
                cv2.rectangle(output_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                if cv2.pointPolygonTest(contour, point, measureDist=False) >= 0:
                    roi = result[y:y + h, x:x + w]
                    # cv2.imshow("binary_roi", binary_roi)

                    # 模板匹配
                    best_match_score = 0
                    best_match_name = None
                    for filename in os.listdir(template_folder):
                        if filename.endswith(('.png', '.jpg', '.jpeg')):
                            template = cv2.imread(os.path.join(template_folder, filename), 0)
                            w, h = template.shape[::-1]
                            if roi.shape[0] < template.shape[0] or roi.shape[1] < template.shape[1]:
                                continue
                            # cv2.imshow("template", template)
                            # cv2.imshow("roi", roi)
                            res = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)
                            threshold = 0.75  # 你可以根据需要调整这个阈值
                            loc = np.where(res >= threshold)
                            if loc[0].size > 0:
                                # 如果找到至少一个匹配项，取最大值的索引
                                max_val = np.max(res)
                                if max_val > best_match_score:
                                    best_match_score = max_val
                                    best_match_name = filename

                                    # 如果找到了最佳匹配，则在原图上绘制匹配的图片名字
                    if best_match_name:
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        cv2.putText(output_image, best_match_name, (x, y - 15), font, 0.8, (0, 0, 255), 2)


            # text_areas, weights = cv2.groupRectangles(text_areas, groupThreshold=1, eps=0.5)
        # for x, y, w, h in text_areas:
        #     cv2.rectangle(output_image, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.imshow("Detected Text Areas", output_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        return text_areas


def process_images_in_folder(folder_path):
    # 确保文件夹路径以斜杠结束，以便正确拼接文件路径
    if not folder_path.endswith(os.sep):
        folder_path += os.sep

        # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        # 检查文件扩展名，确保只处理图片文件
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            # 拼接完整的文件路径
            image_path = os.path.join(folder_path, filename)
            # 调用DetectText的detect_text_areas函数处理图片
            DetectText.detect_text_areas(image_path)


if __name__ == "__main__":
    # 指定包含图片的文件夹路径
    folder_path = "D:/Code_Work/antec/StarRailCopilot/dev_tools/"
    # 调用函数处理文件夹中的所有图片
    process_images_in_folder(folder_path)