from msl.network import Service

try:
    from picamera import PiCamera  # on RPi
except ImportError:
    pass
else:
    import os
    from io import BytesIO
    from base64 import b64encode

    import numpy as np

    from .ocr import ocr
    from .utils import (
        DEFAULT_IMAGE_FORMAT,
        to_base64,
    )

    os.environ['TESSDATA_PREFIX'] = '/usr/local/share/'


class OCRService(Service):

    def __init__(self):
        super().__init__(max_clients=1)
        self._camera = PiCamera()
        self._initialize_array()

    def capture(self):
        """Capture an image with the camera.

        Returns
        -------
        :class:`str`
            A :mod:`base64` representation of the image.
        """
        buffer = BytesIO()
        self._camera.capture(buffer, DEFAULT_IMAGE_FORMAT)
        return b64encode(buffer.getvalue()).decode('utf-8')

    def shutdown_service(self):
        self._camera.close()

    def ocr(self, *, image=None, original=True, **parameters):
        """Apply the OCR algorithm using the specified parameters.

        Parameters
        ----------
        image : :class:`str`, :class:`numpy.ndarray` or :class:`Image.Image`, optional
            The image to perform OCR on. If :data:`None` then capture an image using
            the camera of the Raspberry Pi.
        original : :class:`bool`, optional
            Whether to return the original (unprocessed) image or the processed image.
        parameters
            Keyword arguments that are passed to the OCR algorithm.

        Returns
        -------
        :class:`str`
            The OCR text.
        :class:`str`
            The :mod:`base64` representation of the original or processed image
            (depending on the value of `original`).
        """
        if image is None:
            # capture the image directly into an OpenCV object
            image = self._camera.capture(self._array, 'rgb')

        original_image = image
        text, processed_image = ocr(image, **parameters)
        img = original_image if original else processed_image
        return text, to_base64(img)

    def set_exposure_mode(self, mode):
        """Sets the exposure mode of the camera.

        Parameters
        ----------
        mode : :class:`str`
            One of the following values:

            * ``'off'``
            * ``'auto'``
            * ``'night'``
            * ``'nightpreview'``
            * ``'backlight'``
            * ``'spotlight'``
            * ``'sports'``
            * ``'snow'``
            * ``'beach'``
            * ``'verylong'``
            * ``'fixedfps'``
            * ``'antishake'``
            * ``'fireworks'``

        """
        self._camera.exposure_mode = mode

    def set_resolution(self, resolution):
        """Set the resolution of the camera.

        Parameters
        ----------
        resolution : :class:`tuple` of :class:`int` or :class:`str`
            For example, the following definitions are all equivalent:

            * resolution = (1280, 720)
            * resolution = '1280x720'
            * resolution = '1280 x 720'
            * resolution = 'HD'
            * resolution = '720p'

        """
        if resolution == 'MAX':
            resolution = self._camera.MAX_RESOLUTION
        self._camera.resolution = resolution
        self._initialize_array()

    def set_zoom(self, zoom):
        """Set the zoom (region of interest) of the camera.

        Parameters
        ----------
        zoom : :class:`tuple` of :class:`float`
            ``(x, y, width, height)`` values ranging from 0.0 to 1.0 which
            indicate the region of the image to include.
        """
        self._camera.zoom = zoom
        self._initialize_array()

    def set_iso(self, value):
        """Set the ISO of the camera.

        Parameters
        ----------
        value : :class:`int`
            Valid values are between 0 (auto) and 1600. The actual value
            used when ISO is explicitly set will be one of the following values
            (whichever is closest): 100, 200, 320, 400, 500, 640, 800.
        """
        if value == 'auto':
            value = 0
        self._camera.iso = int(value)

    def _initialize_array(self):
        width, height = self._camera.resolution
        width_factor, height_factor = self._camera.zoom[2:]
        w = round(width * width_factor)
        h = round(height * height_factor)
        self._array = np.empty((h, w, 3), dtype=np.uint8)
