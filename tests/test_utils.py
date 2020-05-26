import os
import base64
import tempfile
from io import BytesIO

import pytest
import numpy as np
from PIL import Image
import cv2 as opencv

from ocr import utils

ROOT = os.path.join(os.path.dirname(__file__), 'images')
PNG_PATH = os.path.join(ROOT, 'six_digits.png')
JPG_PATH = os.path.join(ROOT, 'tesseract_numbers.jpg')
BMP_PATH = os.path.join(ROOT, 'colour.bmp')


def test_OpenCVImage_class():
    img = utils.OpenCVImage([1, 2, 3])
    assert isinstance(img, np.ndarray)
    assert isinstance(img, utils.OpenCVImage)
    assert isinstance(img[::2], utils.OpenCVImage)
    assert np.array_equal(img, [1, 2, 3])
    assert np.array_equal(img[::2], [1, 3])
    assert img[1] == 2
    assert img.ext == utils.DEFAULT_FILE_EXTENSION
    assert img[::2].ext == utils.DEFAULT_FILE_EXTENSION
    assert img.size == 3
    assert img.shape == (3,)
    assert img.ndim == 1

    img = utils.OpenCVImage([1, 2, 3], ext='.png')
    assert img.ext == '.png'

    regular_ndarray = np.arange(10)
    assert isinstance(regular_ndarray, np.ndarray)
    assert not isinstance(regular_ndarray, utils.OpenCVImage)


def test_save():
    base_path = tempfile.gettempdir() + '/rpi-ocr-temp-image.'
    exts = ['bmp', 'dib', 'jpg', 'jpeg', 'jpe', 'png', 'tif', 'tiff']

    for original_image in [BMP_PATH, PNG_PATH, JPG_PATH]:
        for ext in exts:
            new_image = base_path + ext
            utils.save(original_image, new_image)
            raw = utils.to_bytes(new_image)
            assert raw.startswith(utils.SIGNATURE_MAP[ext])
            os.remove(new_image)  # cleanup
            assert not os.path.isfile(new_image)

    save_to_path = base_path + '.jpg'

    utils.save(JPG_PATH, save_to_path)
    assert utils.to_bytes(save_to_path).startswith(utils.SIGNATURE_MAP['jpg'])

    utils.save(utils.to_base64(JPG_PATH), save_to_path)
    assert utils.to_bytes(save_to_path).startswith(utils.SIGNATURE_MAP['jpg'])

    utils.save(utils.to_cv2(JPG_PATH), save_to_path)
    assert utils.to_bytes(save_to_path).startswith(utils.SIGNATURE_MAP['jpg'])

    utils.save(utils.to_pil(JPG_PATH), save_to_path)
    assert utils.to_bytes(save_to_path).startswith(utils.SIGNATURE_MAP['jpg'])

    utils.save(utils.to_pil(utils.to_base64(JPG_PATH)), save_to_path)
    assert utils.to_bytes(save_to_path).startswith(utils.SIGNATURE_MAP['jpg'])

    utils.save(utils.to_base64(utils.to_pil(utils.to_base64(JPG_PATH))), save_to_path)
    assert utils.to_bytes(save_to_path).startswith(utils.SIGNATURE_MAP['jpg'])

    # cleanup
    os.remove(save_to_path)
    assert not os.path.isfile(save_to_path)


def test_save_with_text():
    temp_path = tempfile.gettempdir() + '/rpi-ocr-temp-image.jpg'

    for path in [PNG_PATH, JPG_PATH, BMP_PATH]:
        original = utils.to_cv2(path)
        _, ext = os.path.splitext(path)

        # don't specify a value for the `text` kwarg
        assert utils.save(original, temp_path) is original

        # the size of the text gets bigger which makes the width of the returned image to be bigger
        for scale in range(1, 11):
            for text in ['hello', 'hello\nworld', 'hello\nworld\nXXXXX\nXXXXXXXX\nXXXXXXXXXXXXXXXXXXXXX']:
                out = utils.save(original, temp_path, text=text, font_scale=scale)
                assert isinstance(out, utils.OpenCVImage)
                assert out.ext == ext
                x = (out.width - original.width) // 2
                y = out.height - original.height
                cropped = utils.crop(out, x, y, original.width, original.height)
                if path == JPG_PATH:  # greyscale image
                    crop_to_gray = opencv.cvtColor(cropped, opencv.COLOR_RGB2GRAY)
                    assert np.array_equal(original, crop_to_gray), path
                else:
                    assert np.array_equal(original, cropped), path

    os.remove(temp_path)


