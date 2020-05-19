"""
A Connection to a camera.
"""
from time import perf_counter
from io import BytesIO

from msl.network import (
    ssh,
    manager,
    filter_run_forever_kwargs,
    filter_service_start_kwargs,
    Service,
    LinkedClient,
)

from . import ocr
from .utils import (
    DEFAULT_IMAGE_FORMAT,
    to_base64,
    to_bytes,
    to_cv2,
    to_pil,
    logger,
)
from .tesseract import languages
from .tesseract import version as tesseract_version
from .ssocr import version as ssocr_version

try:
    from picamera import PiCamera
except ImportError:
    class PiCamera(object):
        pass

_converters = {
    'base64': to_base64,
    'bytes': to_bytes,
    'cv2': to_cv2,
    'pil': to_pil,
}


def _convert(image, as_type):
    try:
        return _converters[as_type](image)
    except KeyError:
        pass

    allowed = ', '.join(_converters)
    raise ValueError('invalid as_type={!r}, must be one of: {}'.format(as_type, allowed))


class Camera(Service, PiCamera):

    def __init__(self, **kwargs):
        """Connect to a local camera.

        Parameters
        ----------
        kwargs
            All keyword arguments are passed to :class:`~picamera.PiCamera`.
        """
        # these attributes of the PiCamera cannot be
        # included in the `identity` of the `Service`
        # because they are not JSON serializable or they
        # raise an exception when getattr() is called
        ignore = ['RAW_FORMATS', 'analog_gain', 'awb_gains',
                  'digital_gain', 'led', 'frame', 'framerate',
                  'framerate_delta', 'framerate_range']
        Service.__init__(self, ignore_attributes=ignore)
        PiCamera.__init__(self, **kwargs)

        self._tesseract_languages = languages()
        self._tesseract_version = tesseract_version()
        self._ssocr_version = ssocr_version(include_copyright=False)

    def get(self, attribute):
        """Get a value from the :class:`~picamera.PiCamera`.

        This method is intended for the :class:`RemoteCamera` class to call.
        You should not call this method directly, but access the attribute directly.

        Parameters
        ----------
        attribute : :class:`str`
            The name of an attribute.

        Returns
        -------
        The value of the attribute.
        """
        return getattr(self, attribute)

    def set(self, attribute, value):
        """Set a value of the :class:`~picamera.PiCamera`.

        This method is intended for the :class:`RemoteCamera` class to call.
        You should not call this method directly, but access the attribute directly.

        Parameters
        ----------
        attribute : :class:`str`
            The name of an attribute.
        value
            The value to set the `attribute` to.
        """
        setattr(self, attribute, value)

    def ssocr_version(self):
        """Get the version information of ssocr.

        Returns
        -------
        :class:`str`
            The version of ssocr.
        """
        return self._ssocr_version

    def tesseract_languages_version(self):
        """Get the languages and version information of Tesseract-OCR.

        Returns
        -------
        :class:`list` of :class:`str`
            The languages that are available to Tesseract-OCR.
        :class:`str`
            The version of Tesseract-OCR.
        """
        return self._tesseract_languages, self._tesseract_version

    def capture_ocr(self, as_type='cv2'):
        """Capture an image and convert it to the specified type.

        Parameters
        ----------
        as_type : :class:`str`, optional
            The object type to return the image in. One of

            * ``bytes`` :math:`\\rightarrow` :class:`bytes`
            * ``base64`` :math:`\\rightarrow` a Base64 representation of the image as a :class:`str`
            * ``cv2`` :math:`\\rightarrow` an :class:`~ocr.utils.OpenCVImage` object
            * ``pil`` :math:`\\rightarrow` a :class:`PIL.Image.Image` object

        Returns
        -------
        The image in the specified data type.
        """
        buffer = BytesIO()
        self.capture(buffer, format=DEFAULT_IMAGE_FORMAT)
        buffer.seek(0)
        return _convert(buffer, as_type)

    def apply_ocr(self, *, image=None, original=False, tasks=None, algorithm='tesseract', **kwargs):
        """Apply OCR to an image.

        This method is intended for the :class:`RemoteCamera` class to call.
        You should not call this method directly, but call :func:`~ocr.ocr` instead.

        Parameters
        ----------
        image
            The image to perform OCR on. If :data`None` then capture an image
            with the camera.
        original : :class:`bool`, optional
            Whether to return the original image or the processed image.
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
            The :mod:`base64` representation of the original or processed image
            (depending on the value of `original`).
        """
        if image is None:
            image = self.capture_ocr()
        text, processed_image = ocr(image, tasks=tasks, algorithm=algorithm, **kwargs)
        if original:
            return text, to_base64(image)
        return text, to_base64(processed_image)

    def shutdown_service(self):
        """Calls :meth:`~picamera.PiCamera.close`."""
        self.close()

    def disconnect(self):
        """Calls :meth:`~picamera.PiCamera.close`."""
        self.close()


