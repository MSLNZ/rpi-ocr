import os
import tempfile

import pytest

import ocr


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
