import cv2
import re
import numpy as np
import os
from PIL import ImageFont, ImageDraw, Image
from module.config.utils import read_file
from module.logger import logger
from module.base.utils import get_bbox_reversed,crop


class TextImageGenerator:
    def __init__(self, font_path="./dev_tools/zh-cn.ttf", font_size=20):
        self.font_en = ImageFont.truetype(font_path, font_size)
        self.font_cn = ImageFont.truetype(font_path, font_size)

    @staticmethod
    def split_string_at_last_space(input_string):
        if all(ord(char) < 128 for char in input_string) and len(input_string) > 35:
            last_space_index = input_string.rfind(' ')
            if last_space_index == -1:
                return input_string, ""
            part1 = input_string[:last_space_index]
            part2 = input_string[last_space_index + 1:]
            return part1
        else:
            return input_string

    def text_image_generator(self, chars, names, font, output_path='./'):
        for char, name in zip(chars, names):
            image_path = os.path.join(output_path, name + '.png')
            part = self.split_string_at_last_space(char)
            image = np.ones((50, 370), dtype=np.uint8) * 255
            image_pil = Image.fromarray(image)
            draw = ImageDraw.Draw(image_pil)
            draw.text((2, 0.5), part, font=font, fill=0)
            image = np.array(image_pil)
            crop_image = crop(image, get_bbox_reversed(image, 70))
            image_pil = Image.fromarray(crop_image)
            image_pil.save(image_path)
            logger.info(f'{name} generated')

    def relics_name_image_generator(self, content_file='./tasks/relics/keywords/relics.py', output_path_cn='./assets/cn/relics/name/', output_path_en='./assets/en/relics/name/'):
        with open(content_file, 'r', encoding='utf-8') as file:
            content = file.read()
        cn_pattern = re.compile(r"cn='([^']*)'")
        en_pattern = re.compile(r"en='([^']*)'")
        name_pattern = re.compile(r"name='([^']*)'")
        cn_values = cn_pattern.findall(content)
        en_values = en_pattern.findall(content)
        name_values = name_pattern.findall(content)
        self.text_image_generator(cn_values, name_values, font=self.font_cn, output_path=output_path_cn)
        self.text_image_generator(en_values, name_values, font=self.font_en, output_path=output_path_en)

if __name__ == '__main__':
    generator = TextImageGenerator()
    generator.relics_name_image_generator()



