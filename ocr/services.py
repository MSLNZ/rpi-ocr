"""
Apply OCR on a Raspberry Pi.
"""
from time import perf_counter

from msl.network import (
    ssh,
    manager,
    Service,
    LinkedClient,
)

from .utils import (
    to_base64,
    to_cv2,
    logger,
)
from . import tesseract
from . import ssocr


class OCR(Service):

    def __init__(self):
        """Allow for OCR to be applied from a remote computer."""
        super(OCR, self).__init__()

        self._tesseract_languages = tesseract.languages()
        self._tesseract_version = tesseract.version()
        self._ssocr_version = ssocr.version()

        from . import apply, process
        self._apply = apply
        self._process = process

    def ssocr_version(self):
        """Get the version information of ssocr.

        Returns
        -------
        :class:`str`
            The version of ssocr.
        """
        return self._ssocr_version

    def tesseract_info(self):
        """Get the languages and version information of Tesseract-OCR.

        Returns
        -------
        :class:`list` of :class:`str`
            The languages that are available to Tesseract-OCR.
        :class:`str`
            The version of Tesseract-OCR.
        """
        return self._tesseract_languages, self._tesseract_version

    def apply(self, image, *, tasks=None, algorithm='tesseract', **kwargs):
        """Apply the OCR algorithm to an image.

        Parameters
        ----------
        image : :class:`str`
            The :mod:`base64` representation of the image to apply OCR to.
        tasks : :class:`list` of :class:`tuple` or :class:`dict`, optional
            The image-processing tasks to apply to `image` before calling the
            OCR algorithm. The value is passed to the :func:`~ocr.process` function.
        algorithm : :class:`str`, optional
            The OCR algorithm to use.
        kwargs
            All additional keyword arguments are passed to the specified OCR algorithm.

        Returns
        -------
        :class:`str`
            The OCR text.
        :class:`str`
            The :mod:`base64` representation of the processed image.
        """
        processed = self._process(to_cv2(image), tasks=tasks)
        text, _ = self._apply(processed, algorithm=algorithm, **kwargs)
        return text, to_base64(processed)

    def shutdown_service(self):
        """Allows for this :class:`~msl.network.service.Service` to be shut down remotely."""
        pass


class RemoteOCR(LinkedClient):

    def __init__(self, **kwargs):
        """Connect to the :class:`.OCR` service on a Raspberry Pi.

        Parameters
        ----------
        kwargs
            All keyword arguments are passed to :func:`~msl.network.client.connect`.
        """
        super(RemoteOCR, self).__init__('OCR', **kwargs)
        logger.debug('connected to the %s service running on %s', self.service_name, self.service_os)

    def apply(self, image, *, tasks=None, algorithm='tesseract', **kwargs):
        """Apply the OCR algorithm to an image.

        Parameters
        ----------
        image
            The image to apply OCR to.
        tasks : :class:`list` of :class:`tuple` or :class:`dict`, optional
            The image-processing tasks to apply to `image` before calling the
            OCR algorithm. The value is passed to the :func:`~ocr.process` function.
        algorithm : :class:`str`, optional
            The OCR algorithm to use.
        kwargs
            All additional keyword arguments are passed to the specified OCR algorithm.

        Returns
        -------
        :class:`str`
            The OCR text.
        :class:`~ocr.utils.OpenCVImage`
            The processed image.
        """
        t0 = perf_counter()
        text, image = self._link.apply(to_base64(image), tasks=tasks, algorithm=algorithm, **kwargs)
        dt = perf_counter() - t0
        logger.info('RemoteOCR.apply took %.3f seconds', dt)
        return text, to_cv2(image)

    def disconnect(self):
        """Disconnect from and shut down the :class:`.OCR` service."""
        self.shutdown_service()
        super(RemoteOCR, self).disconnect()
        logger.debug('disconnected from the %s service', self.service_name)


def start():
    """Starts the :class:`~ocr.cameras.Camera` and :class:`.OCR` services on the Raspberry Pi.

    This function should only be called from the ``ocr`` console script *(see setup.py)*.
    """
    kwargs = ssh.parse_console_script_kwargs()
    if kwargs.get('auth_login', False) and ('username' not in kwargs or 'password' not in kwargs):
        raise ValueError(
            'The Manager is using a login for authentication but the OCR service '
            'does not know the username and password to use to connect to the Manager'
        )

    manager.run_services(OCR(), **kwargs)


def kill_ocr_service(*, host='raspberrypi', rpi_username='pi', rpi_password=None, **ignored):
    """Kill the :class:`.OCR` service and shut down the Network :class:`~msl.network.manager.Manager`.

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
    from . import OCR_EXE_PATH
    from .cameras import kill_service
    kill_service(exe=OCR_EXE_PATH, name='OCR', host=host, rpi_username=rpi_username, rpi_password=rpi_password)
