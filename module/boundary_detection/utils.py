import math
import numpy as np
import cv2
import datetime

from module.base import utils

def _crop_image_with_object_area(image, area):
    """
    Crop the image with only object area.
    It will help filter lines outside the object area

    Args:
        image (np.array):
            Target Image
        area (tuple):
            tuple of length 4 representing width_min, height_min, width_max, height_max
    
    Returns:
        the cropped image
    """
    height, width, channels = image.shape
    cropped_image = image[area[1]:area[3], area[0]:area[2], 0:channels]
    return cropped_image


def _covert_hough_lines(lines, height_min, width_min):
    """
    Covert the hough lines from cv2 from represented by rho, theta to represented by 2 points.
    
    Args:
        lines (np.array):
            Shape of the lines is num_lines, 1, 2
        height_min (int):
            Min height of the area boundary
        width_min (int):
            Min width of the area boundary

    Returns:
        Converted lines with each line [x1, y1, x2, y2]
    """
    if lines is None or len(lines) == 0:
        return []

    num_lines = np.shape(lines)[0]
    rho = lines[:, :, 0].reshape(num_lines)
    theta = lines[:, :, 1].reshape(num_lines)
    a = np.cos(theta)
    b = np.sin(theta)
    x0 = a * rho
    y0 = b * rho
    x1 = (x0 + 1000*(-b) + width_min)
    y1 = (y0 + 1000*(a) + height_min)
    x2 = (x0 - 1000*(-b) + width_min)
    y2 = (y0 - 1000*(a) + height_min)
    return np.stack([x1, y1, x2, y2], axis=1).astype(int)


def _mask_image_hsv(cropped_image):
    """
    Mask target colors using hsv on the target regions
    
    Args:
        cropped_image (np.array):
            Cropped image with 

    Remarks:
        Objects are off 5 colors: orange, purple, blue, green, gray
        We filter the color based on the hsv of the five colors

    Returns:
        Mask image with only target colors highlighted
    """
    hsv_image = cv2.cvtColor(cropped_image, cv2.COLOR_RGB2HSV)

    orange_low = np.array([2, 73, 107])
    orange_high = np.array([19, 122, 222])
    orange_mask = cv2.inRange(hsv_image, orange_low, orange_high)

    green_low = np.array([85, 80, 75])
    green_high = np.array([111, 141, 180])
    green_mask = cv2.inRange(hsv_image, green_low, green_high)

    blue_low = np.array([105, 82, 92])
    blue_high = np.array([120, 174, 205])
    blue_mask = cv2.inRange(hsv_image, blue_low, blue_high)

    purple_low = np.array([114, 64, 82])
    purple_high = np.array([136, 142, 220])
    purple_mask = cv2.inRange(hsv_image, purple_low, purple_high)

    gray_low = np.array([109, 0, 55])
    gray_high = np.array([135, 68, 190])
    gray_mask = cv2.inRange(hsv_image, gray_low, gray_high)

    mask = orange_mask + blue_mask + purple_mask + green_mask + gray_mask
    print(f"HSV Mask: {np.shape(mask)}")
    print(f"Mask: {mask}")
    return cv2.bitwise_and(cropped_image, cropped_image, mask=mask)


def find_hough_lines(image, area):
    """
    Find the boundary lines of the objects with hough algorithm

    Args:
        image (np.array):
            target image
        area (tuple):
            tuple of length 4 representing width_min, height_min, width_max, height_max
    
    Returns:
        hough lines divided into horizontal ones and vertical ones
    """
    cropped_image = _crop_image_with_object_area(image, area)
    masked_image = _mask_image_hsv(cropped_image)
    gray = cv2.cvtColor(masked_image, cv2.COLOR_RGB2GRAY)
    _, threshold_image = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY)
    edges = cv2.Canny(threshold_image, 20, 150, apertureSize=3)
    lines_h = _covert_hough_lines(cv2.HoughLines(edges, 1, np.pi/180, 200), area[1], area[0])
    lines_v = _covert_hough_lines(cv2.HoughLines(edges, 1, np.pi/180, 110), area[1], area[0])
    
    lines_result_h = []
    h_axis = []
    for line in lines_h:
        if abs(line[1]-line[3]) < 2 and not any(abs(prev_line[1] - line[1]) < 5 for prev_line in lines_result_h):
            lines_result_h.append(line)
            h_axis.append(line[1])

    lines_result_v = []
    v_axis = []
    for line in lines_v:
        if abs(line[0]-line[2]) < 2  and not any(abs(prev_line[0] - line[0]) < 5 for prev_line in lines_result_v):
            lines_result_v.append(line)
            v_axis.append(line[0])

    return h_axis, v_axis
    

def get_object_rectangles(image, area):
    """
    Find the boundary rectangles of the objects

    Args:
        image (np.array):
            target image
        area (tuple):
            tuple of length 4 representing width_min, height_min, width_max, height_max
    
    Returns:
        hough lines divided into horizontal ones and vertical ones
    """
    lines_h, lines_v = find_hough_lines(image, area)
    lines_h.sort()
    lines_v.sort()

    rec_h_pair = []
    for h_index in range(1, len(lines_h)-1):
        if abs((lines_h[h_index] - lines_h[h_index-1]) - 89) < 2 and abs((lines_h[h_index+1] - lines_h[h_index]) - 20) < 2:
            rec_h_pair.append((lines_h[h_index-1], lines_h[h_index+1]))

    rec_v_pair = []
    for v_index in range(1, len(lines_v)):
        if abs((lines_v[v_index] - lines_v[v_index-1]) - 96) < 2:
            rec_v_pair.append((lines_v[v_index-1], lines_v[v_index]))

    for h_pair in rec_h_pair:
        for v_pair in rec_v_pair:
            cv2.rectangle(image, (v_pair[0], h_pair[0]), (v_pair[1], h_pair[1]), (0, 0, 255), 2)

    return rec_h_pair, rec_v_pair