def test_to_bytes():
    items = [(PNG_PATH, 'png'), (JPG_PATH, 'jpg'), (BMP_PATH, 'bmp')]
    for path, key in items:
        signature = utils.SIGNATURE_MAP[key]
        with open(path, 'rb') as fp:
            bytes_expected = fp.read()

        # file path (str) -> bytes
        assert isinstance(path, str)
        assert os.path.isfile(path)
        bytes_path = utils.to_bytes(path)
        assert isinstance(bytes_path, bytes)
        assert bytes_path == bytes_expected

        # base64 (str) -> bytes
        b64 = utils.to_base64(path)
        assert isinstance(b64, str)
        bytes_base64 = utils.to_bytes(b64)
        assert isinstance(bytes_base64, bytes)
        assert bytes_base64 == bytes_expected

        # PIL -> bytes
        pil = utils.to_pil(path)
        assert isinstance(pil, utils.PillowImage)
        bytes_pil = utils.to_bytes(pil)
        assert isinstance(bytes_pil, bytes)
        assert bytes_pil.startswith(signature)

        # OpenCV -> bytes
        cv2 = utils.to_cv2(path)
        assert isinstance(cv2, utils.OpenCVImage)
        assert cv2.ext == '.'+key
        bytes_cv2 = utils.to_bytes(cv2)
        assert isinstance(bytes_cv2, bytes)
        assert bytes_cv2.startswith(signature)

    # bytes -> bytes
    b = b'get_out_whatever_is_sent_in'
    assert utils.to_bytes(b) is b

    # BytesIO -> bytes
    assert utils.to_bytes(BytesIO(b)) == b

    # BytesIO buffer -> bytes
    assert utils.to_bytes(BytesIO(b).getbuffer()) == b

    # bytearray -> bytes
    assert utils.to_bytes(bytearray(b)) == b

    # invalid str
    for obj in ['does/not/exist.jpg', 'X'*10000 + '.png']:
        with pytest.raises(ValueError, match=r'^Invalid path or Base64 string'):
            utils.to_bytes(obj)

    for obj in [1, 2.0, None, True, [], Image.ImageTransformHandler()]:
        with pytest.raises(TypeError, match=r'^Cannot convert'):
            utils.to_bytes(obj)


def test_to_base64():
    items = [(PNG_PATH, 'png'), (JPG_PATH, 'jpg'), (BMP_PATH, 'bmp')]
    for path, key in items:
        signature = base64.b64encode(utils.SIGNATURE_MAP[key]).decode('ascii')[:-1]
        with open(path, 'rb') as fp:
            base64_expected = base64.b64encode(fp.read()).decode('ascii')

        # file path (str) -> base64
        assert isinstance(path, str)
        assert os.path.isfile(path)
        base64_path = utils.to_base64(path)
        assert isinstance(base64_path, str)
        assert base64_path == base64_expected

        # base64 (str) -> base64
        b64 = utils.to_base64(base64_expected)
        assert isinstance(b64, str)
        assert b64 == base64_expected

        # PIL -> base64
        pil = utils.to_pil(path)
        assert isinstance(pil, utils.PillowImage)
        base64_pil = utils.to_base64(pil)
        assert isinstance(base64_pil, str)
        assert base64_pil.startswith(signature)

        # OpenCV -> base64
        cv2 = utils.to_cv2(path)
        assert isinstance(cv2, utils.OpenCVImage)
        assert cv2.ext == '.'+key
        base64_cv2 = utils.to_base64(cv2)
        assert isinstance(base64_cv2, str)
        assert base64_cv2.startswith(signature)

    # bytes -> base64
    b = b'get_out_whatever_is_sent_in'
    b64 = base64.b64encode(b).decode('ascii')
    assert isinstance(b64, str)
    assert utils.to_base64(b) == b64

    # BytesIO -> base64
    assert utils.to_base64(BytesIO(b)) == b64

    # BytesIO buffer -> base64
    assert utils.to_base64(BytesIO(b).getbuffer()) == b64

    # bytearray -> base64
    assert utils.to_base64(bytearray(b)) == b64

    # invalid str
    for obj in ['does/not/exist.jpg', 'X'*10000 + '.png']:
        with pytest.raises(ValueError, match=r'^Invalid path or Base64 string'):
            utils.to_base64(obj)

    for obj in [1, 2.0, None, True, [], Image.ImageTransformHandler()]:
        with pytest.raises(TypeError, match=r'^Cannot convert'):
            utils.to_base64(obj)


