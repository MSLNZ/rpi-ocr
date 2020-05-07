"""
Utility functions for performing image conversion and image processing.
"""
import base64
import logging
from io import BytesIO
from os.path import splitext

import cv2
import numpy as np
from PIL import Image
from PIL.Image import Image as PillowImage
from PIL import ImageFilter

DEFAULT_IMAGE_FORMAT = 'jpg'
DEFAULT_FILE_EXTENSION = '.' + DEFAULT_IMAGE_FORMAT
SIGNATURE_MAP = {
    'bmp': b'BM',
    'dib': b'BM',
    'jpg': b'\xff\xd8\xff',
    'jpeg': b'\xff\xd8\xff',
    'jpe': b'\xff\xd8\xff',
    'png': b'\x89PNG\r\n\x1a\n',
    'tif': b'II*\x00',
    'tiff': b'II*\x00',
}

logger = logging.getLogger('ocr')


class OpenCVImage(np.ndarray):
    """A :class:`numpy.ndarray` that has an `ext` attribute.

    The `ext` attribute represents the file extension that defines the output
    format. It can be used by the :func:`cv2.imencode` function.
    """

    def __new__(cls, array, ext=DEFAULT_FILE_EXTENSION):
        obj = np.asarray(array).view(cls)
        obj.ext = ext
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        self.ext = getattr(obj, 'ext', DEFAULT_FILE_EXTENSION)


def save(filename, image, params=None):
    """Save the image.

    Parameters
    ----------
    filename : :class:`str`
        The name to use to save the image file. The image format is chosen based on the filename extension
    image : :class:`bytes`, :class:`str`, :class:`OpenCVImage` or :class:`PIL.Image.Image`
        The image to save.
    params : :class:`tuple`, optional
        See :func:`cv2.imwrite` for more details.
    """
    img = cv2.cvtColor(to_cv2(image), cv2.COLOR_RGB2BGR)
    cv2.imwrite(filename, img, params=params)


def to_bytes(obj):
    """Convert an object to the :class:`bytes` representation of the image.

    Parameters
    ----------
    obj : :class:`bytes`, :class:`str`, :class:`OpenCVImage` or :class:`PIL.Image.Image`
        The object to convert.

    Returns
    -------
    :class:`bytes`
        The image as bytes.
    """
    if isinstance(obj, str):
        try:
            with open(obj, 'rb') as fp:
                return fp.read()
        except OSError:
            try:
                return base64.b64decode(obj)
            except ValueError:
                raise ValueError('Invalid path or base64 string, {!r}'.format(obj)) from None

    if isinstance(obj, OpenCVImage):
        bgr_image = cv2.cvtColor(obj, code=cv2.COLOR_RGB2BGR)
        ret, buf = cv2.imencode(obj.ext, bgr_image)
        if not ret:
            raise RuntimeError('error calling cv2.imencode')
        return buf.tobytes()

    if isinstance(obj, PillowImage):
        b = BytesIO()
        obj.save(b, obj.format)
        return b.getvalue()

    if isinstance(obj, bytes):
        return obj

    raise TypeError('Cannot convert {} to bytes'.format(type(obj)))


def to_base64(obj):
    """Convert an object to a :mod:`base64` representation of the image.

    Parameters
    ----------
    obj : :class:`bytes`, :class:`str`, :class:`OpenCVImage` or :class:`PIL.Image.Image`
        The object to convert to base64.

    Returns
    -------
    :class:`str`
        A :mod:`base64` representation of the image.
    """
    return base64.b64encode(to_bytes(obj)).decode('ascii')


