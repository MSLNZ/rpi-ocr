import os
import tempfile

import pytest
import numpy as np
from PIL import Image

from ocr import utils

ROOT = os.path.join(os.path.dirname(__file__), 'images')
PNG_PATH = os.path.join(ROOT, 'six_digits.png')
JPG_PATH = os.path.join(ROOT, 'tesseract_numbers.jpg')
BMP_PATH = os.path.join(ROOT, 'colour.bmp')


def test_to_base64():
    #
    # test path -> to_base64
    #

    png = utils.to_base64(PNG_PATH)
    assert isinstance(png, str)
    assert png.startswith('iVBOR')

    jpg = utils.to_base64(JPG_PATH)
    assert isinstance(jpg, str)
    assert jpg.startswith('/9j/4')

    bmp = utils.to_base64(BMP_PATH)
    assert isinstance(bmp, str)
    assert bmp.startswith('Qk02u')

    #
    # test to_base64 -> to_base64
    #
    assert utils.to_base64(png) is png
    assert utils.to_base64(jpg) is jpg
    assert utils.to_base64(bmp) is bmp

    #
    # test to_cv2 -> to_base64 (to_base64 always returns a JPG image type for cv2)
    #

    png = utils.to_base64(utils.to_cv2(PNG_PATH))
    assert isinstance(png, str)
    assert png.startswith('/9j/4')

    jpg = utils.to_base64(utils.to_cv2(JPG_PATH))
    assert isinstance(jpg, str)
    assert jpg.startswith('/9j/4')

    bmp = utils.to_base64(utils.to_cv2(BMP_PATH))
    assert isinstance(bmp, str)
    assert bmp.startswith('/9j/4')

    # test to_pil -> to_base64 (to_base64 always returns a JPG image type for PIL)
    png = utils.to_base64(utils.to_pil(PNG_PATH))
    assert isinstance(png, str)
    assert png.startswith('/9j/4')

    jpg = utils.to_base64(utils.to_pil(JPG_PATH))
    assert isinstance(jpg, str)
    assert jpg.startswith('/9j/4')

    bmp = utils.to_base64(utils.to_pil(BMP_PATH))
    assert isinstance(bmp, str)
    assert bmp.startswith('/9j/4')

    #
    # test non-image objects
    #
    for item in (None, b'hey!', 99, 7j, [], {}):
        with pytest.raises(TypeError):
            utils.to_base64(item)


def test_to_cv2():
    #
    # test path -> to_cv2
    #
    png = utils.to_cv2(PNG_PATH)
    assert isinstance(png, np.ndarray)
    assert np.array_equal(png[14, 106], [235, 245, 233])

    jpg = utils.to_cv2(JPG_PATH)
    assert isinstance(jpg, np.ndarray)
    assert np.array_equal(jpg[168, 231], (0, 0, 0))

    bmp = utils.to_cv2(BMP_PATH)
    assert isinstance(bmp, np.ndarray)
    assert np.array_equal(bmp[285, 454], (0, 249, 21))

    #
    # test to_base64 -> to_cv2
    #
    png = utils.to_cv2(utils.to_base64(PNG_PATH))
    assert isinstance(png, np.ndarray)
    assert np.array_equal(png[14, 106], [235, 245, 233])

    jpg = utils.to_cv2(utils.to_base64(JPG_PATH))
    assert isinstance(jpg, np.ndarray)
    assert np.array_equal(jpg[168, 231], (0, 0, 0))

    bmp = utils.to_cv2(utils.to_base64(BMP_PATH))
    assert isinstance(bmp, np.ndarray)
    assert np.array_equal(bmp[285, 454], (0, 249, 21))

    #
    # test to_cv2 -> to_cv2
    #
    assert np.array_equal(utils.to_cv2(utils.to_cv2(PNG_PATH)), utils.to_cv2(PNG_PATH))
    assert np.array_equal(utils.to_cv2(utils.to_cv2(JPG_PATH)), utils.to_cv2(JPG_PATH))
    assert np.array_equal(utils.to_cv2(utils.to_cv2(BMP_PATH)), utils.to_cv2(BMP_PATH))

    #
    # test to_pil -> to_cv2
    #
    png = utils.to_cv2(utils.to_pil(PNG_PATH))
    assert isinstance(png, np.ndarray)
    assert np.array_equal(png[14, 106], [235, 245, 233])

    jpg = utils.to_cv2(utils.to_pil(JPG_PATH))
    assert isinstance(jpg, np.ndarray)
    assert np.array_equal(jpg[168, 231], (0, 0, 0))

    bmp = utils.to_cv2(utils.to_pil(BMP_PATH))
    assert isinstance(bmp, np.ndarray)
    assert np.array_equal(bmp[285, 454], (0, 249, 21))

    #
    # test non-image objects
    #
    for item in (None, b'hey!', 99, 7j, [], {}):
        with pytest.raises(TypeError):
            utils.to_cv2(item)


