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

__author__ = 'Measurement Standards Laboratory of New Zealand'
__copyright__ = '\xa9 2020, ' + __author__
__version__ = '0.1.0.dev0'

_v = re.search(r'(\d+)\.(\d+)\.(\d+)[.-]?(.*)', __version__).groups()

version_info = namedtuple('version_info', 'major minor micro releaselevel')(int(_v[0]), int(_v[1]), int(_v[2]), _v[3])
""":obj:`~collections.namedtuple`: Contains the version information as a (major, minor, micro, releaselevel) tuple."""


# if you change this value then you must also update the name of the
# virtual environment that is created in rpi-setup.sh
RPI_EXE_PATH = 'ocrenv/bin/ocr'

ON_RPI = platform.machine().startswith('arm')


def camera(**kwargs):
    """Create a connection to a camera.

    If you call this function from a script running on a Raspberry Pi then
    a :class:`~ocr.connection.Camera` object is returned and all keyword
    arguments are passed to :class:`~picamera.PiCamera`.

    Otherwise a :class:`~ocr.connection.RemoteCamera` object is returned
    and the keyword arguments are as follows,

    * host :class:`str` : The hostname or IP address of the Raspberry Pi [default='raspberrypi'].
    * rpi_username :class:`str` : The username for the Raspberry Pi [default='pi'].
    * rpi_password :class:`str` : The password for `rpi_username`. [default is to prompt user]
    * All additional keyword arguments are passed to the :class:`~picamera.PiCamera` class
      or to the :func:`~msl.network.ssh.start_manager` function.

    Returns
    -------
    :class:`~ocr.connection.Camera` or :class:`~ocr.connection.RemoteCamera`
        The connection to the camera.
    """
    if ON_RPI:
        from .connection import Camera
        utils.logger.debug('connecting to a local camera ...')
        return Camera(**kwargs)

    utils.logger.debug('connecting to a camera on a Raspberry Pi ...')

    host = kwargs.pop('host', 'raspberrypi')
    rpi_username = kwargs.pop('rpi_username', 'pi')
    rpi_password = kwargs.pop('rpi_password', None)

    console_script_path = '/home/{}/{}'.format(rpi_username, RPI_EXE_PATH)
    ssh.start_manager(host, console_script_path, ssh_username=rpi_username,
                      ssh_password=rpi_password, as_sudo=True, **kwargs)

    from .connection import RemoteCamera
    return RemoteCamera(host=host, **kwargs)


def kill_camera_service(*, host='raspberrypi', rpi_username='pi', rpi_password=None, **ignored):
    """Kill the :class:`~ocr.connection.Camera` service on the Raspberry Pi.

    Parameters
    ----------
    host : :class:`str`, optional
        The hostname or IP address of the Raspberry Pi.
    rpi_username : :class:`str`, optional
        The username for the Raspberry Pi.
    rpi_password : :class:`str`, optional
        The password for `rpi_username`.
    ignored
        All additional keyword arguments are silently ignored.
    """
    ssh_client = ssh.connect(host, username=rpi_username, password=rpi_password)
    lines = ssh.exec_command(ssh_client, 'ps aux | grep ocr')
    pids = [line.split()[1] for line in lines if RPI_EXE_PATH in line]
    for pid in pids:
        try:
            utils.logger.debug('killing pid={} on the Raspberry Pi'.format(pid))
            ssh.exec_command(ssh_client, 'sudo kill -9 ' + pid)
        except Exception as e:
            utils.logger.error(e)
    ssh_client.close()


def configure(connection, **kwargs):
    """Create a Qt application to interact with the image and the OCR algorithm.

    Parameters
    ----------
    connection : :class:`~ocr.connection.Camera` or :class:`~ocr.connection.RemoteCamera`
        The connection to the camera. See :func:`camera`.
    kwargs
        Describe...

    Returns
    -------
    :class:`dict`
        The OCR parameters.
    """
    from msl.qt import application, excepthook
    from .gui import Gui
    sys.excepthook = excepthook
    app = application()
    gui = Gui(connection, **kwargs)
    gui.show()
    app.exec()
    return gui.ocr_params


def ocr(image, *, tasks=None, algorithm='tesseract', **kwargs):
    """Perform OCR on an image.

    Parameters
    ----------
    image : :class:`str`, :class:`~ocr.utils.OpenCVImage` or :class:`PIL.Image.Image`
        The image to perform OCR on. If a :class:`str` then a file path or a
        base64 representation of the image.
    tasks : :class:`list` of :class:`tuple` or :class:`dict`, optional
        The image-processing tasks to apply to `image` before calling the
        OCR algorithm. The value is passed to the :func:`.process` function.
    algorithm : :class:`str`, optional
        The OCR algorithm to use: ``tesseract`` or ``ssocr``.
    kwargs
        All additional keyword arguments are passed to the specified OCR algorithm,
        :func:`~ocr.tesseract.tesseract` or :func:`~ocr.ssocr.ssocr`.

    Returns
    -------
    :class:`str`
        The OCR text.
    :class:`~ocr.utils.OpenCVImage` or :class:`PIL.Image.Image`
        The processed image.
    """
    if isinstance(image, str):
        image = utils.to_cv2(image)
    img = process(image, tasks=tasks)

    if algorithm == 'tesseract':
        text = tesseract(img, **kwargs)
    elif algorithm == 'ssocr':
        text = ssocr(img, **kwargs)
    else:
        raise ValueError('Invalid algorithm {!r} to use for OCR'.format(algorithm))

    return text, img


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


from .utils import *
from .ssocr import (
    ssocr,
    set_ssocr_path,
)
from .tesseract import (
    tesseract,
    set_tesseract_path,
)
