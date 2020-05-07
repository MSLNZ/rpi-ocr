import os
import base64
import tempfile

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
            utils.save(new_image, original_image)
            raw = utils.to_bytes(new_image)
            assert raw.startswith(utils.SIGNATURE_MAP[ext])
            os.remove(new_image)  # cleanup
            assert not os.path.isfile(new_image)

    save_to_path = base_path + '.jpg'

    utils.save(save_to_path, JPG_PATH)
    assert utils.to_bytes(save_to_path).startswith(utils.SIGNATURE_MAP['jpg'])

    utils.save(save_to_path, utils.to_base64(JPG_PATH))
    assert utils.to_bytes(save_to_path).startswith(utils.SIGNATURE_MAP['jpg'])

    utils.save(save_to_path, utils.to_cv2(JPG_PATH))
    assert utils.to_bytes(save_to_path).startswith(utils.SIGNATURE_MAP['jpg'])

    utils.save(save_to_path, utils.to_pil(JPG_PATH))
    assert utils.to_bytes(save_to_path).startswith(utils.SIGNATURE_MAP['jpg'])

    utils.save(save_to_path, utils.to_pil(utils.to_base64(JPG_PATH)))
    assert utils.to_bytes(save_to_path).startswith(utils.SIGNATURE_MAP['jpg'])

    utils.save(save_to_path, utils.to_base64(utils.to_pil(utils.to_base64(JPG_PATH))))
    assert utils.to_bytes(save_to_path).startswith(utils.SIGNATURE_MAP['jpg'])

    # cleanup
    os.remove(save_to_path)
    assert not os.path.isfile(save_to_path)


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

    # invalid str
    for obj in ['does/not/exist.jpg', 'X'*10000 + '.png']:
        with pytest.raises(ValueError, match=r'^Invalid path or base64 string'):
            utils.to_bytes(obj)

    for obj in [1, 2.0, None, True, bytearray(), [], Image.ImageTransformHandler()]:
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

    # invalid str
    for obj in ['does/not/exist.jpg', 'X'*10000 + '.png']:
        with pytest.raises(ValueError, match=r'^Invalid path or base64 string'):
            utils.to_base64(obj)

    for obj in [1, 2.0, None, True, bytearray(), [], Image.ImageTransformHandler()]:
        with pytest.raises(TypeError, match=r'^Cannot convert'):
            utils.to_base64(obj)


def test_to_pil():
    items = [(PNG_PATH, 'png'), (JPG_PATH, 'jpg'), (BMP_PATH, 'bmp')]
    for path, key in items:

        # cv2 -> PIL
        cv2 = utils.to_cv2(path)
        assert isinstance(cv2, utils.OpenCVImage)
        assert cv2.ext == '.'+key
        cv2_pil = utils.to_pil(cv2)
        assert isinstance(cv2_pil, utils.PillowImage)
        assert cv2_pil.format == key.upper()
        assert cv2_pil.mode == 'RGB'
        assert cv2_pil.height == cv2.shape[0]
        assert cv2_pil.width == cv2.shape[1]
        assert len(cv2_pil.getbands()) == cv2.shape[2]
        assert np.array_equal(cv2_pil, cv2)

        # file path (str) -> PIL
        # base64 (str) -> PIL
        # bytes -> PIL
        with open(path, 'rb') as fp:
            raw = fp.read()
        img_expected = Image.open(path).convert(mode='RGB')
        for obj in [path, base64.b64encode(raw).decode('ascii'), raw]:
            assert isinstance(obj, (str, bytes))
            pil = utils.to_pil(obj)
            assert isinstance(pil, utils.PillowImage)
            if key == 'jpg':
                assert pil.format == 'JPEG'
            else:
                assert pil.format == key.upper()
            assert pil.mode == 'RGB'
            assert img_expected.mode == pil.mode
            assert img_expected.size == pil.size
            assert img_expected.info == pil.info
            assert img_expected.category == pil.category
            assert img_expected.getpalette() == pil.getpalette()
            assert img_expected.tobytes() == pil.tobytes()
            assert pil.height == cv2.shape[0]  # compare to cv2 result
            assert pil.width == cv2.shape[1]
            assert len(pil.getbands()) == cv2.shape[2]

            # PIL -> PIL
            assert isinstance(img_expected, utils.PillowImage)
            assert utils.to_pil(img_expected) is img_expected

    # invalid str
    for obj in ['does/not/exist.jpg', 'X'*10000 + '.png']:
        with pytest.raises(ValueError, match=r'^Invalid path or base64 string'):
            utils.to_pil(obj)

    for obj in [1, 2.0, None, True, bytearray(), [], Image.ImageTransformHandler()]:
        with pytest.raises(TypeError, match=r'^Cannot convert'):
            utils.to_pil(obj)


