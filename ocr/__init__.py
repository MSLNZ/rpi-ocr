"""
Optical Character Recognition with a Raspberry Pi.
"""
import platform

from msl.network import (
    manager,
    ssh,
)

# if you change this value then you must also update the name of the
# virtual environment that is created in rpi-setup.sh
RPI_EXE_PATH = 'ocrenv/bin/ocr'

ON_RPI = platform.machine().startswith('arm')


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
    console_script_path = '/home/{}/{}'.format(rpi_username, RPI_EXE_PATH)
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


def kill_manager(*, host='raspberrypi', rpi_username='pi', rpi_password=None, timeout=10, **kwargs):
    """Kill the Network :class:`~msl.network.manager.Manager` on the Raspberry Pi.

    Parameters
    ----------
    host : :class:`str`, optional
        The hostname or IP address of the Raspberry Pi.
    rpi_username : :class:`str`, optional
        The username for the Raspberry Pi.
    rpi_password : :class:`str`, optional
        The password for `rpi_username`.
    timeout : :class:`float`, optional
        The maximum number of seconds to wait for the connection.
    kwargs
        Keyword arguments that are passed to :meth:`~paramiko.client.SSHClient.connect`.
    """
    ssh_client = ssh.connect(host, username=rpi_username, password=rpi_password, timeout=timeout, **kwargs)
    lines = ssh.exec_command(ssh_client, 'ps aux | grep ocr')
    pids = [line.split()[1] for line in lines if RPI_EXE_PATH in line]
    for pid in pids:
        try:
            ssh.exec_command(ssh_client, 'sudo kill -9 ' + pid)
        except:
            pass
    ssh_client.close()


def ocr(image, *, algorithm='tesseract', **parameters):
    """Perform OCR on an image.

    Parameters
    ----------
    image : :class:`str`, :class:`numpy.ndarray` or :class:`Image.Image`
        The image to perform OCR on.
    algorithm : :class:`str`, optional
        The OCR algorithm to use: ``tesseract`` or ``ssocr``.
    parameters
        Keyword arguments that are passed to :func:`.process` and to
        the OCR algorithm.

    Returns
    -------
    :class:`str`
        The OCR text.
    :class:`~.utils.OpenCVImage` or :class:`PIL.Image.Image`
        The processed image.
    """
    img = process(image, **parameters)

    if algorithm == 'tesseract':
        text = tesseract(img, **parameters)
    elif algorithm == 'ssocr':
        text = ssocr(img, **parameters)
    else:
        raise ValueError('Invalid algorithm {!r} to use for OCR'.format(algorithm))

    return text, img


from . import gui
from .client import OCRClient
from .service import OCRService
from .utils import (
    save,
    process,
)
from .ssocr import (
    ssocr,
    set_ssocr_path,
)
from .tesseract import (
    tesseract,
    set_tesseract_path,
)
