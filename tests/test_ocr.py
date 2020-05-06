import os
import sys
import tempfile

import pytest

import ocr


def test_ssocr():
    expected = '431432'
    six_digits_path = os.path.join(os.path.dirname(__file__), 'images', 'six_digits.png')

    temp_paths = [tempfile.gettempdir() + '/six_digits.' + ext
                  for ext in ['bmp', 'jpg', 'jpeg', 'png', 'tif', 'tiff']]

    if sys.platform == 'win32':
        # check that the error message is correct if ssocr.exe is not available on PATH
        with pytest.raises(FileNotFoundError, match=r'ocr.set_ssocr_path(...)'):
            ocr.ssocr(six_digits_path)

        # set the path to the ssocr.exe so that the remainder of this test will pass
        ocr.set_ssocr_path(os.path.join(os.path.dirname(__file__), '..', 'resources', 'ssocr-win64'))

    for p in temp_paths:
        ocr.save(p, six_digits_path)
        _, ext = os.path.splitext(p)
        assert ocr.ssocr(p, iter_threshold=True) == expected
        assert ocr.ssocr(ocr.utils.to_bytes(p), iter_threshold=True) == expected
        with open(p, 'rb') as fp:
            assert ocr.ssocr(fp.read(), iter_threshold=True) == expected
        assert ocr.ssocr(ocr.utils.to_cv2(p), iter_threshold=True) == expected
        assert ocr.ssocr(ocr.utils.to_pil(p), iter_threshold=True) == expected

        zoomed = ocr.utils.zoom(ocr.utils.to_cv2(p), 0, 0, 100, 73)
        assert ocr.ssocr(zoomed, iter_threshold=True) == expected[:2]
        zoomed = ocr.utils.zoom(ocr.utils.to_pil(p), 0, 0, 100, 73)
        assert ocr.ssocr(zoomed, iter_threshold=True) == expected[:2]

        with pytest.raises(RuntimeError, match=r'IMLIB_LOAD_ERROR_FILE_DOES_NOT_EXIST$'):
            ocr.ssocr(ocr.utils.to_base64(p))

        with pytest.raises(RuntimeError, match=r'IMLIB_LOAD_ERROR_FILE_DOES_NOT_EXIST$'):
            ocr.ssocr('no_image.' + ext)

        os.remove(p)
        assert not os.path.isfile(p)


def test_tesseract():

    # English text
    eng = os.path.join(os.path.dirname(__file__), 'images', 'tesseract_eng_text.png')
    temp_paths = [tempfile.gettempdir() + '/tesseract_eng_text.' + ext
                  for ext in ['bmp', 'jpg', 'jpeg', 'png', 'tif', 'tiff']]

    expected = 'A Python Approach to Character\nRecognition'
    assert ocr.tesseract(eng, config='') == expected
    for p in temp_paths:
        ocr.save(p, eng)
        assert ocr.tesseract(p, config='') == expected
        assert ocr.tesseract(ocr.utils.to_cv2(p), config='') == expected
        assert ocr.tesseract(ocr.utils.to_pil(p), config='') == expected
        assert ocr.tesseract(ocr.utils.to_base64(p), config='') == expected
        os.remove(p)
        assert not os.path.isfile(p)

    # Digits
    numbers = os.path.join(os.path.dirname(__file__), 'images', 'tesseract_numbers.jpg')
    temp_paths = [tempfile.gettempdir() + '/tesseract_numbers.' + ext
                  for ext in ['bmp', 'jpg', 'jpeg', 'png', 'tif', 'tiff']]
    expected = '619121'
    assert ocr.tesseract(numbers) == expected
    for p in temp_paths:
        ocr.save(p, numbers)
        assert ocr.tesseract(p) == expected
        assert ocr.tesseract(ocr.utils.to_cv2(p)) == expected
        assert ocr.tesseract(ocr.utils.to_pil(p)) == expected
        assert ocr.tesseract(ocr.utils.to_base64(p)) == expected

        zoomed = ocr.utils.zoom(ocr.utils.to_cv2(p), 200, 100, 180, 200)
        assert ocr.tesseract(zoomed) == expected[:2]
        zoomed = ocr.utils.zoom(ocr.utils.to_pil(p), 200, 100, 180, 200)
        assert ocr.tesseract(zoomed) == expected[:2]

        os.remove(p)
        assert not os.path.isfile(p)
