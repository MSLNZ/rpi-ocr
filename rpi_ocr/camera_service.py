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

import os

from .utils import (
    to_base64,
    to_cv2,
)
from .process_image import (
    apply_threshold,
    apply_erosion,
    apply_dilation,
)
from .ssocr import run_ssocr
from .tess import run_tesseract


os.environ['TESSDATA_PREFIX'] = '/usr/local/share/'

class Camera(Service):

    def __init__(self):
        super().__init__(max_clients=1)
        self._camera = PiCamera()

    def capture(self):
        buffer = BytesIO()
        self._camera.capture(buffer, 'jpeg')
        data = buffer.getvalue()
        return b64encode(data).decode('utf-8')

    def disconnect_service(self):
        self._camera.close()
        self._disconnect()

    def ocr(self, image=None, **params):
        if image is None:
            image = self.capture()

        # Convert to cv2 for processing
        image = to_cv2(image)

        if 'Crop' in params:
            x, y, w, h = params['Crop']
            image = image[y:y + h, x:x + w]

        image = apply_threshold(image, params.get('Threshold', 0))
        image = apply_dilation(image, params.get('Dilation', 0))
        image = apply_erosion(image, params.get('Erosion', 0))

        # Convert to base64 to send to RPi for ocr
        image = to_base64(image)
        language = params.get('Language', 'eng')

        if language == 'ssocr':
            number, image = run_ssocr(image)
        elif language in ['eng', 'letsgodigital']:
            number, image = run_tesseract(image, language)
        else:
            raise ValueError('Language not recognised.')
        return number, image

    def set_resolution(self, resolution):
        self._camera.resolution = resolution

    def set_zoom(self, zoom):
        self._camera.zoom = zoom
