import os
import re
import typing as t
from dataclasses import dataclass

import cv2
import numpy as np
from tqdm import tqdm

from module.base.code_generator import CodeGenerator
from module.base.utils import (
    SelectedGrids, area_center, area_limit, area_pad, corner2area, get_bbox, get_color, image_size, load_image)
from module.config.config_manual import ManualConfig as AzurLaneConfig
from module.config.server import VALID_LANG
from module.config.utils import deep_get, deep_iter, deep_set, iter_folder
from module.logger import logger

SHARE_SERVER = 'share'
ASSET_SERVER = [SHARE_SERVER] + VALID_LANG


def parse_grid(image):
    """
    Args:
        image:

    Returns:
        dict: Key: Grid position (x, y)
            Value: Area on image
    """
    image = cv2.inRange(image, (127, 127, 127), (255, 255, 255))
    contours, _ = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    dic_rect = {}
    for corners in contours:
        area = corner2area(corners.reshape(4, 2)) + (0, 0, 1, 1)
        center = area_center(area)
        dic_rect[center] = area
    # for k, v in dic_rect.items():
    #     print(k, v)

    dic_grid = {}
    prev_y = -100
    grid_y = -1
    stack_center = []
    for center in sorted(dic_rect.keys(), key=lambda x: x[1]):
        if center[1] > prev_y + 3:
            for x, c in enumerate(sorted(stack_center, key=lambda x: x[0])):
                dic_grid[(x, grid_y)] = tuple(dic_rect[c].astype(int))
            grid_y += 1
            stack_center = []
        stack_center.append(center)
        prev_y = center[1]
    for x, c in enumerate(sorted(stack_center, key=lambda x: x[0])):
        dic_grid[(x, grid_y)] = tuple(dic_rect[c].astype(int))
    # for k, v in dic_grid.items():
    #     print(k, v)
    return dic_grid


class AssetsImage:
    REGEX_ASSETS = re.compile(
        f'^{AzurLaneConfig.ASSETS_FOLDER}/'
        f'(?P<server>{"|".join(ASSET_SERVER).lower()})/'
        f'(?P<module>[a-zA-Z0-9_/]+?)/'
        f'(?P<assets>\w+)'
        f'(?P<frame>\.\d+)?'
        f'(?P<attr>\.AREA|\.SEARCH|\.COLOR|\.BUTTON|\.GRID)?'
        f'\.png$'
    )

    def __init__(self, file: str):
        """
        Args:
            file: ./assets/<server>/<module>/<assets>.<frame>.<attr>.png
                Example: ./assets/cn/ui/login/LOGIN_CONFIRM.2.BUTTON.png
                then, server="cn", module="ui/login", assets="LOGIN_CONFIRM", frame=2, attr="BUTTON"
                <frame> and <attr> are optional.
        """
        self.file: str = file
        prefix = AzurLaneConfig.ASSETS_FOLDER
        res = AssetsImage.REGEX_ASSETS.match(file)

        self.valid = False
        self.server = ''
        self.module = ''
        self.assets = ''
        self.frame = 1
        self.attr = ''
        self.posi = None

        if res:
            self.valid = True
            self.server = res.group('server')
            self.module = res.group('module')
            self.assets = res.group('assets')
            if res.group('frame'):
                self.frame = int(res.group('frame').strip('.'))
            else:
                self.frame = 1
            if res.group('attr'):
                self.attr = res.group('attr').strip('.')
            else:
                self.attr = ''
            self.parent_file = f'{prefix}{res.group(1)}.png'
        else:
            logger.info(f'Invalid assets name: {self.file}')

        self.bbox: t.Tuple = ()
        self.mean: t.Tuple = ()
        self.grids = {}

    def parse(self):
        image = load_image(self.file)

        size = image_size(image)
        if size != AzurLaneConfig.ASSETS_RESOLUTION:
            logger.warning(f'{self.file} has wrong resolution: {size}')
            self.valid = False
        bbox = get_bbox(image)
        mean = get_color(image=image, area=bbox)
        mean = tuple(np.rint(mean).astype(int))
        self.bbox = bbox
        self.mean = mean

        if self.attr == 'GRID':
            self.grids = parse_grid(image)

        return bbox, mean

    def __str__(self):
        if self.valid:
            return f'AssetsImage(module={self.module}, assets={self.assets}, server={self.server}, frame={self.frame}, attr={self.attr})'
        else:
            return f'AssetsImage(file={self.file}, valid={self.valid})'

    @property
    def is_GRID(self):
        return self.attr == 'GRID'

    @property
    def is_base(self):
        return self.attr == ''

    def iter_grids(self):
        frame = 0
        for posi, rect in self.grids.items():
            frame += 1
            image = AssetsImage(self.file)
            image.attr = ''
            image.bbox = rect
            image.mean = self.mean
            image.frame = frame
            image.posi = posi
            yield image


