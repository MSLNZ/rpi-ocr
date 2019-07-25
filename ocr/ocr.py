"""
Functions to perform OCR.
"""
import os
import sys
import tempfile
import warnings
import subprocess
try:
    import pytesseract
except ImportError:
    pytesseract = None

from . import utils


def ocr(image, *, algorithm='tesseract', **parameters):
    """Perform OCR on an image.

    Parameters
    ----------
    image : :class:`str`, :class:`numpy.ndarray` or :class:`Image.Image`
        The image to perform OCR on.
    algorithm : :class:`str`
        The OCR algorithm to use, e.g., `'tesseract'`, `'ssocr'`
    parameters
        Keyword arguments that are passed to :func:`process` and to
        the OCR algorithm.

    Returns
    -------
    :class:`str`
        The OCR text.
    :class:`numpy.ndarray` or :class:`Image.Image`
        The processed image.
    """
    img = process(image, **parameters)

    if algorithm == 'tesseract':
        text = tesseract(img, **parameters)
    elif algorithm == 'ssocr':
        text = ssocr(img, **parameters)
    else:
        raise ValueError('Invalid algorithm {!r} to use for OCR'.format(algorithm))

    return text, img


def tesseract(image, lang='eng', config='-c tessedit_char_whitelist=0123456789+-,.', **ignored):
    """Apply the `Tesseract <https://github.com/tesseract-ocr/tesseract>`_ algorithm.

    Parameters
    ----------
    image : :class:`str`, :class:`numpy.ndarray` or :class:`Image.Image`
        The image to apply the algorithm to.
    lang : :class:`str`
        The language code.
    config : :class:`str`
        The configuration options.
    ignored
        All other keyword arguments are silently ignored.

    Returns
    -------
    :class:`str`
        The OCR text.
    """
    if pytesseract is None:
        raise ImportError('You must install and configure tesseract and pytesseract')
    return pytesseract.image_to_string(utils.to_cv2(image), lang=lang, config=config)


def ssocr(image, iter_threshold=False, **ignored):
    """Apply the `ssocr <https://www.unix-ag.uni-kl.de/~auerswal/ssocr/>`_ algorithm.

    Parameters
    ----------
    image : :class:`str`, :class:`numpy.ndarray` or :class:`Image.Image`
        The image to apply the algorithm to.
    iter_threshold : :class:`bool`, optional
        Use iterative thresholding method.
    ignored
        All other keyword arguments are silently ignored.

    Returns
    -------
    :class:`str`
        The OCR text.
    """
    is_windows = sys.platform == 'win32'

    command = ['ssocr.bat'] if is_windows else ['ssocr']

    if iter_threshold:
        command.append('-T')

    # TODO implement all options

    # TODO use a PIPE on Windows and pass this as STDIN to Cygwin's bash.exe
    #  For now, save the image to a file and let ssocr reload it
    if is_windows:
        data = None

        try:
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', category=DeprecationWarning)
                isfile = os.path.isfile(image)
        except (ValueError, TypeError):
            isfile = False

        if isfile:
            command.append(image)
        else:
            # keep the extension png, Imlib2 raises IMLIB_LOAD_ERROR_NO_LOADER_FOR_FILE_FORMAT otherwise
            filename = os.path.join(tempfile.gettempdir(), 'ssocr-tmp.png')
            utils.save(image, filename)
            command.append(filename)

    else:
        command.append('-')  # a filename of '-' means to read the image data from stdin
        data = utils.to_base64(image).encode()

    try:
        p = subprocess.run(command, input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        raise FileNotFoundError('You must add the location of ssocr to PATH. '
                                'Call ocr.set_ssocr_path(...)') from None

    # delete the temporary image file
    if is_windows and not isfile:
        os.remove(filename)

    if p.stderr:
        raise RuntimeError(p.stderr.decode())

    return p.stdout.rstrip().decode('utf-8')


def process(image, zoom=None, rotate=None, threshold=None, dilate=None,
            erode=None, blur=None, **ignored):
    """Perform image processing.

    Parameters
    ----------
    image : :class:`str`, :class:`numpy.ndarray` or :class:`Image.Image`
        The image to process.
    zoom : :class:`tuple` of :class:`int` or :class:`float`, optional
        If specified then the value is passed to :func:`~.utils.zoom`.
    rotate : :class:`float`, optional
        If specified then the value is passed to :func:`~.utils.rotate`.
    threshold : :class:`int`, optional
        If specified then the value is passed to :func:`~.utils.threshold`.
    dilate : :class:`dict`, optional
        If specified then the value is passed to :func:`~.utils.dilate`.
        For example, dilate={'radius': 2} or dilate={'radius': 3, 'iterations': 4}
    erode : :class:`dict`, optional
        If specified then the value is passed to :func:`~.utils.erode`.
        For example, erode={'radius': 2} or erode={'radius': 3, 'iterations': 4}
    blur : :class:`int`, optional
        If specified then the value is passed to :func:`~.utils.gaussian_blur`.
    ignored
        All other keyword arguments are silently ignored.

    Returns
    -------
    The processed image.
    """
    if isinstance(image, str):
        image = utils.to_cv2(image)
    # TODO give the option to change the order of applying the transformations and the filters
    if zoom:
        image = utils.zoom(image, *zoom)
    if rotate:
        image = utils.rotate(image, rotate)
    if threshold:
        image = utils.threshold(image, threshold)
    if dilate:
        image = utils.dilate(image, **dilate)
    if erode:
        image = utils.erode(image, **erode)
    if blur:
        image = utils.gaussian_blur(image, blur)
    return image
