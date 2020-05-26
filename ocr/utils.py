"""
Utility functions for performing image conversion and image processing.
"""
import os
import sys
import base64
import logging
from io import BytesIO

import cv2
import numpy as np
from PIL import (
    Image,
    ImageFilter,
    ImageOps,
)
from PIL.Image import Image as PillowImage
from msl.qt.convert import to_qcolor

__all__ = (
    'adaptive_threshold',
    'crop',
    'dilate',
    'erode',
    'gaussian_blur',
    'greyscale',
    'invert',
    'rotate',
    'save',
    'threshold',
    'to_base64',
    'to_bytes',
    'to_cv2',
    'to_pil',
)

DEFAULT_IMAGE_FORMAT = 'jpeg'
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

    The `ext` attribute represents the file extension of
    the original image.
    """

    def __new__(cls, array, ext=None):
        obj = np.asarray(array).view(cls)
        obj.ext = ext or DEFAULT_FILE_EXTENSION
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        self.ext = getattr(obj, 'ext', DEFAULT_FILE_EXTENSION)

    @property
    def height(self):
        """The height of the image."""
        try:
            return self.shape[0]
        except IndexError:
            return 0

    @property
    def width(self):
        """The width of the image."""
        try:
            return self.shape[1]
        except IndexError:
            return 0

    def __str__(self):
        # mimic what PIL returns
        return '<OpenCVImage ext={} size={}x{} at {:#x}>'.format(self.ext, self.width, self.height, id(self))


def save(image, path, *, text='', font_face=cv2.FONT_HERSHEY_SIMPLEX,
         font_scale=2, thickness=3, foreground='black', background='white'):
    """Save an image to a file.

    This function will convert a greyscale image to a colour image.

    Parameters
    ----------
    image : :class:`str`, :class:`OpenCVImage` or :class:`PIL.Image.Image`
        The image to save. Can be a Base64 string or a file path (e.g., if
        you only wanted to convert an image to a new image format).
    path : :class:`str`
        A file path to save the image to. The image format is chosen based
        on the filename extension.
    text : :class:`str`, optional
        The text to draw at the top of the image (can contain the newline character).
    font_face : :class:`int`, optional
        The font to use. See
        `here <https://docs.opencv.org/4.3.0/d6/d6e/group__imgproc__draw.html#ga0f9314ea6e35f99bb23f29567fc16e11>`_
        for the enum options.
    font_scale : :class:`float`, optional
        The font scale factor that is multiplied by the font-specific base size.
    thickness : :class:`int`, optional
        Thickness of lines used to render the text.
    foreground
        The colour to draw the text. See :func:`~msl.qt.utils.to_qcolor` for
        the data types that are supported.
    background
        The colour the text is drawn on. See :func:`~msl.qt.utils.to_qcolor` for
        the data types that are supported.

    Returns
    -------
    :class:`OpenCVImage`
        The image with the text added.
    """
    img = to_cv2(image)
    if text:
        text_positions = []
        text_width, text_height = 0, 0
        for line in text.splitlines():
            (size_x, size_y), baseline = cv2.getTextSize(line, font_face, font_scale, thickness)
            text_width = max(text_width, size_x)
            text_height += int(size_y * 1.5)  # add some vertical padding
            text_positions.append((line, size_x, text_height - baseline//2))

        b = to_qcolor(background)
        bg = (b.red(), b.green(), b.blue())
        f = to_qcolor(foreground)
        fg = (f.red(), f.green(), f.blue())

        ext = img.ext
        image_height, image_width = img.shape[:2]
        if img.ndim == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

        new_width = max(image_width, text_width)
        new_height = image_height + text_height
        new_image = np.full((new_height, new_width, 3), bg, dtype=np.uint8)
        offset = (new_width - image_width)//2
        new_image[text_height:, offset:image_width+offset, :] = img

        for text, w, h in text_positions:
            bottom_left = ((new_image.shape[1] - w)//2, h)
            cv2.putText(new_image, text, bottom_left, font_face, font_scale, fg, thickness=thickness)

        img = OpenCVImage(new_image, ext=ext)

    cv2.imwrite(path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    logger.debug('image saved to {!r}'.format(path))
    return img


def get_executable_path(path, executable):
    """Get the full path to the OCR executable.

    Parameters
    ----------
    path : :class:`str`
        The full path to the executable or a top-level
        directory that contains the executable.
    executable : :class:`str`
        The name of the executable, e.g., ssocr or tesseract.

    Returns
    -------
    :class:`str`
        The full path to the executable.
    """
    # allows for specifying '~' in the path and de-references symbolic links
    path = os.path.realpath(os.path.expanduser(path))
    if sys.platform == 'win32' and not executable.endswith('.exe'):
        executable += '.exe'

    if os.path.isfile(path):
        if os.path.basename(path) != executable:
            raise FileNotFoundError('Invalid path to {!r}'.format(executable))
    elif os.path.isdir(path):
        found_it = False
        for root, _, _ in os.walk(path):
            url = os.path.join(root, executable)
            if os.path.isfile(url):
                path = url
                found_it = True
                break
        if not found_it:
            raise FileNotFoundError('Cannot find the {!r} executable'.format(executable))
    else:
        raise FileNotFoundError('The path is not a valid file or directory')

    return path


def to_bytes(obj):
    """Convert an object to the :class:`bytes` representation of the image.

    Parameters
    ----------
    obj
        The object to convert. Can be any of the following data types

        * :term:`bytes-like object`
        * :class:`str` (as a file path or a Base64 representation of an image)
        * :class:`OpenCVImage`
        * :class:`PIL.Image.Image`

    Returns
    -------
    :class:`bytes`
        The image as bytes.
    """
    if isinstance(obj, str):
        try:
            with open(obj, 'rb') as fp:
                data = fp.read()
            logger.debug('opened {!r} as bytes'.format(obj))
            return data
        except OSError:
            try:
                data = base64.b64decode(obj)
                logger.debug('converted Base64 to bytes')
                return data
            except ValueError:
                raise ValueError('Invalid path or Base64 string, {!r}'.format(obj)) from None

    if isinstance(obj, OpenCVImage):
        bgr_image = cv2.cvtColor(obj, code=cv2.COLOR_RGB2BGR)
        ret, buf = cv2.imencode(obj.ext, bgr_image)
        if not ret:
            raise RuntimeError('error calling cv2.imencode')
        logger.debug('converted {} to bytes'.format(obj.__class__.__name__))
        return buf.tobytes()

    if isinstance(obj, PillowImage):
        b = BytesIO()
        obj.save(b, obj.format)
        logger.debug('converted {} to bytes'.format(obj.__class__.__name__))
        return b.getvalue()

    if isinstance(obj, BytesIO):
        logger.debug('returned value of BytesIO object')
        return obj.getvalue()

    if isinstance(obj, memoryview):
        logger.debug('returned bytes from memoryview')
        return obj.tobytes()

    if isinstance(obj, bytearray):
        logger.debug('returned bytes from bytearray')
        return bytes(obj)

    if isinstance(obj, bytes):
        logger.debug('returned original bytes object')
        return obj

    raise TypeError('Cannot convert {} to bytes'.format(type(obj)))


def to_base64(obj):
    """Convert an object to the Base64 representation of the image.

    Parameters
    ----------
    obj
        The object to convert. See :func:`to_bytes` for more details.

    Returns
    -------
    :class:`str`
        The Base64 representation of the image.
    """
    b64 = base64.b64encode(to_bytes(obj)).decode('ascii')
    logger.debug('converted bytes to Base64')
    return b64


def to_pil(obj):
    """Convert an object to a Pillow :class:`~PIL.Image.Image`.

    Parameters
    ----------
    obj
        The object to convert. See :func:`to_bytes` for more details.

    Returns
    -------
    :class:`PIL.Image.Image`
        The Pillow image.
    """
    if isinstance(obj, OpenCVImage):
        im = Image.fromarray(obj)
        fmt = obj.ext[1:].upper()
        if fmt == 'JPG':
            fmt = 'JPEG'
        im.format = fmt
        logger.debug('converted {} to Pillow image'.format(obj.__class__.__name__))
        return im

    if isinstance(obj, BytesIO):
        image = Image.open(obj)
        logger.debug('converted BytesIO to Pillow image')
        return image

    if isinstance(obj, (bytes, memoryview, bytearray)):
        image = Image.open(BytesIO(obj))
        logger.debug('converted {} to Pillow image'.format(obj.__class__.__name__))
        return image

    if isinstance(obj, str):
        try:
            image = Image.open(obj)
            logger.debug('opened {!r} as a Pillow image'.format(obj))
        except OSError:
            try:
                buf = base64.b64decode(obj)
            except ValueError:
                raise ValueError('Invalid path or Base64 string, {!r}'.format(obj)) from None
            else:
                image = Image.open(BytesIO(buf))
                logger.debug('converted Base64 to Pillow image')
        return image

    if isinstance(obj, PillowImage):
        return obj

    raise TypeError('Cannot convert {} to a Pillow image'.format(type(obj)))


def to_cv2(obj):
    """Convert an object to an OpenCV image.

    Parameters
    ----------
    obj
        The object to convert. See :func:`to_bytes` for more details.

    Returns
    -------
    :class:`OpenCVImage`
        An OpenCV image.
    """
    # the OpenCVImage check must come before the np.ndarray check
    if isinstance(obj, OpenCVImage):
        return obj

    if isinstance(obj, (PillowImage, np.ndarray)):
        try:
            ext = '.' + obj.format
        except:
            ext = None
        img = OpenCVImage(np.asarray(obj), ext=ext)
        logger.debug('converted {} to OpenCVImage'.format(obj.__class__.__name__))
        return img

    if isinstance(obj, str):
        image = cv2.imread(obj, flags=cv2.IMREAD_UNCHANGED)
        if image is not None:
            _, ext = os.path.splitext(obj)
            if image.ndim > 2:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            logger.debug('opened {!r} as an OpenCVImage'.format(obj))
            return OpenCVImage(image, ext=ext)

        try:
            obj = base64.b64decode(obj)
            logger.debug('decode Base64 for OpenCVImage conversion')
        except ValueError:
            raise ValueError('Invalid path or Base64 string, {!r}'.format(obj)) from None

    if isinstance(obj, BytesIO):
        buffer = obj.getbuffer()
    else:
        buffer = obj

    try:
        arr = np.frombuffer(buffer, dtype=np.uint8)
    except TypeError:
        raise TypeError('Cannot convert {} to an OpenCV image'.format(type(obj))) from None

    if isinstance(buffer, memoryview):
        buffer = buffer[:10].tobytes()

    ext = None
    for key, value in SIGNATURE_MAP.items():
        if buffer.startswith(value):
            ext = '.' + key
            break

    image = cv2.imdecode(arr, flags=cv2.IMREAD_UNCHANGED)
    if image.ndim > 2:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    img = OpenCVImage(image, ext=ext)
    logger.debug('converted buffer to OpenCVImage')
    return img


def threshold(image, value):
    """Apply a threshold to an image.

    Parameters
    ----------
    image : :class:`OpenCVImage` or :class:`PIL.Image.Image`
        The image object.
    value : :class:`int`
        The threshold value, between 0 and 255.

    Returns
    -------
    The image with the threshold applied.
    """
    logger.debug('threshold value={}'.format(value))
    if isinstance(image, OpenCVImage):
        _, out = cv2.threshold(image, value, 255, cv2.THRESH_BINARY)
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
        radius=1 then use 1 pixel in each direction from the central pixel,
        i.e., 9 pixels in total.
    iterations : :class:`int`, optional
        The number of times to apply erosion.

    Returns
    -------
    The `image` with erosion applied.
    """
    logger.debug('erode radius={} iterations={}'.format(radius, iterations))
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
        radius=1 then use 1 pixel in each direction from the central pixel,
        i.e., 9 pixels in total.
    iterations : :class:`int`, optional
        The number of times to apply dilation.

    Returns
    -------
    The `image` with dilation applied.
    """
    logger.debug('dilate radius={} iterations={}'.format(radius, iterations))
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
    image : :class:`OpenCVImage` or :class:`PIL.Image.Image`
        The image object.
    radius : :class:`int`
        The number of pixels to include in each direction. For example, if
        radius=1 then use 1 pixel in each direction from the central pixel,
        i.e., 9 pixels in total.

    Returns
    -------
    The `image` with a Gaussian blur applied.
    """
    logger.debug('gaussian_blur radius={}'.format(radius))
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
    logger.debug('rotate angle={}'.format(angle))
    if angle is None or angle == 0:
        return image

    if angle < 0:
        angle += 360.

    if isinstance(image, np.ndarray):
        # the following will expand the image size to fill the view

        # we also reuse this code to rotate a corner of a bounding box
        # do not include that this in the docstring above since it's
        # not meant to be publicly known. See :func:`ocr.gui.rotate_image_corners`
        is_corner = not isinstance(image, OpenCVImage)

        # grab the dimensions of the image and then determine the center
        if is_corner:
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

        # perform the actual rotation and return the image or corner
        if is_corner:
            # the corner rotated, has shape (2,)
            return np.dot(matrix, [x, y, 1.0])
        out = cv2.warpAffine(image, matrix, (new_w, new_h))
        return OpenCVImage(out, ext=image.ext)

    if isinstance(image, PillowImage):
        out = image.rotate(angle, expand=True)
        out.format = image.format
        return out

    raise TypeError('Expect a Pillow or OpenCV image')