def test_to_pil():
    for path in [PNG_PATH, JPG_PATH, BMP_PATH]:
        img_expected = Image.open(path)
        _, ext = os.path.splitext(path)

        # cv2 -> PIL
        cv2 = utils.to_cv2(path)
        assert isinstance(cv2, utils.OpenCVImage)
        assert cv2.ext == ext
        assert cv2.height == img_expected.height
        assert cv2.width == img_expected.width
        cv2_pil = utils.to_pil(cv2)
        assert isinstance(cv2_pil, utils.PillowImage)
        assert cv2_pil.format == img_expected.format
        assert cv2_pil.mode == img_expected.mode
        assert cv2_pil.height == img_expected.height
        assert cv2_pil.width == img_expected.width
        assert cv2_pil.getbands() == img_expected.getbands()
        assert np.array_equal(cv2_pil, cv2)
        assert np.array_equal(cv2_pil, img_expected)

        # file path (str) -> PIL
        # base64 (str) -> PIL
        # bytes -> PIL
        # BytesIO -> PIL
        # BytesIO buffer -> PIL
        # bytearray -> PIL
        with open(path, 'rb') as fp:
            raw = fp.read()
        for obj in [path, base64.b64encode(raw).decode('ascii'), raw,
                    BytesIO(raw), BytesIO(raw).getbuffer(), bytearray(raw)]:
            pil = utils.to_pil(obj)
            assert isinstance(pil, utils.PillowImage)
            assert img_expected.format == pil.format
            assert img_expected.mode == pil.mode
            assert img_expected.size == pil.size
            assert img_expected.info == pil.info
            assert img_expected.category == pil.category
            assert img_expected.getpalette() == pil.getpalette()
            assert img_expected.tobytes() == pil.tobytes()
            assert img_expected.getbands() == pil.getbands()
            assert img_expected.height == pil.height
            assert img_expected.width == pil.width

        # PIL -> PIL
        assert isinstance(img_expected, utils.PillowImage)
        assert utils.to_pil(img_expected) is img_expected

    # invalid str
    for obj in ['does/not/exist.jpg', 'X'*10000 + '.png']:
        with pytest.raises(ValueError, match=r'^Invalid path or Base64 string'):
            utils.to_pil(obj)

    for obj in [1, 2.0, None, True, [], Image.ImageTransformHandler()]:
        with pytest.raises(TypeError, match=r'^Cannot convert'):
            utils.to_pil(obj)