def to_pil(obj):
    """Convert an object to a Pillow :class:`~PIL.Image.Image`.

    Parameters
    ----------
    obj : :class:`bytes`, :class:`str`, :class:`OpenCVImage` or :class:`PIL.Image.Image`
        The object to convert to a Pillow image.

    Returns
    -------
    :class:`PIL.Image.Image`
        The Pillow image.
    """
    if isinstance(obj, OpenCVImage):
        im = Image.fromarray(obj)
        im.format = obj.ext[1:].upper()
        return im

    if isinstance(obj, (str, bytes)):
        if isinstance(obj, bytes):
            image = Image.open(BytesIO(obj))
        else:
            try:
                image = Image.open(obj)
            except OSError:
                try:
                    buf = base64.b64decode(obj)
                except ValueError:
                    raise ValueError('Invalid path or base64 string, {!r}'.format(obj)) from None
                else:
                    image = Image.open(BytesIO(buf))

        if image.mode != 'RGB':
            converted = image.convert(mode='RGB')
            converted.format = image.format
            return converted

        return image

    if isinstance(obj, PillowImage):
        return obj

    raise TypeError('Cannot convert {} to a Pillow image'.format(type(obj)))


def to_cv2(obj):
    """Convert an object to an OpenCV image.

    Parameters
    ----------
    obj : :class:`bytes`, :class:`str`, :class:`numpy.ndarray` or :class:`PIL.Image.Image`
        The object to convert to an OpenCV image.

    Returns
    -------
    :class:`OpenCVImage`
        An OpenCV image.
    """
    def get_ext_from_bytes(buffer):
        for key, value in SIGNATURE_MAP.items():
            if buffer.startswith(value):
                return '.' + key
        return DEFAULT_FILE_EXTENSION

    if isinstance(obj, PillowImage):
        if obj.format is None:
            return OpenCVImage(np.asarray(obj))
        return OpenCVImage(np.asarray(obj), ext='.'+obj.format)

    if isinstance(obj, str):
        image = cv2.imread(obj)
        if image is None:
            try:
                buf = base64.b64decode(obj)
            except ValueError:
                raise ValueError('Invalid path or base64 string, {!r}'.format(obj)) from None
            arr = np.frombuffer(buf, dtype=np.uint8)
            image = cv2.imdecode(arr, flags=cv2.IMREAD_COLOR)
            ext = get_ext_from_bytes(buf)
        else:
            ext = splitext(obj)[1]
        array = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        return OpenCVImage(array, ext=ext)

    if isinstance(obj, bytes):
        arr = np.frombuffer(obj, dtype=np.uint8)
        image = cv2.imdecode(arr, flags=cv2.IMREAD_COLOR)
        array = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        ext = get_ext_from_bytes(obj)
        return OpenCVImage(array, ext=ext)

    if isinstance(obj, OpenCVImage):
        return obj

    if isinstance(obj, np.ndarray):
        return OpenCVImage(obj)

    raise TypeError('Cannot convert {} to an OpenCV image'.format(type(obj)))


def threshold(image, value):
    """Apply a threshold to an image.

    Parameters
    ----------
    image : :class:`OpenCVImage` or :class:`PIL.Image.Image`
        The image object.
    value : :class:`int`
        The threshold value.

    Returns
    -------
    The `image` with a threshold applied.
    """
    if isinstance(image, OpenCVImage):
        ret, out = cv2.threshold(image, value, 255, cv2.THRESH_BINARY)
        if not ret:
            raise RuntimeError('error in cv2.threshold')
        return OpenCVImage(out, ext=image.ext)

    if isinstance(image, PillowImage):
        out = image.point(lambda p: p > value and 255)
        out.format = image.format
        return out

    raise TypeError('Expect a Pillow or OpenCV image')


