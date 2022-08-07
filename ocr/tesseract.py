"""
The `Tesseract <https://github.com/tesseract-ocr/tesseract>`_ algorithm.
"""
import os
import sys
import subprocess

import pytesseract

from .utils import (
    to_cv2,
    get_executable_path,
    logger,
)

# the name of the executable
tesseract_exe = 'tesseract.exe' if sys.platform == 'win32' else 'tesseract'

# whether the executable is available in PATH
is_available = False
for path in os.environ['PATH'].split(os.pathsep):
    if os.path.isfile(os.path.join(path, tesseract_exe)):
        is_available = True
        break


def set_tesseract_path(path):
    """Set the path to the ``tesseract`` executable.

    Parameters
    ----------
    path : :class:`str`
        The full path to the ``tesseract`` executable or a top-level
        directory that contains the executable.
    """
    global is_available
    cmd = get_executable_path(path, 'tesseract')
    logger.debug('set tesseract executable to %r', cmd)
    pytesseract.pytesseract.tesseract_cmd = cmd
    is_available = True


def version():
    """Get the version number of ``tesseract``.

    Returns
    -------
    :class:`str`
        The version number.
    """
    # pytesseract.get_tesseract_version() returns an object of type
    # <class 'packaging.version.Version'>, so cast to str
    ver = str(pytesseract.get_tesseract_version())
    logger.debug('tesseract version: %s', ver)
    return ver


def languages():
    """Get the list of languages that are available to ``tesseract``.

    Returns
    -------
    :class:`list` of :class:`str`
        The languages.
    """
    cmd = [pytesseract.pytesseract.tesseract_cmd, '--list-langs']
    out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    langs = out.decode('utf-8').splitlines()[1:]
    logger.debug('tesseract languages: %s', ', '.join(langs))
    return langs


def apply(image, *, language='eng', psm=8, oem=3, whitelist='0123456789+-.', timeout=0, nice=0, config=''):
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
        The maximum number of seconds to wait for the result before raising a :exc:`RuntimeError`.
    nice : :class:`int`, optional
        Modifies the processor priority for the Tesseract run. Not supported on Windows.
    config : :class:`str`, optional
        Any additional configuration parameters.

    Returns
    -------
    :class:`str`
        The OCR text.
    """
    cfg = f'--psm {psm} --oem {oem}'
    if whitelist:
        cfg += f' -c tessedit_char_whitelist={whitelist}'
    if config:
        cfg += f' {config}'
    logger.info('tesseract params: language=%r config=%r nice=%s timeout=%s', language, cfg, nice, timeout)
    string = pytesseract.image_to_string(to_cv2(image), lang=language, config=cfg, nice=nice, timeout=timeout)
    return string.strip()