def test_to_cv2():
    items = [(PNG_PATH, '.png'), (JPG_PATH, '.jpg'), (BMP_PATH, '.bmp')]
    for path, ext in items:
        image = opencv.imread(path, flags=-1)

        if path == JPG_PATH:
            expected_ndim = 2  # greyscale image
            expected = image
        else:
            expected_ndim = 3
            expected = image[:, :, [2, 1, 0]]  # convert BGR to RGB

        # PIL -> cv2
        pil = Image.open(path)
        cv2 = utils.to_cv2(pil)
        assert isinstance(pil, utils.PillowImage)
        assert isinstance(cv2, utils.OpenCVImage)
        assert cv2.ext == '.'+pil.format
        assert cv2.height == pil.height
        assert cv2.width == pil.width
        assert cv2.ndim == expected_ndim
        assert np.array_equal(pil, cv2)

        # PIL (with format attribute = None) -> cv2
        pil.format = None
        cv2 = utils.to_cv2(pil)
        assert isinstance(pil, utils.PillowImage)
        assert isinstance(cv2, utils.OpenCVImage)
        assert cv2.ext == utils.DEFAULT_FILE_EXTENSION
        assert np.array_equal(pil, cv2)

        # file path (str) -> cv2
        cv2 = utils.to_cv2(path)
        assert isinstance(cv2, utils.OpenCVImage)
        assert cv2.ext == ext
        assert np.array_equal(expected, cv2)

        # base64 (str) -> cv2
        with open(path, mode='rb') as fp:
            b64 = base64.b64encode(fp.read()).decode('ascii')
        cv2 = utils.to_cv2(b64)
        assert isinstance(b64, str)
        assert isinstance(cv2, utils.OpenCVImage)
        assert cv2.ext == ext
        assert np.array_equal(expected, cv2)

        # cv2 -> cv2
        assert isinstance(cv2, utils.OpenCVImage)
        assert utils.to_cv2(cv2) is cv2

        # bytes -> cv2
        with open(path, mode='rb') as fp:
            raw = fp.read()
        cv2 = utils.to_cv2(raw)
        assert isinstance(raw, bytes)
        assert isinstance(cv2, utils.OpenCVImage)
        assert cv2.ext == ext
        assert np.array_equal(expected, cv2)

        # BytesIO -> cv2
        with open(path, mode='rb') as fp:
            bio = BytesIO(fp.read())
        cv2 = utils.to_cv2(bio)
        assert isinstance(cv2, utils.OpenCVImage)
        assert cv2.ext == ext
        assert np.array_equal(expected, cv2)

        # BytesIO buffer -> cv2
        with open(path, mode='rb') as fp:
            bio = BytesIO(fp.read())
        cv2 = utils.to_cv2(bio.getbuffer())
        assert isinstance(cv2, utils.OpenCVImage)
        assert cv2.ext == ext
        assert np.array_equal(expected, cv2)

        # bytearray -> cv2
        with open(path, mode='rb') as fp:
            ba = bytearray(fp.read())
        cv2 = utils.to_cv2(ba)
        assert isinstance(cv2, utils.OpenCVImage)
        assert cv2.ext == ext
        assert np.array_equal(expected, cv2)

    # ndarray -> cv2
    array = np.arange(100)
    cv2 = utils.to_cv2(array)
    assert isinstance(array, np.ndarray)
    assert isinstance(cv2, utils.OpenCVImage)
    assert cv2.ext == utils.DEFAULT_FILE_EXTENSION
    assert np.array_equal(array, cv2)

    # invalid str
    for obj in ['does/not/exist.jpg', 'X'*10000 + '.png']:
        with pytest.raises(ValueError, match=r'^Invalid path or Base64 string'):
            utils.to_cv2(obj)

    # BufferedReader
    with pytest.raises(TypeError, match=r'^Cannot convert'):
        with open(JPG_PATH, mode='rb') as fp:
            utils.to_cv2(fp)

    for obj in [1, 2.0, None, True, Image.ImageTransformHandler()]:
        with pytest.raises(TypeError, match=r'^Cannot convert'):
            utils.to_cv2(obj)

    assert str(utils.to_cv2(PNG_PATH)).startswith('<OpenCVImage ext=.png size=280x73 at 0x')


