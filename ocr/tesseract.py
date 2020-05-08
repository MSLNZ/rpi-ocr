"""
The `Tesseract <https://github.com/tesseract-ocr/tesseract>`_ algorithm.
"""
try:
    import pytesseract
except ImportError:
    pytesseract = None

from .utils import (
    to_cv2,
    get_executable_path,
    logger,
)


def set_tesseract_path(path):
    """Set the path to the ``tesseract`` executable.

    Parameters
    ----------
    path : :class:`str`
        The full path to the ``tesseract`` executable or a top-level
        directory that contains the executable.
    """
    _check_pytessseract_installed()
    exe = get_executable_path(path, 'tesseract')
    logger.debug('set tesseract executable to {!r}'.format(exe))
    pytesseract.pytesseract.tesseract_cmd = exe


def version():
    """Get the version number of ``tesseract``.

    Returns
    -------
    :class:`str`
        The version number (and possibly copyright information).
    """
    _check_pytessseract_installed()
    return pytesseract.get_tesseract_version()


def tesseract(image, *, lang='eng', config='-c tessedit_char_whitelist=0123456789+-,.', **kwargs):
    """Apply the `Tesseract <https://github.com/tesseract-ocr/tesseract>`_ algorithm.

    Parameters
    ----------
    image
        An image to apply the algorithm to. The data type must be supported
        by :func:`~.utils.to_cv2`.
    lang : :class:`str`, optional
        The language name.
    config : :class:`str`, optional
        The configuration options.
    kwargs
        Additional keyword arguments are passed to :func:`pytesseract.image_to_string`.

    Returns
    -------
    :class:`str`
        The OCR text.
    """
    _check_pytessseract_installed()
    return pytesseract.image_to_string(to_cv2(image), lang=lang, config=config, **kwargs)


def _check_pytessseract_installed():
    if pytesseract is None:
        # this is the same error message that pytesseract.TesseractNotFoundError would display
        # Raise FileNotFoundError since this is what ssocr raises if it is not available
        raise FileNotFoundError("tesseract is not installed or it's not in your path")
