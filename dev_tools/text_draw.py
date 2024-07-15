import cv2
import re
import numpy as np
import os
from PIL import ImageFont, ImageDraw, Image
from module.config.utils import read_file
from module.logger import logger


def crop_to_text_edge(original_image):
    gray = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)

    _, binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    x_min, y_min = float('inf'), float('inf')
    x_max, y_max = float('-inf'), float('-inf')

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        x_min = min(x_min, x)
        y_min = min(y_min, y)
        x_max = max(x_max, x + w)
        y_max = max(y_max, y + h)

    cropped_image = original_image[y_min:y_max, x_min:x_max]
    return cropped_image


def split_string_at_last_space(input_string):
    if all(ord(char) < 128 for char in input_string) and len(input_string) > 35:
        last_space_index = input_string.rfind(' ')

        if last_space_index == -1:
            return input_string, ""

        part1 = input_string[:last_space_index]
        part2 = input_string[last_space_index + 1:]

        return part1, part2
    else:
        return input_string, ""


def text_image_generator(chars, names, font, output_path='./'):
    for char, name in zip(chars, names):
        image_path = os.path.join(output_path, name + '.png')
        if (os.path.isfile(image_path)):
            logger.info(f'{name} already exists, skipping')
            continue
        else:
            part = ['', '']
            part = split_string_at_last_space(char)

            image = np.ones((50, 370, 3), dtype=np.uint8) * 255

            image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

            draw = ImageDraw.Draw(image_pil)

            draw.text((2, 0.5), part[0], font=font, fill=(0, 0, 0))
            draw.text((2, 25), part[1], font=font, fill=(0, 0, 0))

            image = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)

            crop_image = crop_to_text_edge(image)
            cv2.imencode('.png', crop_image)[1].tofile(image_path)
            logger.info(f'{name} generated')


def relics_name_image_generator():
    font_en = ImageFont.truetype("./dev_tools/zh-cn.ttf", 20)
    font_cn = ImageFont.truetype("./dev_tools/zh-cn.ttf", 20)
    output_path_cn = './assets/cn/relics/name/'
    output_path_en = './assets/en/relics/name/'

    with open('./tasks/relics/keywords/relics.py', 'r', encoding='utf-8') as file:
        content = file.read()

    cn_pattern = re.compile(r"cn='([^']*)'")
    en_pattern = re.compile(r"en='([^']*)'")
    name_pattern = re.compile(r"name='([^']*)'")

    cn_values = cn_pattern.findall(content)
    en_values = en_pattern.findall(content)
    name_values = name_pattern.findall(content)

    text_image_generator(cn_values, name_values, font=font_cn, output_path=output_path_cn)
    text_image_generator(en_values, name_values, font=font_en, output_path=output_path_en)


if __name__ == '__main__':
    relics_name_image_generator()



