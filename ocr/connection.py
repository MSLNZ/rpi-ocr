"""
A Connection to a camera.
"""
from io import BytesIO

from msl.network import (
    ssh,
    manager,
    filter_run_forever_kwargs,
    filter_service_start_kwargs,
    Service,
    LinkedClient,
)

import numpy as np

from . import ocr
from .utils import (
    DEFAULT_IMAGE_FORMAT,
    OpenCVImage,
    to_base64,
    logger,
)

try:
    from picamera import PiCamera
except ImportError:
    class PiCamera(object):
        pass


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

    def get(self, attribute):
        """Get a value from the :class:`~picamera.PiCamera`.

        This method is for the :class:`RemoteCamera` class to call.
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

        This method is for the :class:`RemoteCamera` class to call.
        You should not call this method directly, but access the attribute directly.

        Parameters
        ----------
        attribute : :class:`str`
            The name of an attribute.
        value
            The value to set the `attribute` to.
        """
        setattr(self, attribute, value)

    def capture_base64_image(self):
        """Capture an image and convert it to base64.

        Returns
        -------
        :class:`str`
            A :mod:`base64` representation of the captured image.
        """
        buffer = BytesIO()
        self.capture(buffer, format=DEFAULT_IMAGE_FORMAT)
        return to_base64(buffer.getvalue())

    def apply_ocr(self, *, image=None, original=False, tasks=None, algorithm='tesseract', **kwargs):
        """Apply OCR to an image.

        This method is for the :class:`RemoteCamera` class to call.
        You should not call this method directly, but call :func:`~ocr.ocr` instead.

        Parameters
        ----------
        image
            The image to perform OCR on. If :data`None` then capture and image
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
            width, height = self.resolution
            image = OpenCVImage(np.empty((height, width, 3), dtype=np.uint8))
            self.capture(image, format=DEFAULT_IMAGE_FORMAT)

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

    def capture_base64_image(self):
        """Capture an image and convert it to base64.

        Returns
        -------
        :class:`str`
            A :mod:`base64` representation of the captured image.
        """
        return self.link.capture_base64_image()

    def apply_ocr(self, *, image=None, original=False, tasks=None, algorithm='tesseract', **kwargs):
        """Apply OCR to an image.

        Parameters
        ----------
        image
            The image to perform OCR on. If :data`None` then capture and image
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
        return self.link.apply_ocr(image=image, original=original, tasks=tasks, algorithm=algorithm, **kwargs)

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
