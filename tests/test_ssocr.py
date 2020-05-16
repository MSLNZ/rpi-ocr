import os
import sys
import tempfile

import pytest

import ocr
from ocr.ssocr import (
    set_ssocr_path,
    ssocr,
    version,
    Colour,
    Luminance,
    Charset,
)

six_digits_path = os.path.join(os.path.dirname(__file__), 'images', 'six_digits.png')
inside_box_path = os.path.join(os.path.dirname(__file__), 'images', 'inside_box.png')


# NOTE: This test must be first function in this module
# because it adds the ssocr executable to the PATH
def test_environ_path():
    ssorc_exe = 'ssocr'
    if sys.platform == 'win32':
        ssorc_exe += '.exe'

    # make sure the executable is not available on PATH
    environ_path = None
    for path in os.environ['PATH'].split(os.pathsep):
        if os.path.isfile(os.path.join(path, ssorc_exe)):
            environ_path = path
            os.environ['PATH'] = os.environ['PATH'].replace(path, '')
            break

    # check that the error message is correct when the ssocr executable is not available
    with pytest.raises(FileNotFoundError, match=r'ocr.set_ssocr_path()'):
        ssocr(six_digits_path, absolute_threshold=False)

    # make sure that the ssocr executable is available for the remainder of the tests in this module
    if environ_path:
        os.environ['PATH'] += os.pathsep + environ_path
    elif sys.platform == 'win32':
        # set the path to ssocr.exe
        set_ssocr_path(os.path.join(os.path.dirname(__file__), '..', 'resources', 'ssocr-win64', 'bin', 'ssocr.exe'))


def test_invalid_image():
    # must raise ValueError instead of FileNotFoundError
    for obj in ['does/not/exist.jpg', 'X'*10000 + '.png']:
        with pytest.raises(ValueError, match=r'^Invalid path or Base64 string'):
            ssocr(obj)


def test_six_digits():
    expected = '431432'

    temp_paths = [tempfile.gettempdir() + '/six_digits.' + ext
                  for ext in ['bmp', 'jpg', 'jpeg', 'png', 'tif', 'tiff']]

    kwargs = {'absolute_threshold': False, 'iter_threshold': True}

    for p in temp_paths:
        ocr.save(six_digits_path, p)

        assert ocr.ssocr(p, **kwargs) == expected
        assert ocr.ssocr(ocr.utils.to_bytes(p), **kwargs) == expected
        with open(p, 'rb') as fp:
            assert ocr.ssocr(fp.read(), **kwargs) == expected
        assert ocr.ssocr(ocr.utils.to_base64(p), **kwargs) == expected
        assert ocr.ssocr(ocr.utils.to_cv2(p), **kwargs) == expected
        assert ocr.ssocr(ocr.utils.to_pil(p), **kwargs) == expected

        for fcn in [ocr.utils.to_cv2, ocr.utils.to_pil]:
            cropped = ocr.utils.crop(fcn(p), 0, 0, 100, 73)
            assert ocr.ssocr(cropped, **kwargs) == expected[:2]

        os.remove(p)
        assert not os.path.isfile(p)

    for obj in ['does/not/exist.jpg', 'X'*10000 + '.png']:
        with pytest.raises(ValueError, match=r'^Invalid path or Base64 string'):
            ocr.ssocr(obj)


def test_inside_box():
    expected = '086861'
    threshold = 21.  # as a percentage
    cv2 = ocr.utils.to_cv2(inside_box_path)
    pil = ocr.utils.to_pil(inside_box_path)
    for obj in [cv2, pil]:
        cropped = ocr.utils.crop(obj, 230, 195, 220, 60)
        assert ocr.ssocr(cropped, threshold=threshold, absolute_threshold=False) == expected

        thresholded = ocr.utils.threshold(cropped, 255 * threshold/100.)
        assert ocr.ssocr(thresholded) == expected


def test_version():
    assert version() == '2.19.0+'

    info = version(include_copyright=True)
    assert info.startswith('Seven Segment Optical Character Recognition')
    assert '@unix-ag.uni-kl.de' in info