def test_to_pil():
    #
    # test path -> to_pil
    #
    png = utils.to_pil(PNG_PATH)
    assert isinstance(png, Image.Image)
    assert np.array_equal(list(png.getdata())[10000], [221, 222, 230])

    jpg = utils.to_pil(JPG_PATH)
    assert isinstance(jpg, Image.Image)
    assert np.array_equal(list(jpg.getdata())[30000], [255, 255, 255])

    bmp = utils.to_pil(BMP_PATH)
    assert isinstance(bmp, Image.Image)
    assert np.array_equal(list(bmp.getdata())[30000], [192, 253, 235])

    #
    # test to_base64 -> to_pil
    #
    png = utils.to_pil(utils.to_base64(PNG_PATH))
    assert isinstance(png, Image.Image)
    assert np.array_equal(list(png.getdata())[10000], [221, 222, 230])

    jpg = utils.to_pil(utils.to_base64(JPG_PATH))
    assert isinstance(jpg, Image.Image)
    assert np.array_equal(list(jpg.getdata())[30000], [255, 255, 255])

    bmp = utils.to_pil(utils.to_base64(BMP_PATH))
    assert isinstance(bmp, Image.Image)
    assert np.array_equal(list(bmp.getdata())[30000], [192, 253, 235])

    #
    # test to_cv2 -> to_pil
    #
    png = utils.to_pil(utils.to_cv2(PNG_PATH))
    assert isinstance(png, Image.Image)
    assert np.array_equal(list(png.getdata())[10000], [221, 222, 230])

    jpg = utils.to_pil(utils.to_cv2(JPG_PATH))
    assert isinstance(jpg, Image.Image)
    assert np.array_equal(list(jpg.getdata())[30000], [255, 255, 255])

    bmp = utils.to_pil(utils.to_cv2(BMP_PATH))
    assert isinstance(bmp, Image.Image)
    assert np.array_equal(list(bmp.getdata())[30000], [192, 253, 235])

    #
    # test to_pil -> to_pil
    #
    png = utils.to_pil(utils.to_pil(PNG_PATH))
    assert isinstance(png, Image.Image)
    assert np.array_equal(list(png.getdata())[10000], [221, 222, 230])

    jpg = utils.to_pil(utils.to_pil(JPG_PATH))
    assert isinstance(jpg, Image.Image)
    assert np.array_equal(list(jpg.getdata())[30000], [255, 255, 255])

    bmp = utils.to_pil(utils.to_pil(BMP_PATH))
    assert isinstance(bmp, Image.Image)
    assert np.array_equal(list(bmp.getdata())[30000], [192, 253, 235])

    #
    # test non-image objects
    #
    for item in (None, b'hey!', 99, 7j, [], {}):
        with pytest.raises(TypeError):
            utils.to_cv2(item)


def test_save():
    temp = os.path.join(tempfile.gettempdir(), 'rpi-ocr-temp-image')

    #
    # test path -> to_base64
    #
    img = utils.to_base64(PNG_PATH)
    filename = temp + '.png'
    utils.save(img, filename)
    assert img[:10] == utils.to_base64(filename)[:10]
    os.remove(filename)

    img = utils.to_base64(JPG_PATH)
    filename = temp + '.jpeg'
    utils.save(img, filename)
    assert img[:10] == utils.to_base64(filename)[:10]
    os.remove(filename)

    img = utils.to_base64(BMP_PATH)
    filename = temp + '.bmp'
    utils.save(img, filename)
    assert img[:10] == utils.to_base64(filename)[:10]
    os.remove(filename)

    #
    # test path -> to_cv2
    #
    img = utils.to_cv2(ROOT + '/colour.png')
    filename = temp + '.png'
    utils.save(img, filename)
    assert np.array_equal(img, utils.to_cv2(filename))
    os.remove(filename)

    img = utils.to_cv2(ROOT + '/colour.bmp')
    filename = temp + '.bmp'
    utils.save(img, filename)
    assert np.array_equal(img, utils.to_cv2(filename))
    os.remove(filename)

    img = utils.to_cv2(ROOT + '/colour.jpeg')
    filename = temp + '.jpeg'
    utils.save(img, filename)
    for i in range(15):  # the arrays do not equal at some point but the saved image looks the same as the original
        assert np.array_equal(img[:, i], utils.to_cv2(filename)[:, i])
    os.remove(filename)