def test_threshold():
    for path in [PNG_PATH, JPG_PATH, BMP_PATH]:
        cv2 = utils.to_cv2(path)
        cv2_th = utils.threshold(cv2, 100)
        assert isinstance(cv2_th, utils.OpenCVImage)
        assert cv2_th.ext == cv2.ext

        pil = utils.to_pil(path)
        pil_th = utils.threshold(pil, 100)
        assert isinstance(pil_th, utils.PillowImage)
        assert pil_th.format == pil.format

        assert np.array_equal(cv2, pil)
        assert np.array_equal(cv2_th, pil_th)

        if path == JPG_PATH:
            assert cv2_th.ndim == 2
            assert pil_th.mode == 'L'
        else:
            assert cv2_th.ndim == 3
            assert pil_th.mode == 'RGB'

        # threshold value is 0
        cv2_0 = utils.threshold(cv2, 0)
        pil_0 = utils.threshold(pil, 0)
        cv2_unique = np.unique(cv2_0)
        if path == PNG_PATH:
            assert np.array_equal(cv2_unique, [255])
            assert cv2_unique.height == 1
        else:  # image has a pixels with a value of 0, so 0 is still in it
            assert np.array_equal(cv2_unique, [0, 255])
            assert cv2_unique.height == 2
        assert cv2_unique.width == 0
        assert np.array_equal(cv2_0, pil_0)

        # threshold value is 255
        cv2_255 = utils.threshold(cv2, 255)
        pil_255 = utils.threshold(pil, 255)
        cv2_unique = np.unique(cv2_255)
        assert np.array_equal(cv2_unique, [0])
        assert cv2_unique.height == 1
        assert cv2_unique.width == 0
        assert np.array_equal(cv2_255, pil_255)

    with pytest.raises(TypeError, match='Pillow or OpenCV'):
        utils.threshold(np.arange(10), 100)


def test_erode():
    for path in [PNG_PATH, JPG_PATH, BMP_PATH]:
        cv2 = utils.to_cv2(path)
        pil = utils.to_pil(path)
        assert np.array_equal(cv2, pil)

        assert utils.erode(cv2, None) is cv2
        assert utils.erode(cv2, 0) is cv2
        assert utils.erode(cv2, 1, 0) is cv2
        assert utils.erode(pil, None) is pil
        assert utils.erode(pil, 0) is pil
        assert utils.erode(pil, 1, 0) is pil

        cv2_er = utils.erode(cv2, 2, 3)
        assert isinstance(cv2_er, utils.OpenCVImage)
        assert cv2_er.ext == cv2.ext

        pil_er = utils.erode(pil, 2, 3)
        assert isinstance(pil_er, utils.PillowImage)
        assert pil_er.format == pil.format

        assert np.array_equal(cv2_er, pil_er)

        if path == JPG_PATH:
            assert cv2_er.ndim == 2
            assert pil_er.mode == 'L'
        else:
            assert cv2_er.ndim == 3
            assert pil_er.mode == 'RGB'

    with pytest.raises(TypeError, match='Pillow or OpenCV'):
        utils.erode(np.arange(10), 1, 1)


def test_dilate():
    for path in [PNG_PATH, JPG_PATH, BMP_PATH]:
        cv2 = utils.to_cv2(path)
        pil = utils.to_pil(path)
        assert np.array_equal(cv2, pil)

        assert utils.dilate(cv2, None) is cv2
        assert utils.dilate(cv2, 0) is cv2
        assert utils.dilate(cv2, 1, 0) is cv2
        assert utils.dilate(pil, None) is pil
        assert utils.dilate(pil, 0) is pil
        assert utils.dilate(pil, 1, 0) is pil

        cv2_di = utils.dilate(cv2, 2, 3)
        assert isinstance(cv2_di, utils.OpenCVImage)
        assert cv2_di.ext == cv2.ext

        pil_di = utils.dilate(pil, 2, 3)
        assert isinstance(pil_di, utils.PillowImage)
        assert pil_di.format == pil.format

        assert np.array_equal(cv2_di, pil_di)

        if path == JPG_PATH:
            assert cv2_di.ndim == 2
            assert pil_di.mode == 'L'
        else:
            assert cv2_di.ndim == 3
            assert pil_di.mode == 'RGB'

    with pytest.raises(TypeError, match='Pillow or OpenCV'):
        utils.dilate(np.arange(10), 1, 1)


