import os

from msl.network import (
    manager,
    ssh,
)

try:
    import pytesseract
except ImportError:
    pytesseract = None

from .client import OCRClient
from .service import OCRService
from .utils import save
from . import gui
from .ocr import (
    ocr,
    ssocr,
    tesseract,
)


def set_ssocr_path(path):
    """Set the path to the ``ssocr`` directory.

    Parameters
    ----------
    path : :class:`str`
        The path to the ``ssocr`` directory.
    """
    if os.path.isfile(path):  # only want the directory
        path = os.path.dirname(path)
    os.environ['PATH'] += os.pathsep + path


def set_tesseract_path(path):
    """Set the path to the ``Tesseract`` directory.

    Parameters
    ----------
    path : :class:`str`
        The path to the ``Tesseract`` directory.
    """
    if pytesseract is None:
        raise ImportError('You must install and configure tesseract and pytesseract')

    if os.path.isfile(path):
        pytesseract.pytesseract.tesseract_cmd = path
    else:
        os.environ['PATH'] += os.pathsep + path


def start_camera(*, host='raspberrypi', rpi_username='pi', rpi_password=None, timeout=10, **kwargs):
    """Connect to the :class:`OCRService` on the Raspberry Pi.

    Parameters
    ----------
    host : :class:`str`
        The hostname or IP address of the Raspberry Pi.
    rpi_username : :class:`str`
        The username for the Raspberry Pi.
    rpi_password : :class:`str`
        The password for `rpi_username`.
    timeout : :class:`float`
        The maximum number of seconds to wait for the connection.
    kwargs
        Keyword arguments that are passed to :func:`~msl.network.ssh.start_manager`

    Returns
    -------
    :class:`OCRClient`
        A connection to the Raspberry Pi.
    """
    console_script_path = '/home/{}/ocrenv/bin/ocr'.format(rpi_username)
    ssh.start_manager(host, console_script_path, ssh_username=rpi_username,
                      ssh_password=rpi_password, timeout=timeout, as_sudo=True, **kwargs)

    kwargs['host'] = host
    return OCRClient('OCRService', **kwargs)


def start_service_on_rpi():
    """Starts the Network :class:`~msl.network.manager.Manager` and the :class:`OCRService`.

    This function should only be called from the ``ocr`` console script (see setup.py).
    """
    kwargs = ssh.parse_console_script_kwargs()
    if kwargs.get('auth_login', False) and ('username' not in kwargs or 'password' not in kwargs):
        raise ValueError(
            'The Manager is using a login for authentication but the OCRService '
            'does not know the username and password to use to connect to the Manager'
        )

    manager.run_services(OCRService(), **kwargs)
