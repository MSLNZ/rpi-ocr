from msl.network import LinkedClient, Service
try:
    from picamera import PiCamera  # on RPi
    from io import BytesIO
    from base64 import b64encode, b64decode
    from time import sleep
    import pytesseract
    import ssocr
    import numpy as np
    import cv2
    from PIL import Image
    import subprocess
except ImportError:
    pass

from .gui import Gui


class CameraClient(LinkedClient):

    def __init__(self, service_name, **kwargs):
        super().__init__(service_name, **kwargs)

    def disconnect(self):
        """
        Shut down the CameraService :class:`~msl.network.service.Service`
        and the Network :class:`~msl.network.manager.Manager`.
        """
        self.disconnect_service()
        super().disconnect()

    def service_error_handler(self):
        """
        Shut down the CameraService :class:`~msl.network.service.Service`
        and the Network :class:`~msl.network.manager.Manager` if there was
        an error.
        """
        self.disconnect()

    def stop(self):
        self.disconnect()

    def configure(self, image=None):
        # pop up GUI -> dict of parameters to pass to self.ocr
        gui = Gui(self)
        gui.set_image(image)
        gui.show()
        return gui.ocr_params
