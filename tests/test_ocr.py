import os
import sys

import ocr


def test_ssocr():
    six_digits = os.path.join(os.path.dirname(__file__), 'images', 'six_digits.png')

    if sys.platform == 'win32':
        ocr.set_ssocr_path(os.path.join(os.path.dirname(__file__), '..', 'resources', 'ssocr-win64'))

    expected = '431432'
    assert ocr.ssocr(six_digits, iter_threshold=True) == expected
    assert ocr.ssocr(ocr.utils.to_cv2(six_digits), iter_threshold=True) == expected
    assert ocr.ssocr(ocr.utils.to_pil(six_digits), iter_threshold=True) == expected
    assert ocr.ssocr(ocr.utils.to_base64(six_digits), iter_threshold=True) == expected


def test_tesseract():
    eng = os.path.join(os.path.dirname(__file__), 'images', 'tesseract_eng_text.png')
    expected = 'A Python Approach to Character\nRecognition'
    assert ocr.tesseract(eng, config='') == expected
    assert ocr.tesseract(ocr.utils.to_cv2(eng), config='') == expected
    assert ocr.tesseract(ocr.utils.to_pil(eng), config='') == expected
    assert ocr.tesseract(ocr.utils.to_base64(eng), config='') == expected

    numbers = os.path.join(os.path.dirname(__file__), 'images', 'tesseract_numbers.jpg')
    expected = '619121'
    assert ocr.tesseract(numbers) == expected
    assert ocr.tesseract(ocr.utils.to_cv2(numbers)) == expected
    assert ocr.tesseract(ocr.utils.to_pil(numbers)) == expected
    assert ocr.tesseract(ocr.utils.to_base64(numbers)) == expected
