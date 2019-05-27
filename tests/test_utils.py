import os

import pytest
import numpy as np
from PIL import Image

from rpi_ocr import utils

img_path = os.path.join(os.path.dirname(__file__), 'images')
png_path = os.path.join(os.path.dirname(__file__), 'images', 'ssocr_website.png')
jpg_path = os.path.join(os.path.dirname(__file__), 'images', 'tesseract_eng_numbers.jpg')
bmp_path = os.path.join(os.path.dirname(__file__), 'images', 'colour.bmp')


def test_to_base64():

    # test path
    png = utils.to_base64(png_path)
    assert isinstance(png, str)
    assert png.startswith('iVBOR')

    jpg = utils.to_base64(jpg_path)
    assert isinstance(jpg, str)
    assert jpg.startswith('/9j/4')

    bmp = utils.to_base64(bmp_path)
    assert isinstance(bmp, str)
    assert bmp.startswith('Qk02u')

    # test base64
    assert utils.to_base64(png) is png
    assert utils.to_base64(jpg) is jpg
    assert utils.to_base64(bmp) is bmp

    # test cv2
    # to_base64 always returns a jpg image type
    png = utils.to_base64(utils.to_cv2(png_path))
    assert isinstance(png, str)
    assert png.startswith('/9j/4')

    jpg = utils.to_base64(utils.to_cv2(jpg_path))
    assert isinstance(jpg, str)
    assert jpg.startswith('/9j/4')

    bmp = utils.to_base64(utils.to_cv2(bmp_path))
    assert isinstance(bmp, str)
    assert bmp.startswith('/9j/4')

    # test PIL
    # to_base64 always returns a PNG image type
    png = utils.to_base64(utils.to_pil(png_path))
    assert isinstance(png, str)
    assert png.startswith('/9j/4')

    jpg = utils.to_base64(utils.to_pil(jpg_path))
    assert isinstance(jpg, str)
    assert jpg.startswith('/9j/4')

    bmp = utils.to_base64(utils.to_pil(bmp_path))
    assert isinstance(bmp, str)
    assert bmp.startswith('/9j/4')

    # test non-image objects
    for item in (None, b'hey!', 99, 7j, [], {}):
        with pytest.raises(TypeError):
            utils.to_base64(item)


def test_to_cv2():
    # test path
    png = utils.to_cv2(png_path)
    assert isinstance(png, np.ndarray)
    assert np.array_equal(png[14, 106], [235, 245, 233])

    jpg = utils.to_cv2(jpg_path)
    assert isinstance(jpg, np.ndarray)
    assert np.array_equal(jpg[168, 231], (0, 0, 0))

    bmp = utils.to_cv2(bmp_path)
    assert isinstance(bmp, np.ndarray)
    assert np.array_equal(bmp[285, 454], (0, 249, 21))

    # test base64
    png = utils.to_cv2(utils.to_base64(png_path))
    assert isinstance(png, np.ndarray)
    assert np.array_equal(png[14, 106], [235, 245, 233])

    jpg = utils.to_cv2(utils.to_base64(jpg_path))
    assert isinstance(jpg, np.ndarray)
    assert np.array_equal(jpg[168, 231], (0, 0, 0))

    bmp = utils.to_cv2(utils.to_base64(bmp_path))
    assert isinstance(bmp, np.ndarray)
    assert np.array_equal(bmp[285, 454], (0, 249, 21))

    # test cv2
    assert np.array_equal(utils.to_cv2(utils.to_cv2(png_path)), utils.to_cv2(png_path))
    assert np.array_equal(utils.to_cv2(utils.to_cv2(jpg_path)), utils.to_cv2(jpg_path))
    assert np.array_equal(utils.to_cv2(utils.to_cv2(bmp_path)), utils.to_cv2(bmp_path))

    # test PIL
    png = utils.to_cv2(utils.to_pil(png_path))
    assert isinstance(png, np.ndarray)
    assert np.array_equal(png[14, 106], [235, 245, 233])

    jpg = utils.to_cv2(utils.to_pil(jpg_path))
    assert isinstance(jpg, np.ndarray)
    assert np.array_equal(jpg[168, 231], (0, 0, 0))

    bmp = utils.to_cv2(utils.to_pil(bmp_path))
    assert isinstance(bmp, np.ndarray)
    assert np.array_equal(bmp[285, 454], (0, 249, 21))

    # test non-image objects
    for item in (None, b'hey!', 99, 7j, [], {}):
        with pytest.raises(TypeError):
            utils.to_cv2(item)


