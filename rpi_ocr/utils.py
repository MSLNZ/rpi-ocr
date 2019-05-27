import base64
from io import BytesIO
import cv2
import numpy as np
from PIL import Image


DEFAULT_IMAGE_FORMAT = '.jpeg'


def save_as_jpeg(image, filename):
    """Saves the image.

    Parameters
    ----------
    image : str or np.ndarray or Image.Image
        The image to save.
    filename : str
        The name of the image file.
    """
    if (filename[-4:]).lower() != 'jpeg':
        filename += '.jpeg'
    to_pil(image).save(filename, format='jpeg')


def to_base64(obj):
    """Convert an object to an image as a base64 string.

    Parameters
    ----------
    obj : :class:`str`, :class:`numpy.ndarray` or :class:`Image.Image`
        The object to convert to base64.

    Returns
    -------
    :class:`str`
        A :mod:`base64` representation of the image.
    """
    if isinstance(obj, str):
        try:
            with open(obj, 'rb') as fp:
                byte_buffer = fp.read()
        except OSError:
            # assume img is already a base64 string
            return obj

    elif isinstance(obj, np.ndarray):
        bgr_image = cv2.cvtColor(obj, code=cv2.COLOR_RGB2BGR)
        _, byte_buffer = cv2.imencode(DEFAULT_IMAGE_FORMAT, bgr_image)

    elif isinstance(obj, Image.Image):
        b = BytesIO()
        obj.save(b, DEFAULT_IMAGE_FORMAT[1:])
        byte_buffer = b.getvalue()

    else:
        raise TypeError('Cannot convert {!r} to a base64 string'.format(type(obj)))

    return base64.b64encode(byte_buffer).decode()


def to_pil(obj):
    """Convert an object to a pillow :class:`Image.Image`.

    Parameters
    ----------
    obj : :class:`str`, :class:`numpy.ndarray` or :class:`Image.Image`
        The object to convert to a :class:`Image.Image`.

    Returns
    -------
    :class:`Image.Image`
        The pillow :class:`Image.Image`.
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

    raise TypeError('Cannot convert {!r} to a PIL.Image'.format(type(obj)))


def to_cv2(obj):
    """Convert an object to an opencv image.

    Parameters
    ----------
    obj : :class:`str`, :class:`numpy.ndarray` or :class:`Image.Image`
        The object to convert to an opencv image.

    Returns
    -------
    :class:`numpy.ndarray`
        The opencv image.
    """
    if isinstance(obj, np.ndarray):
        return obj

    if isinstance(obj, Image.Image):
        return np.array(obj)

    if isinstance(obj, str):
        image = cv2.imread(obj)
        if image is None:
            # arr = np.fromstring(base64.b64decode(obj), np.uint8)
            arr = np.frombuffer(base64.b64decode(obj), np.uint8)
            image = cv2.imdecode(arr, flags=cv2.IMREAD_COLOR)
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    raise TypeError('Cannot convert {!r} to an opencv image'.format(type(obj)))
