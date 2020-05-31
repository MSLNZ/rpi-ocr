"""
Optical Character Recognition with a Raspberry Pi.
"""
import re
import sys
import platform
from collections import (
    OrderedDict,
    namedtuple,
)

from msl.network import ssh

from .utils import *
from . import ssocr
from . import tesseract
from .ssocr import set_ssocr_path
from .tesseract import set_tesseract_path
from .camera import (
    Camera,
    RemoteCamera,
    kill_camera_service,
)
from .service import kill_ocr_service

__author__ = 'Measurement Standards Laboratory of New Zealand'
__copyright__ = '\xa9 2020, ' + __author__
__version__ = '0.1.0.dev0'

_v = re.search(r'(\d+)\.(\d+)\.(\d+)[.-]?(.*)', __version__).groups()

version_info = namedtuple('version_info', 'major minor micro releaselevel')(int(_v[0]), int(_v[1]), int(_v[2]), _v[3])
""":obj:`~collections.namedtuple`: Contains the version information as a (major, minor, micro, releaselevel) tuple."""

# if you change the name of the virtual environment then you must also change
# the name of the virtual environment that is defined in rpi-setup.sh
CAMERA_EXE_PATH = 'ocrenv/bin/camera'
OCR_EXE_PATH = 'ocrenv/bin/ocr'

ON_RPI = platform.machine().startswith('arm')

ALGORITHMS = {
    'tesseract': tesseract.apply,
    'ssocr': ssocr.apply,
}


def camera(**kwargs):
    """Connect to a camera on a Raspberry Pi.

    If you call this function from a script running on a Raspberry Pi then
    a :class:`~ocr.connection.Camera` object is returned and all keyword
    arguments are passed to :class:`~ocr.camera.Camera`.

    Otherwise a Network :class:`~msl.network.manager.Manager` is started on the
    Raspberry Pi to run the :class:`~ocr.camera.Camera` service. In this situation
    the keyword arguments are as follows,

    * host :class:`str` : The hostname or IP address of the Raspberry Pi [default='raspberrypi'].
    * rpi_username :class:`str` : The username for the Raspberry Pi [default='pi'].
    * rpi_password :class:`str` : The password for `rpi_username`. [default is to prompt user]
    * All additional keyword arguments are passed to the :class:`~ocr.camera.Camera` class
      or to the :func:`~msl.network.ssh.start_manager` function.

    Returns
    -------
    :class:`~ocr.camera.Camera` or :class:`~ocr.camera.RemoteCamera`
        The connection to the camera.
    """
    if ON_RPI:
        utils.logger.debug('connecting to a local camera ...')
        return Camera(**kwargs)

    host = kwargs.pop('host', 'raspberrypi')
    rpi_username = kwargs.pop('rpi_username', 'pi')
    rpi_password = kwargs.pop('rpi_password', None)

    utils.logger.debug('connecting to a camera at {} ...'.format(host))

    console_script_path = '/home/{}/{}'.format(rpi_username, CAMERA_EXE_PATH)
    ssh.start_manager(host, console_script_path, ssh_username=rpi_username,
                      ssh_password=rpi_password, as_sudo=True, **kwargs)

    return RemoteCamera(host=host, **kwargs)


def service(host='raspberrypi', rpi_username='pi', rpi_password=None, **kwargs):
    """Start the Network :class:`~msl.network.manager.Manager` and the
    :class:`~ocr.service.OCR` service on a Raspberry Pi to apply OCR.

    Parameters
    ----------
    host : :class:`str`, optional
        The hostname or IP address of the Raspberry Pi.
    rpi_username : :class:`str`, optional
        The username for the Raspberry Pi.
    rpi_password : :class:`str`, optional
        The password for `rpi_username`.
    kwargs
        All additional keyword arguments are passed to the
        :func:`~msl.network.ssh.start_manager` function.

    Returns
    -------
    :class:`~ocr.service.RemoteOCR`
        The connection to the :class:`~ocr.service.OCR` service on the Raspberry Pi.
    """
    from .service import RemoteOCR
    utils.logger.debug('connecting to the OCR service at {} ...'.format(host))

    console_script_path = '/home/{}/{}'.format(rpi_username, OCR_EXE_PATH)
    ssh.start_manager(host, console_script_path, ssh_username=rpi_username,
                      ssh_password=rpi_password, as_sudo=True, **kwargs)

    return RemoteOCR(host=host, **kwargs)