def erode(image, radius, iterations=1):
    """Apply erosion to an image.

    Parameters
    ----------
    image : :class:`OpenCVImage` or :class:`PIL.Image.Image`
        The image object.
    radius : :class:`int`
        The number of pixels to include in each direction. For example, if
        `radius`=1 then use 1 pixel in each direction from the central pixel,
        i.e., 9 pixels in total.
    iterations : :class:`int`, optional
        The number of times to apply erosion.

    Returns
    -------
    The `image` with erosion applied.
    """
    if radius is None or radius < 1 or iterations < 1:
        return image

    size = 2 * radius + 1
    if isinstance(image, OpenCVImage):
        kernel = np.ones((size, size), dtype=np.uint8)
        out = cv2.erode(image, kernel, iterations=iterations)
        return OpenCVImage(out, ext=image.ext)

    if isinstance(image, PillowImage):
        fmt = image.format
        for i in range(iterations):
            image = image.filter(ImageFilter.MinFilter(size=size))
        image.format = fmt
        return image

    raise TypeError('Expect a Pillow or OpenCV image')


def dilate(image, radius, iterations=1):
    """Apply dilation to an image.

    Parameters
    ----------
    image : :class:`OpenCVImage` or :class:`PIL.Image.Image`
        The image object.
    radius : :class:`int`
        The number of pixels to include in each direction. For example, if
        `radius`=1 then use 1 pixel in each direction from the central pixel,
        i.e., 9 pixels in total.
    iterations : :class:`int`, optional
        The number of times to apply dilation.

    Returns
    -------
    The `image` with dilation applied.
    """
    if radius is None or radius < 1 or iterations < 1:
        return image

    size = 2 * radius + 1
    if isinstance(image, OpenCVImage):
        kernel = np.ones((size, size), dtype=np.uint8)
        out = cv2.dilate(image, kernel, iterations=iterations)
        return OpenCVImage(out, ext=image.ext)

    if isinstance(image, PillowImage):
        fmt = image.format
        for i in range(iterations):
            image = image.filter(ImageFilter.MaxFilter(size=size))
        image.format = fmt
        return image

    raise TypeError('Expect a Pillow or OpenCV image')


def gaussian_blur(image, radius):
    """Apply a Gaussian blur to an image.

    Parameters
    ----------
    image : :class:`numpy.ndarray` or :class:`PIL.Image.Image`
        The image object.
    radius : :class:`int`
        The number of pixels to include in each direction. For example, if
        `radius`=1 then use 1 pixel in each direction from the central pixel,
        i.e., 9 pixels in total.

    Returns
    -------
    The `image` with a Gaussian blur applied.
    """
    if radius is None or radius < 1:
        return image

    if isinstance(image, OpenCVImage):
        size = 2 * radius + 1
        sigma = 0.3 * (radius - 1) + 0.8  # taken from the docstring of cv2.getGaussianKernel
        out = cv2.GaussianBlur(image, (size, size), sigmaX=sigma, sigmaY=sigma)
        return OpenCVImage(out, ext=image.ext)

    if isinstance(image, PillowImage):
        out = image.filter(ImageFilter.GaussianBlur(radius=radius))
        out.format = image.format
        return out

    raise TypeError('Expect a Pillow or OpenCV image')


def rotate(image, angle):
    """Rotate an image.

    Parameters
    ----------
    image : :class:`OpenCVImage` or :class:`PIL.Image.Image`
        The image object.
    angle : :class:`float`
        The angle, in degrees, to rotate the image. Can be between
        0 and 360 or -180 and 180.

    Returns
    -------
    The rotated image.
    """
    if angle is None or angle == 0:
        return image

    if angle < 0:
        angle += 360.

    if isinstance(image, OpenCVImage):
        # the following will expand the image size to fill the view

        # we also reuse this code to rotate a bounding box
        is_bounding_box = image.shape == (4,)

        # grab the dimensions of the image and then determine the center
        if is_bounding_box:
            x, y, w, h = image
        else:
            h, w = image.shape[:2]

        cx, cy = w * 0.5, h * 0.5

        # generate the rotation matrix
        matrix = cv2.getRotationMatrix2D((cx, cy), angle, 1.0)
        cos = abs(matrix[0, 0])
        sin = abs(matrix[0, 1])

        # find the new width and height bounds to expand the image
        new_w = int(h * sin + w * cos)
        new_h = int(h * cos + w * sin)

        # adjust the rotation matrix to take into account translation
        matrix[0, 2] += new_w * 0.5 - cx
        matrix[1, 2] += new_h * 0.5 - cy

        # perform the actual rotation and return the image/bounding box
        if is_bounding_box:
            return np.dot(matrix, [x, y, 1.0])
        out = cv2.warpAffine(image, matrix, (new_w, new_h))
        return OpenCVImage(out, ext=image.ext)

    if isinstance(image, PillowImage):
        out = image.rotate(angle, expand=True)
        out.format = image.format
        return out

    raise TypeError('Expect a Pillow or OpenCV image')