def iter_images():
    for server in ASSET_SERVER:
        for path, folders, files in os.walk(os.path.join(AzurLaneConfig.ASSETS_FOLDER, server)):
            for file in files:
                if not file.startswith('.'):
                    file = os.path.join(path, file).replace('\\', '/')
                    yield AssetsImage(file)


def iter_grids(images):
    for image in images:
        for grid in image.iter_grids():
            yield grid


@dataclass
class DataAssets:
    module: str
    assets: str
    server: str
    frame: int
    file: str = ''
    posi = None
    area: t.Tuple[int, int, int, int] = ()
    search: t.Tuple[int, int, int, int] = ()
    color: t.Tuple[int, int, int] = ()
    button: t.Tuple[int, int, int, int] = ()

    has_raw_area = False
    has_raw_search = False
    has_raw_color = False
    has_raw_button = False

    @staticmethod
    def area_to_search(area):
        area = area_pad(area, pad=-20)
        area = area_limit(area, (0, 0, *AzurLaneConfig.ASSETS_RESOLUTION))
        return area

    @classmethod
    def product(cls, image: AssetsImage):
        """
        Product DataAssets from AssetsImage with attr=""
        """
        data = cls(module=image.module, assets=image.assets, server=image.server, frame=image.frame, file=image.file)
        return data

    def load_image(self, image: AssetsImage):
        if image.attr == '':
            self.file = image.file
            self.area = image.bbox
            self.color = image.mean
            self.button = image.bbox
            self.posi = image.posi
        elif image.attr == 'AREA':
            self.area = image.bbox
            self.has_raw_area = True
        elif image.attr == 'SEARCH':
            self.search = image.bbox
            self.has_raw_search = True
        elif image.attr == 'COLOR':
            self.color = image.mean
            self.has_raw_color = True
        elif image.attr == 'BUTTON':
            self.button = image.bbox
            self.has_raw_button = True
        elif image.attr == 'GRID':
            pass
        else:
            logger.warning(f'Trying to load an image with unknown attribute: {image}')

    def generate_code(self):
        return f'Assets(file="{self.file}", area={self.area}, search={self.search}, color={self.color}, button={self.button})'


