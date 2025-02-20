import os
import shutil
from io import BytesIO
from pathlib import Path
from typing import Dict, Tuple

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import FreeTypeFont

from module.base.utils import crop, get_bbox_reversed, rgb2gray


class Font:
    _font_cache: Dict[Tuple[str, float], FreeTypeFont] = {}
    _file_cache: Dict[str, bytes] = {}
    _root = Path(__file__).joinpath('../../../../').resolve()
    _font_folder = _root.joinpath('dev_tools/fonts').resolve()

    @classmethod
    def _get_font_io(cls, file: str) -> BytesIO:
        try:
            cache = cls._file_cache[file]
            return BytesIO(cache)
        except KeyError:
            pass
        # Read file to BytesIO
        path = cls._font_folder.joinpath(f'./{file}').resolve().__str__()
        try:
            with open(path, "rb") as f:
                cache = f.read()
        except FileNotFoundError:
            print(f'Font file does not exist: {file}')
            print(f'You should copy fonts from desktop client '
                  f'"Star Rail/Game/StarRail_Data/StreamingAssets/MiHoYoSDKRes/HttpServerResources/font"'
                  f' to "StarRailCopilot/dev_tools/fonts"')
            exit(1)
        cls._file_cache[file] = cache
        return BytesIO(cache)

    @classmethod
    def get_font(cls, file: str, size: float) -> FreeTypeFont:
        try:
            return cls._font_cache[(file, size)]
        except KeyError:
            pass
        # Create Font object
        cache = cls._get_font_io(file)
        font = ImageFont.truetype(cache, size)
        cls._font_cache[(file, size)] = font
        return font

    @classmethod
    def clear_font_cache(cls):
        cls._font_cache.clear()

    @classmethod
    def clear_all_cache(cls):
        cls._font_cache.clear()
        cls._file_cache.clear()

    def __init__(self, file: str, size: float):
        self.file: str = file
        self.size: float = size
        self.font: FreeTypeFont = self.__class__.get_font(file, size)

    def draw(self, text: str, file: str = ''):
        """
        Convert text to image.
        Text are in black and background is in white.

        Args:
            text: Text to draw
            file: If given, write image to file

        Returns:
            np.ndarray:
        """
        # Create temp image and draw text first
        temp_image = Image.new('RGB', (1, 1))
        temp_draw = ImageDraw.Draw(temp_image)
        text_bbox = temp_draw.textbbox((0, 0), text, font=self.font)
        # Calculate text border
        pad = 2
        left, top, right, bottom = text_bbox
        text_width = right - left + pad * 2
        text_height = bottom - top + pad * 2
        x_offset = -left + pad
        y_offset = -top + pad

        # Draw text
        image = Image.new('RGB', (text_width, text_height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        draw.text((x_offset, y_offset), text, font=self.font, fill=(0, 0, 0))

        # Crop to text edge
        # image.show()
        image = np.array(image)
        image = crop(image, get_bbox_reversed(image), copy=True)
        image = rgb2gray(image)

        # Image.fromarray(image, mode='L').show()
        if file != '':
            self.write(image, file)
        return image

    def write(self, image, file: str):
        """
        Write image to file with auto folder creation
        """
        file = self.__class__._root.joinpath(file).resolve()
        f = str(file)
        print(f'Write image file: {f}')

        success = cv2.imwrite(f, image)
        if success:
            return

        file.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(file), image)

    @classmethod
    def clear_output(cls, folder):
        folder = cls._root.joinpath(folder).resolve()
        try:
            files = list(folder.iterdir())
        except FileNotFoundError:
            return
        for file in files:
            if os.path.islink(file):
                os.unlink(file)
            elif os.path.isfile(file):
                os.remove(file)
            else:
                shutil.rmtree(file)


class GeneratorBase:
    @classmethod
    def generate(cls):
        """
        Call all functions defined in this class

        Examples:
            class RelicRecGenerator(GeneratorBase):
                @classmethod
                def rec_main_cn(cls):
                    pass

            RelicRecGenerator.generate()
            # RelicRecGenerator.rec_main_cn() will be called
        """
        for name, func in vars(cls).items():
            if name.startswith('_'):
                continue
            if callable(func):
                print(f'Run func: {cls.__name__}.{name}')
                func()
            elif isinstance(func, classmethod):
                print(f'Run func: {cls.__name__}.{name}')
                getattr(cls, name)()
