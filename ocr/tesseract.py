"""
The `Tesseract <https://github.com/tesseract-ocr/tesseract>`_ algorithm.
"""
import subprocess

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


def languages():
    """Get the list of languages that are available to ``tesseract``.

    Returns
    -------
    :class:`list` of :class:`str`
        The languages.
    """
    _check_pytessseract_installed()
    cmd = [pytesseract.pytesseract.tesseract_cmd, '--list-langs']
    out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    return out.decode('utf-8').splitlines()[1:]


def tesseract(image, *, language='eng', psm=7, oem=3, whitelist='0123456789+-.', timeout=0, nice=0, config=''):
    """Apply the `Tesseract <https://github.com/tesseract-ocr/tesseract>`_ algorithm.

    Parameters
    ----------
    image
        An image to apply the algorithm to. The data type must be supported
        by :func:`~.utils.to_cv2`.
    language : :class:`str`, optional
        The name of the language to use.
    psm : :class:`int`, optional
        Page segmentation mode:

        * 0 -- Orientation and script detection (OSD) only.
        * 1 -- Automatic page segmentation with OSD.
        * 2 -- Automatic page segmentation, but no OSD, or OCR. (not implemented)
        * 3 -- Fully automatic page segmentation, but no OSD.
        * 4 -- Assume a single column of text of variable sizes.
        * 5 -- Assume a single uniform block of vertically aligned text.
        * 6 -- Assume a single uniform block of text.
        * 7 -- Treat the image as a single text line.
        * 8 -- Treat the image as a single word.
        * 9 -- Treat the image as a single word in a circle.
        * 10 --Treat the image as a single character.
        * 11 -- Sparse text. Find as much text as possible in no particular order.
        * 12 -- Sparse text with OSD.
        * 13 -- Raw line. Treat the image as a single text line, bypassing hacks that are Tesseract-specific.
    oem : :class:`int`, optional
        OCR engine mode:

        * 0 -- Legacy engine only.
        * 1 -- Neural nets LSTM engine only.
        * 2 -- Legacy + LSTM engines.
        * 3 -- Based on what is available.
    whitelist : :class:`str`, optional
        The character set that the result must be in (equivalent to ``-c tessedit_char_whitelist``).
        Set to :data:`None` or an empty string to not use a whitelist.
    timeout : :class:`float`, optional
        The number of seconds to wait for the result before raising a :exc:`RuntimeError`.
    nice : :class:`int`, optional
        Modifies the processor priority for the Tesseract run. Not supported on Windows.
    config : :class:`str`, optional
        Any additional configuration parameters.

    Returns
    -------
    :class:`str`
        The OCR text.
    """
    _check_pytessseract_installed()
    cfg = '--psm {} --oem {}'.format(psm, oem)
    if whitelist:
        cfg += ' -c tessedit_char_whitelist=' + whitelist
    if config:
        cfg += ' ' + config
    logger.debug('tesseract params: language={!r} config={!r} nice={} timeout={}'.format(language, cfg, nice, timeout))
    return pytesseract.image_to_string(to_cv2(image), lang=language, config=cfg, nice=nice, timeout=timeout)


def _check_pytessseract_installed():
    if pytesseract is None:
        # this is the same error message that pytesseract.TesseractNotFoundError would display
        # Raise FileNotFoundError since this is what ssocr raises if it is not available
        raise FileNotFoundError("tesseract is not installed or it's not in your path")
