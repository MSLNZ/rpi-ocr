import os
import sys
import tempfile
from distutils.version import LooseVersion

import pytest
from pytesseract import TesseractNotFoundError

import ocr
from ocr.tesseract import (
    version,
    set_tesseract_path,
)


def test_english():
    expected = 'A Python Approach to Character\nRecognition'

    eng = os.path.join(os.path.dirname(__file__), 'images', 'tesseract_eng_text.png')
    temp_paths = [tempfile.gettempdir() + '/tesseract_eng_text.' + ext
                  for ext in ['bmp', 'jpg', 'jpeg', 'png', 'tif', 'tiff']]

    assert ocr.tesseract(eng, config='') == expected

    for p in temp_paths:
        ocr.save(eng, p)

        assert ocr.tesseract(p, config='') == expected
        assert ocr.tesseract(ocr.utils.to_cv2(p), config='') == expected
        assert ocr.tesseract(ocr.utils.to_pil(p), config='') == expected
        assert ocr.tesseract(ocr.utils.to_base64(p), config='') == expected
        assert ocr.tesseract(ocr.utils.to_bytes(p), config='') == expected
        with open(p, 'rb') as fp:
            assert ocr.tesseract(fp.read(), config='') == expected

        os.remove(p)
        assert not os.path.isfile(p)


def test_numbers():
    expected = '619121'

    numbers = os.path.join(os.path.dirname(__file__), 'images', 'tesseract_numbers.jpg')
    temp_paths = [tempfile.gettempdir() + '/tesseract_numbers.' + ext
                  for ext in ['bmp', 'jpg', 'jpeg', 'png', 'tif', 'tiff']]

    assert ocr.tesseract(numbers) == expected

    for p in temp_paths:
        ocr.save(numbers, p)

        assert ocr.tesseract(p) == expected
        assert ocr.tesseract(ocr.utils.to_cv2(p)) == expected
        assert ocr.tesseract(ocr.utils.to_pil(p)) == expected
        assert ocr.tesseract(ocr.utils.to_base64(p)) == expected
        assert ocr.tesseract(ocr.utils.to_bytes(p)) == expected
        with open(p, 'rb') as fp:
            assert ocr.tesseract(fp.read()) == expected

        for fcn in [ocr.utils.to_cv2, ocr.utils.to_pil]:
            zoomed = ocr.utils.zoom(fcn(p), 200, 100, 180, 200)
            assert ocr.tesseract(zoomed) == expected[:2]

        os.remove(p)
        assert not os.path.isfile(p)

    for obj in ['does/not/exist.jpg', 'X'*10000 + '.png']:
        with pytest.raises(ValueError, match=r'^Invalid path or base64 string'):
            ocr.tesseract(obj)


def test_version():
    assert isinstance(version(), LooseVersion)


def test_set_tesseract_path():
    expected = '619121'
    numbers_path = os.path.join(os.path.dirname(__file__), 'images', 'tesseract_numbers.jpg')

    # make sure tesseract is available
    assert ocr.tesseract(numbers_path) == expected

    # make sure the executable is not available on PATH
    tesseract_exe = 'tesseract'
    if sys.platform == 'win32':
        tesseract_exe += '.exe'
    environ_path = None
    for path in os.environ['PATH'].split(os.pathsep):
        if os.path.isfile(os.path.join(path, tesseract_exe)):
            environ_path = path
            os.environ['PATH'] = os.environ['PATH'].replace(path, '')
            break
    assert environ_path is not None

    # tesseract not available
    with pytest.raises(TesseractNotFoundError):
        ocr.tesseract(numbers_path)

    # this should work again
    set_tesseract_path(environ_path)
    assert ocr.tesseract(numbers_path) == expected