def test_gaussian_blur():
    for path in [PNG_PATH, JPG_PATH, BMP_PATH]:
        cv2 = utils.to_cv2(path)
        pil = utils.to_pil(path)
        assert np.array_equal(cv2, pil)

        assert utils.gaussian_blur(cv2, None) is cv2
        assert utils.gaussian_blur(cv2, 0) is cv2
        assert utils.gaussian_blur(pil, None) is pil
        assert utils.gaussian_blur(pil, 0) is pil

        cv2_gb = utils.gaussian_blur(cv2, 5)
        assert isinstance(cv2_gb, utils.OpenCVImage)
        assert cv2_gb.ext == cv2.ext

        pil_gb = utils.gaussian_blur(pil, 5)
        assert isinstance(pil_gb, utils.PillowImage)
        assert pil_gb.format == pil.format

        if path == JPG_PATH:
            assert cv2_gb.ndim == 2
            assert pil_gb.mode == 'L'
        else:
            assert cv2_gb.ndim == 3
            assert pil_gb.mode == 'RGB'

    with pytest.raises(TypeError, match='Pillow or OpenCV'):
        utils.gaussian_blur(np.arange(10), 1)


def test_rotate():
    for path in [PNG_PATH, JPG_PATH, BMP_PATH]:
        cv2 = utils.to_cv2(path)
        pil = utils.to_pil(path)
        assert np.array_equal(cv2, pil)

        assert utils.rotate(cv2, None) is cv2
        assert utils.rotate(cv2, 0) is cv2
        assert utils.rotate(pil, None) is pil
        assert utils.rotate(pil, 0) is pil

        cv2_rot = utils.rotate(cv2, 90)
        assert isinstance(cv2_rot, utils.OpenCVImage)
        assert cv2_rot.ext == cv2.ext
        assert np.array_equal(utils.rotate(cv2, -63), utils.rotate(cv2, 297))

        pil_rot = utils.rotate(pil, 90)
        assert isinstance(pil_rot, utils.PillowImage)
        assert pil_rot.format == pil.format

        if path == JPG_PATH:
            assert cv2_rot.ndim == 2
            assert pil_rot.mode == 'L'
        else:
            assert cv2_rot.ndim == 3
            assert pil_rot.mode == 'RGB'

        assert pil_rot.height == cv2_rot.height
        assert pil_rot.width == cv2_rot.width

    # the rotate function is also used to rotate a corner of a bounding box
    x, y, w, h = 100, 200, 50, 75
    corners = ((x, y), (x + w, y), (x + w, y + h), (x, y + h))
    rotated = utils.rotate(np.array([*corners[0], w, h]), 90)
    assert np.allclose(rotated, [y, -w])
    rotated = utils.rotate(np.array([*corners[1], w, h]), 90)
    assert np.allclose(rotated, [y, -x])
    rotated = utils.rotate(np.array([*corners[2], w, h]), 90)
    assert np.allclose(rotated, [y+h, -x])
    rotated = utils.rotate(np.array([*corners[3], w, h]), 90)
    assert np.allclose(rotated, [y+h, -w])

    # bounding box must have shape (4,) and be an ndarray
    with pytest.raises(ValueError, match=r'not enough values to unpack'):
        utils.rotate(np.array([1, 2]), 10)
    with pytest.raises(ValueError, match=r'too many values to unpack'):
        utils.rotate(np.array([1, 2, 3, 4, 5]), 10)
    with pytest.raises(TypeError, match=r'Pillow or OpenCV image$'):
        utils.rotate([100, 200, 300, 400], 10)  # must be an ndarray not a list