def crop(image, x, y, w, h):
    """Crop an image.

    Parameters
    ----------
    image : :class:`OpenCVImage` or :class:`PIL.Image.Image`
        The image object.
    x : :class:`int` or :class:`float`
        The x value of the top-left corner.
        If a :class:`float` then a number between 0 and 1.
    y : :class:`int` or :class:`float`
        The y value of the top-left corner.
        If a :class:`float` then a number between 0 and 1.
    w : :class:`int` or :class:`float`
        The width of the cropped region. If a :class:`float`
        then a number between 0 and 1.
    h : :class:`int` or :class:`float`
        The height of the cropped region. If a :class:`float`
        then a number between 0 and 1.

    Returns
    -------
    The cropped image.
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

    logger.debug('zoom x={} y={} w={} h={}'.format(x, y, w, h))

    if isinstance(image, OpenCVImage):
        return image[y:y+h, x:x+w]

    out = image.crop(box=(x, y, x + w, y + h))
    out.format = image.format
    return out


def greyscale(image):
    """Convert an image to greyscale.

    Parameters
    ----------
    image : :class:`OpenCVImage` or :class:`PIL.Image.Image`
        The image object.

    Returns
    -------
    The image converted to greyscale.
    """
    logger.debug('convert image to greyscale')
    if isinstance(image, OpenCVImage):
        if image.ndim == 2:
            return image
        converted = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        return OpenCVImage(converted, ext=image.ext)

    if isinstance(image, PillowImage):
        if image.mode == 'L':
            return image
        converted = ImageOps.grayscale(image)
        converted.format = image.format
        return converted

    raise TypeError('Expect a Pillow or OpenCV image')


def invert(image):
    """Invert an image.

    Parameters
    ----------
    image : :class:`OpenCVImage` or :class:`PIL.Image.Image`
        The image object.

    Returns
    -------
    The image inverted.
    """
    logger.debug('invert image')
    if isinstance(image, OpenCVImage):
        return OpenCVImage(~image, ext=image.ext)

    if isinstance(image, PillowImage):
        inverted = ImageOps.invert(image)
        inverted.format = image.format
        return inverted

    raise TypeError('Expect a Pillow or OpenCV image')


def adaptive_threshold(image, *, use_mean=True, radius=2, c=0):
    """Apply adaptive thresholding to an image.

    Parameters
    ----------
    image : :class:`OpenCVImage` or :class:`PIL.Image.Image`
        The image object. The image must be in greyscale, if it is not then
        it will first be converted to be.
    use_mean : :class:`bool`, optional
        Decides which adaptive thresholding algorithm to use. If :data:`True`
        then uses ``cv2.ADAPTIVE_THRESH_MEAN_C`` else uses
        ``cv2.ADAPTIVE_THRESH_GAUSSIAN_C``.
    radius : :class:`int`, optional
        Radius of the pixel neighborhood that is used to calculate a threshold
        value, e.g., radius=2 uses a 5x5 area.
    c : :class:`int`, optional
        A constant which is subtracted from the mean or weighted mean calculated.

    Returns
    -------
    The image with adaptive threshold applied.
    """
    logger.debug('adaptive threshold image')
    if isinstance(image, OpenCVImage):
        if image.ndim > 2:
            image = greyscale(image)
        method = cv2.ADAPTIVE_THRESH_MEAN_C if use_mean else cv2.ADAPTIVE_THRESH_GAUSSIAN_C
        size = 2 * radius + 1
        img = cv2.adaptiveThreshold(image, 255, method, cv2.THRESH_BINARY, size, c)
        return OpenCVImage(img, ext=image.ext)

    if isinstance(image, PillowImage):
        return to_pil(adaptive_threshold(to_cv2(image)))

    raise TypeError('Expect a Pillow or OpenCV image')
