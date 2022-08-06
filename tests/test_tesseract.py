import os
import sys
import tempfile

import pytest
from pytesseract import TesseractNotFoundError

import ocr
from ocr import tesseract

IMAGE_ROOT = os.path.join(os.path.dirname(__file__), 'images')


@pytest.mark.parametrize('ext', ['bmp', 'jpg', 'jpeg', 'png', 'tif', 'tiff'])
def test_english(ext):
    expected = 'A Python Approach to Character\nRecognition'
    params = {'psm': 3, 'whitelist': None}

    eng = os.path.join(IMAGE_ROOT, 'tesseract_eng_text.png')
    p = tempfile.gettempdir() + '/tesseract_eng_text.' + ext

    assert tesseract.apply(eng, **params) == expected

    ocr.save(p, eng)

    assert tesseract.apply(p, **params) == expected
    assert tesseract.apply(ocr.utils.to_cv2(p), **params) == expected
    assert tesseract.apply(ocr.utils.to_pil(p), **params) == expected
    assert tesseract.apply(ocr.utils.to_base64(p), **params) == expected
    assert tesseract.apply(ocr.utils.to_bytes(p), **params) == expected
    with open(p, mode='rb') as fp:
        assert tesseract.apply(fp.read(), **params) == expected

    os.remove(p)
    assert not os.path.isfile(p)


@pytest.mark.parametrize('ext', ['bmp', 'jpg', 'jpeg', 'png', 'tif', 'tiff'])
def test_numbers(ext):
    expected = '619121'

    numbers = os.path.join(IMAGE_ROOT, 'tesseract_numbers.jpg')
    p = tempfile.gettempdir() + '/tesseract_numbers.' + ext

    assert tesseract.apply(numbers, psm=7) == expected

    ocr.save(p, numbers)

    assert tesseract.apply(p, psm=7) == expected
    assert tesseract.apply(ocr.utils.to_cv2(p), psm=7) == expected
    assert tesseract.apply(ocr.utils.to_pil(p), psm=7) == expected
    assert tesseract.apply(ocr.utils.to_base64(p), psm=7) == expected
    assert tesseract.apply(ocr.utils.to_bytes(p), psm=7) == expected
    with open(p, mode='rb') as fp:
        assert tesseract.apply(fp.read(), psm=7) == expected

    for fcn in [ocr.utils.to_cv2, ocr.utils.to_pil]:
        cropped = ocr.utils.crop(fcn(p), 200, 100, 180, 200)
        assert tesseract.apply(cropped, psm=7) == expected[:2]

    os.remove(p)
    assert not os.path.isfile(p)


def test_version():
    assert isinstance(tesseract.version(), str)


@pytest.mark.skipif(sys.platform != 'win32', reason='non-Windows OS')
def test_set_tesseract_path():
    expected = '619121'
    numbers_path = os.path.join(IMAGE_ROOT, 'tesseract_numbers.jpg')

    # make sure tesseract is available
    assert tesseract.apply(numbers_path, psm=7) == expected

    # make sure the executable is not available on PATH
    environ_path = None
    for path in os.environ['PATH'].split(os.pathsep):
        if os.path.isfile(os.path.join(path, 'tesseract.exe')):
            environ_path = path
            os.environ['PATH'] = os.environ['PATH'].replace(path, '')
            break
    assert environ_path is not None

    # tesseract not available
    with pytest.raises(TesseractNotFoundError):
        tesseract.apply(numbers_path)

    # this should work again
    tesseract.set_tesseract_path(environ_path)
    assert tesseract.apply(numbers_path, psm=7) == expected


def test_languages():
    langs = tesseract.languages()
    assert 'eng' in langs
    assert 'letsgodigital' in langs


def test_letsgodigital():
    path = os.path.join(IMAGE_ROOT, 'letsgodigital.png')
    tasks = [('greyscale',), ('threshold', 40), ('erode', 3)]
    text, _ = ocr.apply(path, tasks=tasks, algorithm='tesseract', language='letsgodigital')
    assert text == '22.3'


def test_config():
    path = os.path.join(IMAGE_ROOT, 'tesseract_numbers.jpg')
    assert tesseract.apply(path, psm=7, whitelist=None, config='-c tessedit_char_whitelist=0123456789') == '619121'
    assert '1' not in tesseract.apply(path, psm=7, config='-c tessedit_char_blacklist=1')


def test_invalid_image():
    # must raise ValueError instead of FileNotFoundError
    for obj in ['does/not/exist.jpg', 'X'*10000 + '.png']:
        with pytest.raises(ValueError, match=r'^Invalid path or base64 string'):
            tesseract.apply(obj)
