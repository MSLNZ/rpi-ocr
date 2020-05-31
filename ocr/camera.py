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

from .utils import (
    DEFAULT_IMAGE_FORMAT,
    to_base64,
    to_bytes,
    to_cv2,
    to_pil,
    logger,
)
from . import tesseract
from . import ssocr

try:
    from picamera import PiCamera
except ImportError:
    PiCamera = None


class Camera(Service):

    def __init__(self, **kwargs):
        """Connect to a local camera.

        Parameters
        ----------
        kwargs
            Keyword arguments are passed to :class:`~picamera.PiCamera`
            Can include a `quality` key-value pair for the quality of the
            JPEG encoder used for a :meth`.capture`.
        """
        super(Camera, self).__init__()

        if PiCamera is None:
            raise RuntimeError('The PiCamera class is not available. '
                               'Create an instance of a RemoteCamera instead.')

        self._quality = kwargs.pop('quality', 85)
        resolution = kwargs.pop('resolution', None)
        self._camera = PiCamera(**kwargs)
        if resolution is not None:
            if resolution == 'MAX':
                resolution = self._camera.MAX_RESOLUTION
            self._camera.resolution = resolution

        self._tesseract_languages = tesseract.languages()
        self._tesseract_version = tesseract.version()
        self._ssocr_version = ssocr.version()

        self._converters = {
            'base64': to_base64,
            'bytes': to_bytes,
            'cv2': to_cv2,
            'pil': to_pil,
        }

        from . import apply
        self._apply = apply

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

    def get_constants(self):
        """Get the ``MAX_RESOLUTION``, ``*_MODES``, ``IMAGE_EFFECTS`` and ``DRC_STRENGTHS``.

        Returns
        -------
        :class:`dict`
            The constants.
        """
        camera = self._camera
        return {
            'MAX_RESOLUTION': camera.MAX_RESOLUTION,
            'METER_MODES': camera.METER_MODES,
            'EXPOSURE_MODES': camera.EXPOSURE_MODES,
            'FLASH_MODES': camera.FLASH_MODES,
            'AWB_MODES': camera.AWB_MODES,
            'IMAGE_EFFECTS': camera.IMAGE_EFFECTS,
            'DRC_STRENGTHS': camera.DRC_STRENGTHS,
        }

    def get_settings(self):
        """Return the current settings of the camera.

        Returns
        -------
        :class:`dict`
            The settings.

        See Also
        --------
        :meth:`.update_settings`
        """
        camera = self._camera
        return {
            'resolution': camera.resolution,
            'iso': camera.iso,
            'meter_mode': camera.meter_mode,
            'exposure_mode': camera.exposure_mode,
            'flash_mode': camera.flash_mode,
            'awb_mode': camera.awb_mode,
            'image_effect': camera.image_effect,
            'drc_strength': camera.drc_strength,
            'brightness': camera.brightness,
            'contrast': camera.contrast,
            'exposure_compensation': camera.exposure_compensation,
            'saturation': camera.saturation,
            'sharpness': camera.sharpness,
            'shutter_speed': camera.shutter_speed,
            'exposure_speed': camera.exposure_speed,
            'rotation': camera.rotation,
            'hflip': camera.hflip,
            'vflip': camera.vflip,
            'image_denoise': camera.image_denoise,
            'digital_gain': float(camera.digital_gain),
            'analog_gain': float(camera.analog_gain),
            'awb_gains': list(map(float, camera.awb_gains)),
            'framerate': float(camera.framerate),
            'framerate_range': [float(camera.framerate_range.low), float(camera.framerate_range.high)],
            'image_effect_params': camera.image_effect_params,
            'zoom': camera.zoom,
            'quality': self._quality,
        }

    def update_settings(self, settings):
        """Update the settings of the camera.

        Parameters
        ----------
        settings : :class:`dict`
            The camera settings.

        See Also
        --------
        :meth:`.get_settings`
        """
        for key, value in settings.items():
            if key == 'quality':
                self._quality = value
            else:
                try:
                    setattr(self._camera, key, value)
                except:  # some attributes are read only
                    pass

    def capture(self, img_type='cv2'):
        """Capture an image and convert it to the specified data type.

        Parameters
        ----------
        img_type : :class:`str`, optional
            The object type to return the image in. One of

            * ``bytes`` :math:`\\rightarrow` :class:`bytes`
            * ``base64`` :math:`\\rightarrow` a Base64 representation of the image as a :class:`str`
            * ``cv2`` :math:`\\rightarrow` an :class:`~ocr.utils.OpenCVImage` object
            * ``pil`` :math:`\\rightarrow` a :class:`PIL.Image.Image` object

        Returns
        -------
        The image in the specified data type.
        """
        with BytesIO() as buffer:
            self._camera.capture(buffer, format=DEFAULT_IMAGE_FORMAT, quality=self._quality)
            buffer.seek(0)
            try:
                return self._converters[img_type](buffer)
            except KeyError:
                allowed = ', '.join(self._converters)
                raise ValueError('invalid img_type={!r}, must be one of: {}'.format(img_type, allowed)) from None

    def capture_with_settings(self):
        """Capture an image and get the camera settings.

        Returns
        -------
        :class:`str`
            The :mod:`base64` representation of the captured image.
        :class:`dict`
            The current settings of the camera.
        """
        capture = self.capture(img_type='base64')
        settings = self.get_settings()
        return capture, settings

    def capture_apply(self, *, tasks=None, algorithm='tesseract', **kwargs):
        """Capture an image and then apply OCR.

        Parameters
        ----------
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
            The :mod:`base64` representation of the captured image.
        """
        return self.apply(self.capture(), tasks=tasks, algorithm=algorithm, **kwargs )

    def apply(self, image, *, tasks=None, algorithm='tesseract', **kwargs):
        """Apply OCR to an image.

        Parameters
        ----------
        image : :class:`str`
            The :mod:`base64` representation of the image.
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
            The :mod:`base64` representation of the original (unprocessed) image.
        """
        text, _ = self._apply(image, tasks=tasks, algorithm=algorithm, **kwargs)
        return text, to_base64(image)

    def disconnect(self):
        """Calls :meth:`.disconnect`."""
        self.shutdown_service()

    close = disconnect

    def shutdown_service(self):
        """Calls :meth:`~picamera.PiCamera.close`."""
        self._camera.close()