class RemoteCamera(LinkedClient):

    def __init__(self, **kwargs):
        """Connect to the :class:`.Camera` service on a Raspberry Pi.

        Parameters
        ----------
        kwargs
            All keyword arguments are passed to :func:`~msl.network.client.connect`.
        """
        super(RemoteCamera, self).__init__('Camera', **kwargs)
        logger.debug('connected to the {!r} service running on {!r}'.format(self.service_name, self.service_os))

    def __getattr__(self, name):
        if name[0] == '_':
            return super(RemoteCamera, self).__getattr__(name)
        else:
            logger.debug('get camera ' + name)
            return self.link.get(name)

    def __setattr__(self, name, value):
        if name[0] == '_':
            super(RemoteCamera, self).__setattr__(name, value)
        else:
            logger.debug('set camera {}={!r}'.format(name, value))
            self.link.set(name, value)

    def disconnect(self):
        """Disconnect from and shut down the :class:`.Camera` service."""
        if self.client is None:
            return

        logger.debug('disconnecting from the {!r} service'.format(self.service_name))
        try:
            self.wait()  # wait for all pending requests to finish
        except:
            pass

        try:
            self.shutdown_service()
        except:
            pass

        try:
            super(RemoteCamera, self).disconnect()
        except:
            pass

    close = disconnect

    def ssocr_version(self):
        """Get the version information of ssocr.

        Returns
        -------
        :class:`str`
            The version of ssocr.
        """
        return self.link.ssocr_version()

    def tesseract_languages_version(self):
        """Get the languages and version information of Tesseract-OCR.

        Returns
        -------
        :class:`list` of :class:`str`
            The languages that are available to Tesseract-OCR.
        :class:`str`
            The version of Tesseract-OCR.
        """
        return self.link.tesseract_languages_version()

    def capture_ocr(self, as_type='cv2'):
        """Capture an image and convert it to the specified type.

        Parameters
        ----------
        as_type : :class:`str`, optional
            The object type to return the image in. See :meth:`.Camera.capture_ocr`
            for more details.

        Returns
        -------
        The image in the specified data type.
        """
        # must request base64 then convert afterwards
        t0 = perf_counter()
        image = self.link.capture_ocr(as_type='base64')
        logger.debug('requesting capture_ocr took {:.3f} seconds'.format(perf_counter()-t0))
        if as_type == 'base64':
            return image
        return _convert(image, as_type)

    def apply_ocr(self, *, image=None, original=False, tasks=None, algorithm='tesseract', **kwargs):
        """Apply OCR to an image.

        Parameters
        ----------
        image
            The image to perform OCR on. If :data`None` then capture an image
            with the camera.
        original : :class:`bool`, optional
            Whether to return the original image or the processed image.
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
            The :mod:`base64` representation of the original or processed image
            (depending on the value of `original`).
        """
        if image is not None:
            image = to_base64(image)
        t0 = perf_counter()
        out = self.link.apply_ocr(image=image, original=original, tasks=tasks, algorithm=algorithm, **kwargs)
        logger.debug('requesting apply_ocr took {:.3f} seconds'.format(perf_counter()-t0))
        return out

    def service_error_handler(self):
        """Shut down the :class:`.Camera` service if it raises an exception."""
        self.disconnect()


def start_camera_service():
    """Starts the Network :class:`~msl.network.manager.Manager` and the :class:`.Camera` service.

    This function should only be called from the ``ocr`` console script (see setup.py).
    """
    kwargs = ssh.parse_console_script_kwargs()
    if kwargs.get('auth_login', False) and ('username' not in kwargs or 'password' not in kwargs):
        raise ValueError(
            'The Manager is using a login for authentication but the Camera service '
            'does not know the username and password to use to connect to the Manager'
        )

    non_camera_kwargs = filter_run_forever_kwargs(**kwargs)
    non_camera_kwargs.update(filter_service_start_kwargs(**kwargs))

    camera_kwargs = {}
    for key, value in kwargs.items():
        if key not in non_camera_kwargs:
            camera_kwargs[key] = value

    manager.run_services(Camera(**camera_kwargs), **non_camera_kwargs)