def zoom(image, x, y, w, h):
    """Zoom to a specific region in an image.

    Parameters
    ----------
    image : :class:`OpenCVImage` or :class:`PIL.Image.Image`
        The image object.
    x : :class:`int` or :class:`float`
        The x value of the top-left corner of the ROI.
        If a :class:`float` then a number between 0 and 1.
    y : :class:`int` or :class:`float`
        The y value of the top-left corner of the ROI.
        If a :class:`float` then a number between 0 and 1.
    w : :class:`int` or :class:`float`
        The width of the ROI. If a :class:`float` then a
        number between 0 and 1.
    h : :class:`int` or :class:`float`
        The height of the ROI. If a :class:`float` then a
        number between 0 and 1.

    Returns
    -------
    The region of interest.
    """
    if isinstance(image, OpenCVImage):
        height, width = image.shape[:2]
    elif isinstance(image, PillowImage):
        width, height = image.size
    else:
        raise TypeError('Expect a Pillow or OpenCV image')

    # rescale the input parameters if any of the parameters is a float
    if isinstance(x, float) or isinstance(y, float) or isinstance(w, float) or isinstance(h, float):
        x = int(width * x)
        y = int(height * y)
        w = int(width * w)
        h = int(height * h)

    if isinstance(image, OpenCVImage):
        return image[y:y+h, x:x+w]

    out = image.crop((x, y, x + w, y + h))
    out.format = image.format
    return out


def process(image, *, params=None, **ignored):
    """Perform image processing.

    Parameters
    ----------
    image : :class:`OpenCVImage` or :class:`PIL.Image.Image`
        The image to process.
    params : :class:`tuple`, optional
        The order to apply the transformations and the filters
        as (name, args/kwargs) pairs. For example::

        ('rotate', 90)
        ('threshold', 20)
        ('gaussian_blur', 5),
        ('zoom': (230, 195, 220, 60))
        ('zoom': {'x': 230, 'y': 195, 'w': 220, 'h': 60})
        ('dilate', (3, 4))
        ('dilate', {'radius': 3, 'iterations': 4})
        ('dilate', 3)
        ('erode', (4, 2))
        ('erode', {'radius': 4, 'iterations': 2})
        ('erode', 4)

    ignored
        All other keyword arguments are silently ignored.

    Returns
    -------
    The processed image.
    """
    if not params:
        return image

    for name, value in params:
        if name == 'zoom':
            if isinstance(value, dict):
                image = zoom(image, **value)
            else:
                image = zoom(image, *value)
        elif name == 'rotate':
            image = rotate(image, value)
        elif name == 'threshold':
            image = threshold(image, value)
        elif name == 'dilate':
            if isinstance(value, dict):
                image = dilate(image, **value)
            elif isinstance(value, (list, tuple)):
                image = dilate(image, *value)
            else:
                image = dilate(image, value)
        elif name == 'erode':
            if isinstance(value, dict):
                image = erode(image, **value)
            elif isinstance(value, (list, tuple)):
                image = erode(image, *value)
            else:
                image = erode(image, value)
        elif name == 'gaussian_blur':
            image = gaussian_blur(image, value)

    return image