class RemoteCamera(LinkedClient):

    def __init__(self, **kwargs):
        """Connect to the :class:`.Camera` service on a Raspberry Pi.

        Parameters
        ----------
        kwargs
            All keyword arguments are passed to :func:`~msl.network.client.connect`.
        """
        super(RemoteCamera, self).__init__('Camera', **kwargs)
        logger.debug('connected to the {} service running on {}'.format(self.service_name, self.service_os))

    def disconnect(self):
        """Disconnect from and shut down the :class:`.Camera` service."""
        if self._client is None:
            return
        self.wait()
        self.shutdown_service()
        super(RemoteCamera, self).disconnect()
        logger.debug('disconnected from the {} service'.format(self.service_name))

    close = disconnect

    def capture(self):
        """Capture an image.

        Returns
        -------
        :class:`~ocr.utils.OpenCVImage`
            The image.
        """
        t0 = perf_counter()
        image = to_cv2(self._link.capture(img_type='base64'))
        dt = perf_counter() - t0
        logger.info('RemoteCamera.capture took {:.3f} seconds'.format(dt))
        return image

    def __getattr__(self, item):
        def service_request(*args, **kwargs):
            try:
                t0 = perf_counter()
                reply = getattr(self._link, item)(*args, **kwargs)
                dt = perf_counter() - t0
                logger.info('RemoteCamera.{} took {:.3f} seconds'.format(item, dt))
                return reply
            except Exception as e:
                logger.error(e)
        return service_request


def start():
    """Starts the :class:`.Camera` service on the Raspberry Pi.

    This function should only be called from the ``camera`` console script (see setup.py).
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


def kill_camera_service(*, host='raspberrypi', rpi_username='pi', rpi_password=None, **ignored):
    """Kill the :class:`.Camera` service and shutdown the Network :class:`~msl.network.manager.Manager`.

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
    from . import CAMERA_EXE_PATH
    kill_service(exe=CAMERA_EXE_PATH, name='Camera', host=host, rpi_username=rpi_username, rpi_password=rpi_password)


def kill_service(exe=None, name=None, host=None, rpi_username=None, rpi_password=None):
    """Kill a service on the Raspberry Pi.

    Parameters
    ----------
    exe : :class:`str`
        The path to the executable from the console script.
    name : :class:`str`
        The name of the service.
    host : :class:`str`
        The hostname or IP address of the Raspberry Pi.
    rpi_username : :class:`str`
        The username for the Raspberry Pi.
    rpi_password : :class:`str`
        The password for `rpi_username`.
    """
    ssh_client = ssh.connect(host, username=rpi_username, password=rpi_password)
    lines = ssh.exec_command(ssh_client, 'ps aux | grep {}'.format(name.lower()))
    pids = [line.split()[1] for line in lines if exe in line]
    for pid in pids:
        try:
            ssh.exec_command(ssh_client, 'sudo kill -9 ' + pid)
            logger.debug('killed the {} service pid={} on the Raspberry Pi'.format(name, pid))
        except Exception as e:
            logger.error(e)
    ssh_client.close()
