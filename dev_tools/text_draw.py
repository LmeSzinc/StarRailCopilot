import cv2
import re
import numpy as np
import os
from PIL import ImageFont, ImageDraw, Image
from module.config.utils import read_file
from module.logger import logger
from module.base.utils import get_bbox_reversed,crop
import inspect
from tasks.relics.keywords import relics as relics_module

class TextImageGenerator:
    def __init__(self, keyword ,font_path="./dev_tools/zh-cn.ttf", font_size=20):
        self.font_en = ImageFont.truetype(font_path, font_size)
        self.font_cn = ImageFont.truetype(font_path, font_size)
        self.keyword=keyword

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

    def delete_files(self,folder_path):
        with os.scandir(folder_path) as entries:
            for entry in entries:
                if entry.is_file():
                    os.remove(entry.path)

    def relics_name_image_generator(self, output_path ,file_module):
        self.delete_files(output_path)
        content = inspect.getsource(file_module)
        text_patten= re.compile(r'' + self.keyword + r"='([^']*)'")
        name_pattern = re.compile(r"name='([^']*)'")
        text_values = text_patten.findall(content)
        name_values = name_pattern.findall(content)
        self.text_image_generator(text_values, name_values, font=self.font_cn, output_path=output_path)

if __name__ == '__main__':
    TextImageGenerator("cn").relics_name_image_generator(output_path="./assets/cn/relics/name/",file_module=relics_module)
    TextImageGenerator("en").relics_name_image_generator(output_path="./assets/en/relics/name/",file_module=relics_module)