def test_to_cv2():
    items = [(PNG_PATH, '.png'), (JPG_PATH, '.jpg'), (BMP_PATH, '.bmp')]
    for path, ext in items:
        expected_img = opencv.imread(path)[:, :, [2, 1, 0]]  # convert BGR to RGB

        # PIL -> cv2
        pil = Image.open(path)
        cv2 = utils.to_cv2(pil)
        assert isinstance(pil, utils.PillowImage)
        assert isinstance(cv2, utils.OpenCVImage)
        assert cv2.ext == '.'+pil.format
        assert cv2.shape[:2] == pil.size[::-1]
        assert np.array_equal(pil, cv2)

        # PIL (with format attribute = None) -> cv2
        pil.format = None
        cv2 = utils.to_cv2(pil)
        assert isinstance(pil, utils.PillowImage)
        assert isinstance(cv2, utils.OpenCVImage)
        assert cv2.ext == utils.DEFAULT_FILE_EXTENSION

        # file path (str) -> cv2
        cv2 = utils.to_cv2(path)
        assert isinstance(cv2, utils.OpenCVImage)
        assert cv2.ext == ext
        assert np.array_equal(expected_img, cv2)

        # base64 (str) -> cv2
        with open(path, 'rb') as fp:
            b64 = base64.b64encode(fp.read()).decode('ascii')
        cv2 = utils.to_cv2(b64)
        assert isinstance(b64, str)
        assert isinstance(cv2, utils.OpenCVImage)
        assert cv2.ext == ext
        assert np.array_equal(expected_img, cv2)

        # bytes -> cv2
        with open(path, 'rb') as fp:
            raw = fp.read()
        cv2 = utils.to_cv2(raw)
        assert isinstance(raw, bytes)
        assert isinstance(cv2, utils.OpenCVImage)
        assert cv2.ext == ext
        assert np.array_equal(expected_img, cv2)

        # ndarray -> cv2
        array = np.arange(100)
        cv2 = utils.to_cv2(array)
        assert isinstance(array, np.ndarray)
        assert isinstance(cv2, utils.OpenCVImage)
        assert cv2.ext == utils.DEFAULT_FILE_EXTENSION
        assert np.array_equal(array, cv2)

        # cv2 -> cv2
        assert utils.to_cv2(cv2) is cv2

    # invalid str
    for obj in ['does/not/exist.jpg', 'X'*10000 + '.png']:
        with pytest.raises(ValueError, match=r'^Invalid path or base64 string'):
            utils.to_cv2(obj)

    for obj in [1, 2.0, None, True, bytearray(), [], Image.ImageTransformHandler()]:
        with pytest.raises(TypeError, match=r'^Cannot convert'):
            utils.to_cv2(obj)


def test_threshold():
    cv2 = utils.to_cv2(PNG_PATH)
    cv2_th = utils.threshold(cv2, 100)
    assert isinstance(cv2_th, utils.OpenCVImage)
    assert cv2_th.ext == cv2.ext

    pil = utils.to_pil(PNG_PATH)
    pil_th = utils.threshold(pil, 100)
    assert isinstance(pil_th, utils.PillowImage)
    assert pil_th.format == pil.format

    assert np.array_equal(cv2, pil)
    assert np.array_equal(cv2_th, pil_th)

    with pytest.raises(TypeError, match='Pillow or OpenCV'):
        utils.threshold(np.arange(10), 100)


def test_erode():
    cv2 = utils.to_cv2(PNG_PATH)
    pil = utils.to_pil(PNG_PATH)
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

    with pytest.raises(TypeError, match='Pillow or OpenCV'):
        utils.erode(np.arange(10), 1, 1)


def test_dilate():
    cv2 = utils.to_cv2(PNG_PATH)
    pil = utils.to_pil(PNG_PATH)
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

    with pytest.raises(TypeError, match='Pillow or OpenCV'):
        utils.dilate(np.arange(10), 1, 1)


def test_gaussian_blur():
    cv2 = utils.to_cv2(PNG_PATH)
    pil = utils.to_pil(PNG_PATH)
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

    with pytest.raises(TypeError, match='Pillow or OpenCV'):
        utils.gaussian_blur(np.arange(10), 1)


def test_rotate():
    cv2 = utils.to_cv2(PNG_PATH)
    pil = utils.to_pil(PNG_PATH)
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

    assert pil_rot.size[::-1] == cv2_rot.shape[:2]

    with pytest.raises(TypeError, match='Pillow or OpenCV'):
        utils.rotate(np.arange(10), 10)


def test_zoom():
    cv2 = utils.to_cv2(JPG_PATH)
    pil = utils.to_pil(JPG_PATH)
    assert np.array_equal(cv2, pil)

    width, height = list(map(float, pil.size))

    cv2_z = utils.zoom(cv2, 200, 100, 180, 200)
    assert isinstance(cv2_z, utils.OpenCVImage)
    assert cv2_z.ext == cv2.ext
    assert cv2_z.shape == (200, 180, 3)

    cv2_z2 = utils.zoom(cv2, 200./width, 100./height, 180./width, 200./height)
    assert np.array_equal(cv2_z, cv2_z2)

    pil_z = utils.zoom(pil, 200, 100, 180, 200)
    assert isinstance(pil_z, utils.PillowImage)
    assert pil_z.format == pil.format
    assert pil_z.size == (180, 200)

    pil_z2 = utils.zoom(pil, 200./width, 100./height, 180./width, 200./height)
    assert np.array_equal(pil_z, pil_z2)

    assert np.array_equal(cv2_z, pil_z)

    with pytest.raises(TypeError, match='Pillow or OpenCV'):
        utils.zoom(np.arange(10), 200, 100, 180, 200)
