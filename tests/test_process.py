import os
import sys
from collections import OrderedDict

import pytest
import numpy as np

import ocr


def test_wrong_datatype():
    # the data type of the first argument, "image",  is irrelevant since
    # the program never gets to the line where the "image" is used

    assert ocr.process(None, tasks=None) is None
    assert ocr.process(6, tasks={}) == 6
    assert ocr.process('hey', tasks=[]) == 'hey'

    if sys.version_info[:2] < (3, 6):
        with pytest.raises(TypeError, match=r'Python <3.6'):
            ocr.process(None, tasks={'erode': 3})

    with pytest.raises(ValueError, match=r'not enough values to unpack'):
        ocr.process(None, tasks=[('rotate',)])

    with pytest.raises(ValueError, match=r'too many values to unpack'):
        ocr.process(None, tasks=['rotate', 3])

    with pytest.raises(ValueError, match=r'too many values to unpack'):
        ocr.process(None, tasks=['erode', 3, 4])

    with pytest.raises(ValueError, match=r'too many values to unpack'):
        ocr.process(None, tasks=[('rotate', 2, 3)])

    with pytest.raises(AttributeError, match=r'no attribute \'invalid\''):
        ocr.process(None, tasks=[('invalid', 2)])

    with pytest.raises(TypeError, match=r'Pillow or OpenCV'):
        ocr.process(None, tasks=[('rotate', 90)])


def test_order_preserved():
    path = os.path.join(os.path.dirname(__file__), 'images', 'inside_box.png')

    # call each function manually
    manual = ocr.utils.zoom(ocr.utils.to_cv2(path), 100, 200, 300, 400)
    manual = ocr.utils.threshold(manual, 50)
    manual = ocr.utils.rotate(manual, 45)
    manual = ocr.utils.dilate(manual, 3, 2)
    manual = ocr.utils.gaussian_blur(manual, 3)
    manual = ocr.utils.erode(manual, 5, 2)

    tasks = [
        ('zoom', (100, 200, 300, 400)),
        ('threshold', 50),
        ('rotate', 45),
        ('dilate', (3, 2)),
        ('gaussian_blur', 3),
        ('erode', (5, 2)),
    ]
    processed = ocr.process(ocr.utils.to_cv2(path), tasks=tasks)
    assert np.array_equal(manual, processed)

    if sys.version_info[:2] < (3, 6):
        processed = ocr.process(ocr.utils.to_cv2(path), tasks=OrderedDict(tasks))
        assert np.array_equal(manual, processed)
    else:
        tasks = {
            'zoom': {'x': 100, 'y': 200, 'w': 300, 'h': 400},
            'threshold': 50,
            'rotate': {'angle': 45},
            'dilate': {'radius': 3, 'iterations': 2},
            'gaussian_blur': (3,),
            'erode': (5, 2),
        }
        processed = ocr.process(ocr.utils.to_cv2(path), tasks=tasks)
        assert np.array_equal(manual, processed)
