"""
The `Tesseract <https://github.com/tesseract-ocr/tesseract>`_ algorithm.
"""
import os

try:
    import pytesseract
except ImportError:
    pytesseract = None

from .utils import to_cv2


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
        os.environ['PATH'] = path + os.pathsep + os.environ['PATH']


def tesseract(image, lang='eng', config='-c tessedit_char_whitelist=0123456789+-,.'):
    """Apply the `Tesseract <https://github.com/tesseract-ocr/tesseract>`_ algorithm.

    Parameters
    ----------
    image
        An image to apply the algorithm to. The data type must be supported by :
    lang : :class:`str`, optional
        The language code.
    config : :class:`str`
        The configuration options.

    Returns
    -------
    :class:`str`
        The OCR text.
    """
    if pytesseract is None:
        raise ImportError('You must install and configure tesseract and pytesseract')
    return pytesseract.image_to_string(to_cv2(image), lang=lang, config=config)