def test_set_ssocr_path():
    # the file exists but the basename is not ssocr[.exe]
    for path in [__file__, six_digits_path]:
        assert os.path.isfile(path)
        with pytest.raises(FileNotFoundError, match='Invalid'):
            set_ssocr_path(path)

    # a valid top-level directory but cannot find the ssocr executable
    for path in [os.path.dirname(__file__)]:
        assert os.path.isdir(path)
        with pytest.raises(FileNotFoundError, match='Cannot find'):
            set_ssocr_path(path)

    # not a file nor a directory
    for path in ['invalid/ssocr', '/does/not/exist/ssocr.exe', 'ssocr.exe']:
        assert not os.path.exists(path)
        with pytest.raises(FileNotFoundError, match='not a valid file or directory'):
            set_ssocr_path(path)

    # ensure that this does not raise an exception
    if sys.platform == 'win32':
        # finds the ssocr.exe executable in the rpi-ocr/resources/ssocr-win64 directory
        root = os.path.join(os.path.dirname(__file__), '..')
        set_ssocr_path(root)
    else:
        set_ssocr_path('/usr/local/bin/ssocr')


def test_enums():
    for obj in ['BLACK', 'black', Colour.BLACK]:
        assert Colour.get_value(obj) == 'black'

    for obj in ['WHITE', 'white', Colour.WHITE]:
        assert Colour.get_value(obj) == 'white'

    for obj in ['Digits', 'digits', Charset.DIGITS]:
        assert Charset.get_value(obj) == 'digits'

    for obj in ['DECIMAL', 'decimal', Charset.DECIMAL]:
        assert Charset.get_value(obj) == 'decimal'

    for obj in ['HEX', 'hex', Charset.HEX]:
        assert Charset.get_value(obj) == 'hex'

    for obj in ['FULL', 'full', Charset.FULL]:
        assert Charset.get_value(obj) == 'full'

    for obj in ['REC601', 'rec601', Luminance.REC601]:
        assert Luminance.get_value(obj) == 'rec601'

    for obj in ['REC709', 'rec709', Luminance.REC709]:
        assert Luminance.get_value(obj) == 'rec709'

    for obj in ['LINEAR', 'linear', Luminance.LINEAR]:
        assert Luminance.get_value(obj) == 'linear'

    for obj in ['MINIMUM', 'minimum', Luminance.MINIMUM]:
        assert Luminance.get_value(obj) == 'minimum'

    for obj in ['MAXIMUM', 'maximum', Luminance.MAXIMUM]:
        assert Luminance.get_value(obj) == 'maximum'

    for obj in ['RED', 'red', Luminance.RED]:
        assert Luminance.get_value(obj) == 'red'

    for obj in ['GREEN', 'green', Luminance.GREEN]:
        assert Luminance.get_value(obj) == 'green'

    for obj in ['BLUE', 'blue', Luminance.BLUE]:
        assert Luminance.get_value(obj) == 'blue'

    with pytest.raises(ValueError, match=r'does not contain'):
        Colour.get_value('invalid')

    with pytest.raises(ValueError, match=r'does not contain'):
        Charset.get_value('invalid')

    with pytest.raises(ValueError, match=r'does not contain'):
        Luminance.get_value('invalid')

    with pytest.raises(TypeError):
        Luminance.get_value(1)


def test_debug_enabled():
    out = ocr.ssocr(six_digits_path, iter_threshold=True, absolute_threshold=False, debug=True)
    assert out.startswith('======')
    assert 'image width: 280\nimage height: 73' in out
    assert 'Display as seen by ssocr:' in out
    assert out.endswith('431432')


def test_hexadecimal_enabled():
    out = ocr.ssocr(six_digits_path, iter_threshold=True, absolute_threshold=False, as_hex=True)
    assert out == '2e:6d:24:2e:6d:5d'


def test_absolute_threshold_enabled():
    with pytest.raises(RuntimeError, match=r'found only 1 of 6 digits'):
        ocr.ssocr(six_digits_path, absolute_threshold=True, num_digits=6)


def test_omit_decimal_point():
    out = ocr.ssocr(six_digits_path, iter_threshold=True, absolute_threshold=False, omit_decimal_point=True)
    assert out == '431432'