def test_zoom():
    x, y, w, h = 98, 7, 123, 32
    for path in [PNG_PATH, JPG_PATH, BMP_PATH]:
        cv2 = utils.to_cv2(path)
        pil = utils.to_pil(path)
        assert np.array_equal(cv2, pil)

        img_width, img_height = float(pil.width), float(pil.height)

        cv2_1 = utils.crop(cv2, x, y, w, h)
        assert isinstance(cv2_1, utils.OpenCVImage)
        assert cv2_1.ext == cv2.ext
        if path == JPG_PATH:
            assert cv2_1.shape == (h, w)  # greyscale
        else:
            assert cv2_1.shape == (h, w, 3), path

        cv2_2 = utils.crop(cv2, x/img_width, y/img_height, w/img_width, h/img_height)
        assert np.array_equal(cv2_1, cv2_2)

        pil_1 = utils.crop(pil, x, y, w, h)
        assert isinstance(pil_1, utils.PillowImage)
        assert pil_1.format == pil.format
        assert pil_1.size == (w, h)
        if path == JPG_PATH:
            assert pil_1.mode == 'L'
        else:
            assert pil_1.mode == 'RGB'

        pil_2 = utils.crop(pil, x/img_width, y/img_height, w/img_width, h/img_height)
        assert np.array_equal(pil_1, pil_2)
        assert np.array_equal(pil_1, cv2_1)

        with pytest.raises(TypeError, match='Pillow or OpenCV'):
            utils.crop(np.arange(10), x, y, w, h)


def test_greyscale():
    #
    # original is in RGB
    #
    cv2 = utils.to_cv2(BMP_PATH)
    assert cv2.shape == (720, 720, 3)

    pil = utils.to_pil(BMP_PATH)
    assert pil.mode == 'RGB'
    assert pil.size == (720, 720)
    assert pil.getbands() == ('R', 'G', 'B')

    cv2_grey = utils.greyscale(cv2)
    assert isinstance(cv2_grey, utils.OpenCVImage)
    assert cv2_grey.ext == '.bmp'
    assert cv2_grey.shape == (720, 720)

    pil_grey = utils.greyscale(pil)
    assert isinstance(pil_grey, utils.PillowImage)
    assert pil_grey.format == 'BMP'
    assert pil_grey.mode == 'L'
    assert pil_grey.size == (720, 720)
    assert pil_grey.getbands() == ('L',)

    #
    # original is already in greyscale
    #
    cv2 = utils.to_cv2(JPG_PATH)
    assert utils.greyscale(cv2) is cv2

    pil = utils.to_pil(JPG_PATH)
    assert utils.greyscale(pil) is pil


def test_invert():
    for path in [BMP_PATH, PNG_PATH, JPG_PATH]:
        _, ext = os.path.splitext(path)
        cv2 = utils.to_cv2(path)
        pil = utils.to_pil(path)
        assert np.array_equal(cv2, pil)

        mn, mx = np.min(cv2), np.max(cv2)

        cv2_inv = utils.invert(cv2)
        assert isinstance(cv2_inv, utils.OpenCVImage)
        assert cv2_inv.ext == ext
        assert 255-mn == np.max(cv2_inv)
        assert 255-mx == np.min(cv2_inv)

        pil_inv = utils.invert(pil)
        assert isinstance(pil_inv, utils.PillowImage)
        assert pil_inv.format == pil.format
        assert np.array_equal(cv2_inv, pil_inv)


def test_adaptive_threahold():
    for path in [BMP_PATH, PNG_PATH, JPG_PATH]:
        _, ext = os.path.splitext(path)
        cv2 = utils.greyscale(utils.to_cv2(path))
        pil = utils.greyscale(utils.to_pil(path))

        cv2_at = utils.adaptive_threshold(cv2)
        assert isinstance(cv2_at, utils.OpenCVImage)
        assert cv2_at.ext == ext

        cv2_unique = np.unique(cv2_at)
        assert np.array_equal(cv2_unique, [0, 255])
        assert cv2_unique.height == 2
        assert cv2_unique.width == 0

        pil_at = utils.adaptive_threshold(pil)
        assert isinstance(pil_at, utils.PillowImage)
        assert pil_at.format == pil.format
