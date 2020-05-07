from msl.network import LinkedClient

from .utils import (
    to_base64,
    save,
)


class OCRClient(LinkedClient):

    def __init__(self, service_name, **kwargs):
        super(OCRClient, self).__init__(service_name, **kwargs)

    def configure(self, **kwargs):
        """Display a GUI to configure the OCR parameters.

        The parameters are the initial values to use in the GUI.

        Parameters
        ----------
        path : :class:`str`, optional
            The image to open. If :data:`None` then stream images taken by the
            camera of the Raspberry Pi.
        algorithm
        threshold
        dilate
        erode
        rotate
        lang
        zoom
        blur
        max_blur
        max_dilate
        max_erode
        iso
        resolution
        exposure_mode

        Returns
        -------
        :class:`dict`
            The parameters to use for the OCR algorithm. These parameters
            should be passed to :meth:`ocr`.
        """
        from . import configure
        return configure(self, **kwargs)

    def disconnect(self):
        """
        Shut down the :class:`~ocr.service.OCRService` and the Network
        :class:`~msl.network.manager.Manager`.
        """
        try:
            self.wait()  # wait for all pending requests to finish before sending the disconnect request
        except:
            pass
        try:
            self.shutdown_service()
        except:
            pass
        try:
            super(OCRClient, self).disconnect()
        except:
            pass

    # make 'stop' an alias for the 'disconnect' method
    stop = disconnect

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
        img = None if image is None else to_base64(image)
        return self.link.ocr(image=img, original=original, **parameters)

    @staticmethod
    def save(image, filename, params=None):
        """Calls :func:`~ocr.utils.save`."""
        save(image, filename, params=params)

    def service_error_handler(self):
        """Shut down the :class:`~ocr.service.OCRService` if it raises an exception."""
        self.disconnect()
