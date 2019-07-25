"""
Utility functions for performing image conversion and image processing.
"""
import base64
from io import BytesIO

import cv2
import numpy as np
from PIL import (
    Image,
    ImageFilter,
)

DEFAULT_IMAGE_FORMAT = 'jpeg'


def save(image, filename, params=None):
    """Save the image.

    Parameters
    ----------
    image : :class:`str`, :class:`numpy.ndarray` or :class:`Image.Image`
        The image to save.
    filename : :class:`str`
        The name to use to save the image file. The image format is chosen
        based on the `filename` extension.
    params : :class:`tuple`, optional
        Format-specific parameters encoded as pairs (paramId_1, paramValue_1, paramId_2, paramValue_2, ... .)
        See :func:`cv2.imwrite` for more details.
    """
    img = cv2.cvtColor(to_cv2(image), cv2.COLOR_RGB2BGR)
    cv2.imwrite(filename, img, params=params)


def to_base64(obj):
    """Convert an object to a :mod:`base64` representation of the image.

    Parameters
    ----------
    obj : :class:`str`, :class:`numpy.ndarray` or :class:`Image.Image`
        The object to convert to :mod:`base64`. Can be the name of a
        file to open.

    Returns
    -------
    :class:`str`
        A :mod:`base64` representation of the image.
    """
    if isinstance(obj, str):
        try:
            with open(obj, 'rb') as fp:
                byte_buffer = fp.read()
        except OSError:  # assume img is already a base64 string
            return obj

    elif isinstance(obj, np.ndarray):
        bgr_image = cv2.cvtColor(obj, code=cv2.COLOR_RGB2BGR)
        _, byte_buffer = cv2.imencode('.'+DEFAULT_IMAGE_FORMAT, bgr_image)

    elif isinstance(obj, Image.Image):
        b = BytesIO()
        obj.save(b, DEFAULT_IMAGE_FORMAT)
        byte_buffer = b.getvalue()

    else:
        raise TypeError('Cannot convert {!r} to a base64 string'.format(obj))

    return base64.b64encode(byte_buffer).decode('utf-8')


def to_pil(obj):
    """Convert an object to a PIL :class:`Image.Image`.

    Parameters
    ----------
    obj : :class:`str`, :class:`numpy.ndarray` or :class:`Image.Image`
        The object to convert to an :class:`Image.Image`.

    Returns
    -------
    :class:`Image.Image`
        A PIL :class:`Image.Image`.
    """
    if isinstance(obj, Image.Image):
        return obj

    if isinstance(obj, np.ndarray):
        return Image.fromarray(obj)

    if isinstance(obj, str):
        try:
            image = Image.open(obj)
        except OSError:
            image = Image.open(BytesIO(base64.b64decode(obj)))

        if image.mode != 'RGB':
            return image.convert('RGB')
        return image

    raise TypeError('Cannot convert {!r} to a PIL Image'.format(obj))


def to_cv2(obj):
    """Convert an object to an OpenCV image.

    Parameters
    ----------
    obj : :class:`str`, :class:`numpy.ndarray` or :class:`Image.Image`
        The object to convert to an OpenCV image.

    Returns
    -------
    :class:`numpy.ndarray`
        An OpenCV image.
    """
    if isinstance(obj, np.ndarray):
        return obj

    if isinstance(obj, Image.Image):
        return np.array(obj)

    if isinstance(obj, str):
        image = cv2.imread(obj)
        if image is None:
            arr = np.frombuffer(base64.b64decode(obj), dtype=np.uint8)
            image = cv2.imdecode(arr, flags=cv2.IMREAD_COLOR)
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    raise TypeError('Cannot convert {!r} to an OpenCV image'.format(obj))


