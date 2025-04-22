import cv2
import numpy as np

from deploy.Windows.atomic import atomic_read_bytes, atomic_write
from module.base.utils import crop


class ImageTruncated(Exception):
    pass


def image_decode(data, area=None):
    """
    Args:
        data (np.ndarray):
        area (tuple):

    Returns:
        np.ndarray

    Raises:
        ImageTruncated:
    """
    # Decode image
    image = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ImageTruncated('Empty image after cv2.imdecode')
    shape = image.shape
    if not shape:
        raise ImageTruncated('Empty image after cv2.imdecode')
    if len(shape) == 2:
        channel = 0
    else:
        channel = shape[2]

    if area:
        # If image get cropped, return image should be copied to re-order array,
        # making later usages faster
        if channel == 3:
            image = crop(image, area, copy=False)
            return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        elif channel == 0:
            return crop(image, area, copy=True)
        elif channel == 4:
            image = crop(image, area, copy=False)
            return cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
        else:
            # proceed as RGB
            image = crop(image, area, copy=False)
            return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    else:
        if channel == 3:
            cv2.cvtColor(image, cv2.COLOR_BGR2RGB, dst=image)
            return image
        elif channel == 0:
            return image
        elif channel == 4:
            return cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
        else:
            # proceed as RGB
            cv2.cvtColor(image, cv2.COLOR_BGR2RGB, dst=image)
            return image


def image_load(file, area=None):
    """
    Load an image like pillow and drop alpha channel.

    Args:
        file (str):
        area (tuple):

    Returns:
        np.ndarray:

    Raises:
        FileNotFoundError:
        ImageTruncated:
    """
    # cv2.imread can't handle non-ascii filepath and PIL.Image.open is slow
    # Here we read with numpy first
    content = atomic_read_bytes(file)
    data = np.frombuffer(content, dtype=np.uint8)
    if not data.size:
        raise ImageTruncated('Empty file')
    return image_decode(data, area=area)


def image_encode(image, ext='png', encode=None):
    """
    Encode image

    Args:
        image (np.ndarray):
        ext:
        encode (list): Extra encode options

    Returns:
        np.ndarray:
    """
    shape = image.shape
    if len(shape) == 3:
        channel = shape[2]
        if channel == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        elif channel == 4:
            image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGRA)
        else:
            # proceed as RGB
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    # Keep grayscale unchanged

    # Prepare encode params
    ext = ext.lower()
    if encode is None:
        if ext == 'png':
            # Best compression, 0~9
            encode = [cv2.IMWRITE_PNG_COMPRESSION, 9]
        elif ext == 'jpg' or ext == 'jpeg':
            # Best quality
            encode = [cv2.IMWRITE_JPEG_QUALITY, 100]
        elif ext.lower() == '.webp':
            # Best quality
            encode = [cv2.IMWRITE_WEBP_QUALITY, 100]
        elif ext == 'tiff' or ext == 'tif':
            # LZW compression in TIFF
            encode = [cv2.IMWRITE_TIFF_COMPRESSION, 5]
        else:
            encode = []

    # Encode
    ret, buf = cv2.imencode(f'.{ext}', image, encode)
    if not ret:
        raise ImageTruncated('cv2.imencode failed')

    return buf


def image_save(image, file, encode=None):
    """
    Save an image like pillow.

    Args:
        image (np.ndarray):
        file (str):
        encode: (list): Encode params
    """
    _, _, ext = file.rpartition('.')
    data = image_encode(image, ext=ext, encode=encode)
    atomic_write(file, data)