def test_to_pil():
    # test path
    png = utils.to_pil(png_path)
    assert isinstance(png, Image.Image)
    assert np.array_equal(list(png.getdata())[10000], [221, 222, 230])

    jpg = utils.to_pil(jpg_path)
    assert isinstance(jpg, Image.Image)
    assert np.array_equal(list(jpg.getdata())[30000], [255, 255, 255])

    bmp = utils.to_pil(bmp_path)
    assert isinstance(bmp, Image.Image)
    assert np.array_equal(list(bmp.getdata())[30000], [192, 253, 235])

    # test base64
    png = utils.to_pil(utils.to_base64(png_path))
    assert isinstance(png, Image.Image)
    assert np.array_equal(list(png.getdata())[10000], [221, 222, 230])

    jpg = utils.to_pil(utils.to_base64(jpg_path))
    assert isinstance(jpg, Image.Image)
    assert np.array_equal(list(jpg.getdata())[30000], [255, 255, 255])

    bmp = utils.to_pil(utils.to_base64(bmp_path))
    assert isinstance(bmp, Image.Image)
    assert np.array_equal(list(bmp.getdata())[30000], [192, 253, 235])

    # test cv2
    png = utils.to_pil(utils.to_cv2(png_path))
    assert isinstance(png, Image.Image)
    assert np.array_equal(list(png.getdata())[10000], [221, 222, 230])

    jpg = utils.to_pil(utils.to_cv2(jpg_path))
    assert isinstance(jpg, Image.Image)
    assert np.array_equal(list(jpg.getdata())[30000], [255, 255, 255])

    bmp = utils.to_pil(utils.to_cv2(bmp_path))
    assert isinstance(bmp, Image.Image)
    assert np.array_equal(list(bmp.getdata())[30000], [192, 253, 235])

    # test PIL
    png = utils.to_pil(utils.to_pil(png_path))
    assert isinstance(png, Image.Image)
    assert np.array_equal(list(png.getdata())[10000], [221, 222, 230])

    jpg = utils.to_pil(utils.to_pil(jpg_path))
    assert isinstance(jpg, Image.Image)
    assert np.array_equal(list(jpg.getdata())[30000], [255, 255, 255])

    bmp = utils.to_pil(utils.to_pil(bmp_path))
    assert isinstance(bmp, Image.Image)
    assert np.array_equal(list(bmp.getdata())[30000], [192, 253, 235])

    # test non-image objects
    for item in (None, b'hey!', 99, 7j, [], {}):
        with pytest.raises(TypeError):
            utils.to_cv2(item)


def test_save_as_jpeg():
    # test base64
    png = utils.to_base64(png_path)
    utils.save_as_jpeg(png, os.path.join(img_path, 'png.jpeg'))
    png_new = utils.to_base64(os.path.join(img_path, 'png.jpeg'))
    assert png_new.startswith('/9j/4')
    os.remove(os.path.join(img_path, 'png.jpeg'))

    jpg = utils.to_base64(jpg_path)
    utils.save_as_jpeg(jpg, os.path.join(img_path, 'jpg.jpeg'))
    jpg_new = utils.to_base64(os.path.join(img_path, 'jpg.jpeg'))
    assert jpg_new.startswith('/9j/4')
    os.remove(os.path.join(img_path, 'jpg.jpeg'))

    bmp = utils.to_base64(bmp_path)
    utils.save_as_jpeg(bmp, os.path.join(img_path, 'bmp.jpeg'))
    bmp_new = utils.to_base64(os.path.join(img_path, 'bmp.jpeg'))
    assert bmp_new.startswith('/9j/4')
    os.remove(os.path.join(img_path, 'bmp.jpeg'))

    # test cv2
    png = utils.to_cv2(png_path)
    utils.save_as_jpeg(png, os.path.join(img_path, 'png.jpeg'))
    png_new = utils.to_cv2(os.path.join(img_path, 'png.jpeg'))
    assert np.array_equal(png[71, 0], png_new[71, 0])
    os.remove(os.path.join(img_path, 'png.jpeg'))

    jpg = utils.to_cv2(jpg_path)
    utils.save_as_jpeg(jpg, os.path.join(img_path, 'jpg.jpeg'))
    jpg_new = utils.to_cv2(os.path.join(img_path, 'jpg.jpeg'))
    assert np.array_equal(jpg[168, 233], jpg_new[168, 233])
    os.remove(os.path.join(img_path, 'jpg.jpeg'))

    bmp = utils.to_cv2(bmp_path)
    utils.save_as_jpeg(bmp, os.path.join(img_path, 'bmp.jpeg'))
    bmp_new = utils.to_cv2(os.path.join(img_path, 'bmp.jpeg'))
    assert np.array_equal(bmp[199, 224], bmp_new[199, 224])
    os.remove(os.path.join(img_path, 'bmp.jpeg'))

    # test PIL
    png = utils.to_pil(png_path)
    utils.save_as_jpeg(png, os.path.join(img_path, 'png.jpeg'))
    png_new = utils.to_pil(os.path.join(img_path, 'png.jpeg'))
    assert np.array_equal(list(png.getdata())[20005], list(png_new.getdata())[20005])
    os.remove(os.path.join(img_path, 'png.jpeg'))

    jpg = utils.to_pil(jpg_path)
    utils.save_as_jpeg(jpg, os.path.join(img_path, 'jpg.jpeg'))
    jpg_new = utils.to_pil(os.path.join(img_path, 'jpg.jpeg'))
    assert np.array_equal(list(jpg.getdata())[30000], list(jpg_new.getdata())[30000])
    os.remove(os.path.join(img_path, 'jpg.jpeg'))

    bmp = utils.to_pil(bmp_path)
    utils.save_as_jpeg(bmp, os.path.join(img_path, 'bmp.jpeg'))
    bmp_new = utils.to_pil(os.path.join(img_path, 'bmp.jpeg'))
    assert np.array_equal(list(bmp.getdata())[10000], list(bmp_new.getdata())[10000])
    os.remove(os.path.join(img_path, 'bmp.jpeg'))