def threshold(image, value):
    """Apply a threshold to an image.

    Parameters
    ----------
    image : :class:`numpy.ndarray` or :class:`Image.Image`
        The image object.
    value : :class:`int`
        The threshold value.

    Returns
    -------
    The `image` with a threshold applied.
    """
    if isinstance(image, np.ndarray):
        return cv2.threshold(image, value, 255, cv2.THRESH_BINARY)[1]
    elif isinstance(image, Image.Image):
        return image.point(lambda p: p > value and 255)
    else:
        raise TypeError('Expect a PIL or OpenCV image')


def erode(image, radius, iterations=1):
    """Apply erosion to an image.

    Parameters
    ----------
    image : :class:`numpy.ndarray` or :class:`Image.Image`
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
    if isinstance(image, np.ndarray):
        kernel = np.ones((size, size), dtype=np.uint8)
        return cv2.erode(image, kernel, iterations=iterations)
    elif isinstance(image, Image.Image):
        for i in range(iterations):
            image = image.filter(ImageFilter.MinFilter(size=size))
        return image
    else:
        raise TypeError('Expect a PIL or OpenCV image')


def dilate(image, radius, iterations=1):
    """Apply dilation to an image.

    Parameters
    ----------
    image : :class:`numpy.ndarray` or :class:`Image.Image`
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
    if isinstance(image, np.ndarray):
        kernel = np.ones((size, size), dtype=np.uint8)
        return cv2.dilate(image, kernel, iterations=iterations)
    elif isinstance(image, Image.Image):
        for i in range(iterations):
            image = image.filter(ImageFilter.MaxFilter(size=size))
        return image
    else:
        raise TypeError('Expect a PIL or OpenCV image')


def gaussian_blur(image, radius):
    """Apply a Gaussian blur to an image.

    Parameters
    ----------
    image : :class:`numpy.ndarray` or :class:`Image.Image`
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
    if isinstance(image, np.ndarray):
        size = 2 * radius + 1
        sigma = 0.3 * (radius - 1) + 0.8  # taken from the docstring of cv2.getGaussianKernel
        return cv2.GaussianBlur(image, (size, size), sigmaX=sigma, sigmaY=sigma)
    elif isinstance(image, Image.Image):
        return image.filter(ImageFilter.GaussianBlur(radius=radius))
    else:
        raise TypeError('Expect a PIL or OpenCV image')


def rotate(image, angle):
    """Rotate an image.

    Parameters
    ----------
    image : :class:`numpy.ndarray` or :class:`Image.Image`
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

    if isinstance(image, np.ndarray):
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
        return cv2.warpAffine(image, matrix, (new_w, new_h))

    elif isinstance(image, Image.Image):
        return image.rotate(angle, expand=True)

    else:
        raise TypeError('Expect a PIL or OpenCV image')


def zoom(image, x, y, w, h):
    """Zoom to a specific region in an image.

    Parameters
    ----------
    image : :class:`numpy.ndarray` or :class:`Image.Image`
        The image object.
    x : :class:`int` or :class:`float`
        The x value of the top-left corner of the ROI.
        If a :class:`float then a number between 0 and 1.
    y : :class:`int` or :class:`float`
        The y value of the top-left corner of the ROI.
        If a :class:`float then a number between 0 and 1.
    w : :class:`int` or :class:`float`
        The width of the ROI. If a :class:`float then a
        number between 0 and 1.
    h : :class:`int` or :class:`float`
        The height of the ROI. If a :class:`float then a
        number between 0 and 1.

    Returns
    -------
    The region of interest.
    """
    if isinstance(image, np.ndarray):
        height, width = image.shape[:2]
    elif isinstance(image, Image.Image):
        width, height = image.size
    else:
        raise TypeError('Expect a PIL or OpenCV image')

    # rescale the input parameters if any of the parameters is a float
    if isinstance(x, float) or isinstance(y, float) or isinstance(w, float) or isinstance(h, float):
        x = int(width * x)
        y = int(height * y)
        w = int(width * w)
        h = int(height * h)

    if isinstance(image, np.ndarray):
        return image[y:y+h, x:x+w]
    else:
        return image.crop((x, y, x+w, y+h))