def configure(config=None):
    """Create a Qt application to interact with the image and the OCR algorithm.

    Parameters
    ----------
    config : :class:`str` or :class:`dict`, optional
        The path to a JSON configuration file to load
        or an already-loaded configuration file.

    Returns
    -------
    :class:`dict`
        The OCR parameters that can be passed to :func:`.apply`.
    """
    from msl.qt import application, excepthook
    from .gui import Configure
    sys.excepthook = excepthook
    app = application()
    gui = Configure(config=config)
    gui.show()
    app.exec()
    return gui.ocr_params


def apply(obj, *, tasks=None, algorithm='tesseract', **kwargs):
    """Apply the OCR algorithm to an image.

    Parameters
    ----------
    obj : :class:`str`, :class:`~ocr.camera.Camera` or :class:`~ocr.camera.RemoteCamera`
        An image to perform OCR on. If a :class:`str` then a file path. Otherwise the image
        is captured using the camera.
    tasks : :class:`list` of :class:`tuple` or :class:`dict`, optional
        The image-processing tasks to apply to `image` before calling the
        OCR algorithm. The value is passed to the :func:`.process` function.
    algorithm : :class:`str`, optional
        The OCR algorithm to use: ``tesseract`` or ``ssocr``.
    kwargs
        All additional keyword arguments are passed to the specified OCR algorithm,
        :func:`ocr.tesseract.apply` or :func:`ocr.ssocr.apply`.

    Returns
    -------
    :class:`str`
        The OCR text.
    :class:`~ocr.utils.OpenCVImage`
        The original (unprocessed) image.
    """
    if isinstance(obj, RemoteCamera):
        if (algorithm == 'tesseract' and tesseract.is_available) or \
                (algorithm == 'ssocr' and ssocr.is_available):
            obj = obj.capture()
        else:
            text, image = obj.capture_apply(tasks=tasks, algorithm=algorithm, **kwargs)
            return text, to_cv2(image)
    elif isinstance(obj, Camera):
        obj = obj.capture()

    image = utils.to_cv2(obj)
    processed = process(image, tasks=tasks)
    text = ALGORITHMS[algorithm](processed, **kwargs)
    return text, image


def process(image, tasks=None):
    """Perform image-processing tasks.

    Parameters
    ----------
    image : :class:`~ocr.utils.OpenCVImage` or :class:`PIL.Image.Image`
        The image to process.
    tasks : :class:`list` of :class:`tuple` or :class:`dict`, optional
        Apply the transformations and the filters to the image. The
        object is a sequence of `name`, `value` pairs. The `name` parameter
        is the name of the transformation or filter (e.g., erode, rotate) and the
        `value` can be a number, a sequence of numbers or a dictionary, for example,

        * [('dilate', (3, 4))] apply dilation with a radius of 3 and using 4 iterations
        * [('dilate', {'radius': 3, 'iterations': 4})]
        * [('dilate', 3)] apply dilation with a radius of 3 and use the default number of iterations
        * [('rotate', 90), ('dilate', 3)] specify multiple tasks, first rotate then dilate
        * [('rotate', 180), ('greyscale',)] greyscale does not accept arguments
        * {'rotate': 90, 'dilate': 3} using a dict instead of a list of tuple

    Returns
    -------
    :class:`~ocr.utils.OpenCVImage` or :class:`PIL.Image.Image`
        The processed image.
    """
    if not tasks:
        return image

    utils.logger.info('process tasks {}'.format(tasks))

    if isinstance(tasks, dict):
        if sys.version_info[:2] < (3, 6) and not isinstance(tasks, OrderedDict):
            # PEP 468 -- Preserving the order of **kwargs in a function.
            raise TypeError('Cannot use a dict in Python <3.6 since the order is not preserved')
        items = tasks.items()
    else:
        items = tasks

    for item in items:
        if len(item) == 1:
            name, value = item[0], None
        else:
            name, value = item

        obj = getattr(utils, name)
        if isinstance(value, (list, tuple)):
            image = obj(image, *value)
        elif isinstance(value, dict):
            image = obj(image, **value)
        elif value is None:
            image = obj(image)
        else:
            image = obj(image, value)

    return image