def iter_assets():
    images = list(iter_images())

    # parse images, this may take a while
    for image in tqdm(images):
        image.parse()

    images += list(iter_grids(images))

    # Validate images
    images = SelectedGrids(images).select(valid=True)
    images.create_index('module', 'assets', 'server', 'frame', 'attr')
    for image in images.filter(lambda x: bool(x.attr)):
        image: AssetsImage = image
        if image.is_GRID:
            pass
        else:
            if not images.indexed_select(image.module, image.assets, image.server, image.frame, ''):
                logger.warning(f'Attribute assets has no parent assets: {image.file}')
                image.valid = False
            if not images.indexed_select(image.module, image.assets, image.server, 1, ''):
                logger.warning(f'Attribute assets has no first frame: {image.file}')
                image.valid = False
        if image.attr == 'SEARCH' and image.frame > 1:
            logger.warning(f'Attribute SEARCH with frame > 1 is not allowed: {image.file}')
            image.valid = False
    images = images.select(valid=True).sort('module', 'assets', 'server', 'frame')

    # Convert to DataAssets
    data = {}
    for image in images:
        if image.is_base:
            row = DataAssets.product(image)
            row.load_image(image)
            deep_set(data, keys=[image.module, image.assets, image.server, image.frame], value=row)
    # Load attribute images
    for image in images:
        if not image.is_base:
            row = deep_get(data, keys=[image.module, image.assets, image.server, image.frame])
            row.load_image(image)
    # Set `search`
    for path, frames in deep_iter(data, depth=3):
        # print(path, frames)
        for frame in frames.values():
            # Generate `search` from `area`
            if not frame.has_raw_search:
                frame.search = DataAssets.area_to_search(frame.area)
        # If an attribute is set in the first frame, apply to all
        first: DataAssets = frames[1]
        for frame in frames.values():
            # frame: DataAssets = frame
            if not frame.has_raw_area and first.has_raw_area:
                frame.area = first.area
            if not frame.has_raw_search and first.has_raw_search:
                frame.search = first.search
            if not frame.has_raw_color and first.has_raw_color:
                frame.color = first.color
            if not frame.has_raw_button and first.has_raw_button:
                frame.button = first.button

    return data


def generate_code():
    all_assets = iter_assets()
    for module, module_data in all_assets.items():
        path = os.path.join(AzurLaneConfig.ASSETS_MODULE, module.split('/', maxsplit=1)[0])
        output = os.path.join(path, 'assets.py')
        if os.path.exists(output):
            os.remove(output)
        output = os.path.join(path, 'assets')
        os.makedirs(output, exist_ok=True)
        for prev in iter_folder(output, ext='.py'):
            if os.path.basename(prev) == '__init__.py':
                continue
            os.remove(prev)

    for module, module_data in all_assets.items():
        path = os.path.join(AzurLaneConfig.ASSETS_MODULE, module.split('/', maxsplit=1)[0])
        output = os.path.join(path, 'assets')
        gen = CodeGenerator()
        gen.Import("""
        from module.base.button import Button, ButtonWrapper
        """)
        gen.CommentAutoGenerage('dev_tools.button_extract')
        for assets, assets_data in module_data.items():
            has_share = SHARE_SERVER in assets_data
            with gen.Object(key=assets, object_class='ButtonWrapper'):
                gen.ObjectAttr(key='name', value=assets)
                if has_share:
                    servers = assets_data.keys()
                else:
                    servers = VALID_LANG
                for server in servers:
                    frames = list(assets_data.get(server, {}).values())
                    if len(frames) > 1:
                        with gen.ObjectAttr(key=server, value=gen.List()):
                            for index, frame in enumerate(frames):
                                with gen.ListItem(gen.Object(object_class='Button')):
                                    gen.ObjectAttr(key='file', value=frame.file)
                                    gen.ObjectAttr(key='area', value=frame.area)
                                    gen.ObjectAttr(key='search', value=frame.search)
                                    gen.ObjectAttr(key='color', value=frame.color)
                                    gen.ObjectAttr(key='button', value=frame.button)
                                    if frame.posi is not None:
                                        gen.ObjectAttr(key='posi', value=frame.posi)
                    elif len(frames) == 1:
                        frame = frames[0]
                        with gen.ObjectAttr(key=server, value=gen.Object(object_class='Button')):
                            gen.ObjectAttr(key='file', value=frame.file)
                            gen.ObjectAttr(key='area', value=frame.area)
                            gen.ObjectAttr(key='search', value=frame.search)
                            gen.ObjectAttr(key='color', value=frame.color)
                            gen.ObjectAttr(key='button', value=frame.button)
                            if frame.posi is not None:
                                gen.ObjectAttr(key='posi', value=frame.posi)
                    else:
                        gen.ObjectAttr(key=server, value=None)
        gen.write(os.path.join(output, f'assets_{module.replace("/", "_")}.py'))


if __name__ == '__main__':
    generate_code()
