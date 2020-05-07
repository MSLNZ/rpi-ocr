import os
import sys
import math
import time

import numpy as np

from . import (
    ocr,
    ON_RPI,
)
from . import utils
from .utils import process

if not ON_RPI:
    import pyqtgraph as pg
    from msl.qt import (
        io,
        QtCore,
        QtGui,
        QtWidgets,
        application,
        excepthook,
        prompt,
        Thread,
        Worker
    )
else:
    Thread = object
    Worker = object

    class QtWidgets(object):
        QWidget = object


def configure(client, **kwargs):
    """Create a Qt application to interact with the image and the OCR algorithm.

    Parameters
    ----------
    client : :class:`~ocr.client.OCRClient`
        The client that is connected to the Raspberry Pi.
    kwargs
        All key-value pairs are passed to the :class:`Gui`.

    Returns
    -------
    :class:`dict`
        The OCR parameters.
    """
    sys.excepthook = excepthook
    app = application()
    gui = Gui(client, **kwargs)
    gui.show()
    app.exec()
    return gui.ocr_params


class Gui(QtWidgets.QWidget):

    def __init__(self, client, **kwargs):
        super(Gui, self).__init__()
        self.path = kwargs.pop('path', None)
        self.client = client
        self.original_image = None
        self.delta = 0.01  # the amount to translate image on UP DOWN LEFT RIGHT key presses
        self.client_queue = {}  # a queue of requests to send to the RPi
        self.close_event_occurred = False

        zoom = kwargs.get('zoom')
        if zoom:
            self.zoom_history = [zoom]  # (x, y, width, height) values between 0.0 and 1.0
        else:
            self.zoom_history = []

        self.ocr_params = {
            'zoom': zoom,
            'rotate': kwargs.get('rotate'),
            'threshold': kwargs.get('threshold'),
            'dilate': kwargs.get('dilate'),
            'erode': kwargs.get('erode'),
            'blur': kwargs.get('blur'),
            'algorithm': kwargs.get('algorithm', 'tesseract').lower(),
            'lang': kwargs.get('lang', 'eng').lower(),
        }

        self.ocr_label = QtWidgets.QLabel()
        self.ocr_label.setFont(QtGui.QFont('Helvetica', 14))

        # the canvas widget to display the image
        self.graphics_view = pg.GraphicsView(background=None)
        self.view_box = pg.ViewBox(invertY=True, lockAspect=True, enableMouse=False, enableMenu=False)
        self.graphics_view.setCentralItem(self.view_box)
        self.canvas = pg.ImageItem(axisOrder='row-major')
        self.view_box.setMouseMode(pg.ViewBox.RectMode)
        self.view_box.addItem(self.canvas)
        self.view_box.mouseDragEvent = self.select_zoom

        graphing_layout = QtWidgets.QVBoxLayout()
        graphing_layout.addWidget(self.ocr_label, alignment=QtCore.Qt.AlignCenter)
        graphing_layout.addWidget(self.graphics_view)

        # the container for all the image-processing widgets
        self.image_processing_group = QtWidgets.QGroupBox('Image Processing')

        # rotate
        self.rotate_label = QtWidgets.QLabel('<html>Rotate [0&deg;]</html>')
        self.rotate_slider = QtWidgets.QSlider(orientation=QtCore.Qt.Horizontal)
        self.rotate_slider.setToolTip('The angle to rotate the image')
        self.rotate_slider.setMinimum(-180)
        self.rotate_slider.setMaximum(180)
        self.rotate_slider.setSingleStep(1)
        self.rotate_slider.setPageStep(15)
        self.rotate_slider.valueChanged.connect(self.update_rotate)
        if self.ocr_params['rotate']:
            self.rotate_slider.setValue(self.ocr_params['rotate'])

        # Gaussian blur
        self.blur_label = QtWidgets.QLabel('Gaussian Blur [0]')
        self.blur_slider = QtWidgets.QSlider(orientation=QtCore.Qt.Horizontal)
        self.blur_slider.setToolTip('The pixel radius to use for the Gaussian blur')
        self.blur_slider.setMinimum(0)
        self.blur_slider.setMaximum(kwargs.pop('max_blur', 9))
        self.blur_slider.setSingleStep(1)
        self.blur_slider.valueChanged.connect(self.update_blur)
        if self.ocr_params['blur']:
            self.blur_slider.setValue(self.ocr_params['blur'])

        # threshold
        self.threshold_label = QtWidgets.QLabel('Threshold [0]')
        self.threshold_checkbox = QtWidgets.QCheckBox()
        self.threshold_checkbox.setToolTip('Apply thresholding?')
        self.threshold_checkbox.clicked.connect(self.update_threshold_checkbox)
        self.threshold_slider = QtWidgets.QSlider(orientation=QtCore.Qt.Horizontal)
        self.threshold_slider.setToolTip('The threshold value')
        self.threshold_slider.setMinimum(0)
        self.threshold_slider.setMaximum(255)
        self.threshold_slider.setSingleStep(1)
        self.threshold_slider.valueChanged.connect(self.update_threshold)
        if self.ocr_params['threshold']:
            self.threshold_slider.setValue(self.ocr_params['threshold'])
            self.threshold_checkbox.setChecked(True)
        else:
            self.threshold_slider.setEnabled(False)
            self.threshold_checkbox.setChecked(False)

        # dilate
        self.dilate_label = QtWidgets.QLabel('Dilate [0]')
        self.dilate_slider = QtWidgets.QSlider(orientation=QtCore.Qt.Horizontal)
        self.dilate_spinbox = QtWidgets.QSpinBox()
        self.dilate_spinbox.setToolTip('The number of iterations to apply dilation at the specified radius')
        self.dilate_spinbox.setMinimum(1)
        self.dilate_spinbox.setMaximum(99)
        self.dilate_spinbox.setSingleStep(1)
        self.dilate_spinbox.valueChanged.connect(self.update_dilate_iter)
        self.dilate_slider.setToolTip('The pixel radius to use for dilation')
        self.dilate_slider.setMinimum(0)
        self.dilate_slider.setMaximum(kwargs.pop('max_dilate', 9))
        self.dilate_slider.setSingleStep(1)
        self.dilate_slider.valueChanged.connect(self.update_dilate)
        if self.ocr_params['dilate']:
            self.dilate_slider.setValue(self.ocr_params['dilate'])

        # erode
        self.erode_label = QtWidgets.QLabel('Erode [0]')
        self.erode_slider = QtWidgets.QSlider(orientation=QtCore.Qt.Horizontal)
        self.erode_spinbox = QtWidgets.QSpinBox()
        self.erode_spinbox.setToolTip('The number of iterations to apply erosion at the specified radius')
        self.erode_spinbox.setMinimum(1)
        self.erode_spinbox.setMaximum(99)
        self.erode_spinbox.setSingleStep(1)
        self.erode_spinbox.valueChanged.connect(self.update_erode_iter)
        self.erode_slider.setToolTip('The pixel radius to use for erosion')
        self.erode_slider.setMinimum(0)
        self.erode_slider.setMaximum(kwargs.pop('max_erode', 9))
        self.erode_slider.setSingleStep(1)
        self.erode_slider.valueChanged.connect(self.update_erode)
        if self.ocr_params['erode']:
            self.erode_slider.setValue(self.ocr_params['erode'])

        # image-processing layout
        ip_layout = QtWidgets.QGridLayout()
        ip_layout.addWidget(self.rotate_label, 0, 0)
        ip_layout.addWidget(self.rotate_slider, 0, 1)
        ip_layout.addWidget(self.blur_label, 1, 0)
        ip_layout.addWidget(self.blur_slider, 1, 1)
        ip_layout.addWidget(self.threshold_label, 2, 0)
        ip_layout.addWidget(self.threshold_slider, 2, 1)
        ip_layout.addWidget(self.threshold_checkbox, 2, 2)
        ip_layout.addWidget(self.dilate_label, 3, 0)
        ip_layout.addWidget(self.dilate_slider, 3, 1)
        ip_layout.addWidget(self.dilate_spinbox, 3, 2)
        ip_layout.addWidget(self.erode_label, 4, 0)
        ip_layout.addWidget(self.erode_slider, 4, 1)
        ip_layout.addWidget(self.erode_spinbox, 4, 2)
        self.image_processing_group.setLayout(ip_layout)

        # the container for all the camera widgets
        self.camera_config_group = QtWidgets.QGroupBox('Camera Settings')

        # ISO
        self.iso_combobox = QtWidgets.QComboBox()
        self.iso_combobox.setToolTip('The ISO setting of the camera')
        self.iso_combobox.addItems(['auto', '100', '200', '320', '400', '500', '640', '800'])
        iso = str(kwargs.pop('iso', 'auto'))
        if iso == '0':
            iso = 'auto'
        self.iso_combobox.setCurrentText(iso)
        self.update_iso(self.iso_combobox.currentText())
        self.iso_combobox.currentTextChanged.connect(self.update_iso)
        self.iso_combobox.setEnabled(not self.path)

        # resolution
        self.resolution_combobox = QtWidgets.QComboBox()
        self.resolution_combobox.setToolTip('The resolution of the camera')
        self.resolution_combobox.addItems(['VGA', 'SVGA', 'XGA', '720p', 'SXGA', 'UXGA', '1080p', 'MAX'])
        self.resolution_combobox.setCurrentText(str(kwargs.pop('resolution', 'VGA')))
        self.update_resolution(self.resolution_combobox.currentText())
        self.resolution_combobox.currentTextChanged.connect(self.update_resolution)
        self.resolution_combobox.setEnabled(not self.path)

        # exposure mode
        self.exposure_mode_combobox = QtWidgets.QComboBox()
        self.exposure_mode_combobox.setToolTip('The exposure mode of the camera')
        self.exposure_mode_combobox.addItems(['off', 'auto', 'night', 'nightpreview',
                                              'backlight', 'spotlight', 'sports', 'snow',
                                              'beach', 'verylong', 'fixedfps', 'antishake', 'fireworks'])
        self.exposure_mode_combobox.setCurrentText(str(kwargs.pop('exposure_mode', 'auto')))
        self.update_exposure_mode(self.exposure_mode_combobox.currentText())
        self.exposure_mode_combobox.currentTextChanged.connect(self.update_exposure_mode)
        self.exposure_mode_combobox.setEnabled(not self.path)

        camera_layout = QtWidgets.QGridLayout()
        camera_layout.addWidget(QtWidgets.QLabel('ISO'), 0, 0)
        camera_layout.addWidget(self.iso_combobox, 0, 1)
        camera_layout.addItem(QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.MinimumExpanding), 0, 2)
        camera_layout.addWidget(QtWidgets.QLabel('Resolution'), 1, 0)
        camera_layout.addWidget(self.resolution_combobox, 1, 1)
        camera_layout.addWidget(QtWidgets.QLabel('Exposure Mode'), 2, 0)
        camera_layout.addWidget(self.exposure_mode_combobox, 2, 1)
        self.camera_config_group.setLayout(camera_layout)

        if self.client is None:
            self.iso_combobox.setEnabled(False)
            self.resolution_combobox.setEnabled(False)
            self.exposure_mode_combobox.setEnabled(False)

        # the container for all the OCR algorithm widgets
        self.ocr_config_group = QtWidgets.QGroupBox('OCR Algorithm Settings')

        # tesseract languages
        self.tess_lang_combobox = QtWidgets.QComboBox()
        self.tess_lang_combobox.addItems(['eng', 'letsgodigital'])
        self.tess_lang_combobox.currentTextChanged.connect(self.update_tess_lang)
        self.tess_lang_combobox.setToolTip('The language to use for Tesseract')

        # tesseract or ssocr
        self.tess_radio = QtWidgets.QRadioButton('Tesseract')
        self.tess_radio.setToolTip('Use Tesseract')
        self.tess_radio.toggled.connect(self.update_algorithm)
        self.ssocr_radio = QtWidgets.QRadioButton('SSOCR')
        self.ssocr_radio.setToolTip('Use SSOCR')
        self.ssocr_radio.toggled.connect(self.update_algorithm)
        if self.ocr_params['algorithm'] == 'ssocr':
            self.ssocr_radio.setChecked(True)
        else:
            self.tess_radio.setChecked(True)

        algo_layout = QtWidgets.QGridLayout()
        algo_layout.addWidget(self.tess_radio, 0, 0)
        algo_layout.addWidget(self.tess_lang_combobox, 0, 1)
        algo_layout.addItem(QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.MinimumExpanding), 0, 2)
        algo_layout.addWidget(self.ssocr_radio, 1, 0)
        self.ocr_config_group.setLayout(algo_layout)

        options_layout = QtWidgets.QVBoxLayout()
        options_layout.addWidget(self.image_processing_group)
        options_layout.addWidget(self.camera_config_group)
        options_layout.addWidget(self.ocr_config_group)
        options_layout.addStretch(1)

        layout = QtWidgets.QHBoxLayout()
        layout.addLayout(graphing_layout)
        layout.addLayout(options_layout)
        self.setLayout(layout)

        if self.path:
            self.setAcceptDrops(True)
            self.capture_thread = None
            self.original_image = utils.to_cv2(self.path)
            height, width = self.original_image.shape[:2]
            try:  # could pass in an already-opened image object (which isn't a path)
                basename = os.path.basename(self.path)
            except OSError:
                basename = 'UNKNOWN'
            self.setWindowTitle('OCR || {} [{} x {}]'.format(basename, width, height))
        else:
            self.setAcceptDrops(False)
            self.original_image = None
            self.capture_index = 0
            self.setWindowTitle('OCR || Capture 0')
            self.capture_thread = Capture()
            self.capture_thread.start(self.client)
            self.capture_thread.finished.connect(self.capture)

        self.apply_ocr()

    def closeEvent(self, event):
        """Override the QWidget.closeEvent method."""
        self.close_event_occurred = True
        if self.capture_thread is not None:
            self.capture_thread.stop()
            while self.capture_thread.is_running():
                time.sleep(0.01)
        super(Gui, self).closeEvent(event)

    def dragEnterEvent(self, event):
        """Override the QWidget.dragEnterEvent method."""
        path = io.get_drag_enter_paths(event)[0]
        ext = os.path.splitext(path)[1].lower()
        if ext in ('.jpeg', '.jpg', '.bmp', '.png'):
            self.path = path
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event=None):
        """Override the QWidget.dropEvent method."""
        try:
            self.original_image = utils.to_cv2(self.path)
        except Exception as e:
            prompt.critical(e)
        else:
            self.setWindowTitle('OCR || ' + os.path.basename(self.path))
            self.append_zoom(None, None, None, None)

    def keyPressEvent(self, event):
        """Override the QWidget.keyPressEvent method."""
        if event.key() == (QtCore.Qt.Key_Control and QtCore.Qt.Key_Z):
            try:
                self.zoom_history.pop()
            except IndexError:
                pass  # tried to pop from an empty list
            else:
                if self.zoom_history:
                    self.append_zoom(*self.zoom_history[-1])
                else:
                    self.append_zoom(None, None, None, None)

        elif event.key() == QtCore.Qt.Key_Escape:
            self.append_zoom(None, None, None, None)

        elif self.zoom_history and event.key() in (QtCore.Qt.Key_Up, QtCore.Qt.Key_Down,
                                                   QtCore.Qt.Key_Left, QtCore.Qt.Key_Right):
            dx, dy = 0, 0
            x, y, w, h = self.zoom_history[-1]
            if event.key() == QtCore.Qt.Key_Up:
                dy = min(self.delta, 1.0 - h - y)
            elif event.key() == QtCore.Qt.Key_Down:
                dy = -min(self.delta, y)
            elif event.key() == QtCore.Qt.Key_Left:
                dx = min(self.delta, 1.0 - w - x)
            else:
                dx = -min(self.delta, x)

            if dx != 0 or dy != 0:
                self.append_zoom(x + dx, y + dy, w, h)

    def select_zoom(self, event):
        """Called when the user wants to zoom in."""
        event.accept()
        if self.canvas.image is None:
            return

        if event.button() & (QtCore.Qt.LeftButton | QtCore.Qt.MidButton):
            if event.isFinish():
                self.view_box.rbScaleBox.hide()

                # get the coordinates of the highlighted region
                rect = QtCore.QRectF(pg.Point(event.buttonDownPos(event.button())), pg.Point(event.pos()))
                rect = self.view_box.childGroup.mapRectFromParent(rect).normalized()

                # get the size of the image on the canvas
                # DO NOT use self.canvas.width(), self.canvas.height()
                height, width = self.original_image.shape[:2]
                if self.zoom_history:
                    width = int(self.zoom_history[-1][2] * width)
                    height = int(self.zoom_history[-1][3] * height)

                angle = self.rotate_slider.value()
                values = rotate_zoom(angle, rect, width, height)
                if values is None:
                    return  # zoom outside of the image

                x, y, w, h, width, height = values

                # convert to the coordinates of the original (un-zoomed) image
                if self.zoom_history:
                    orig_height, orig_width = self.original_image.shape[:2]
                    x2, y2, w2, h2 = self.zoom_history[-1]
                    x = x * width / orig_width + x2
                    y = y * height / orig_height + y2
                    w *= w2
                    h *= h2

                self.append_zoom(x, y, w, h)

            else:
                self.view_box.updateScaleBox(event.buttonDownPos(), event.pos())

    def append_zoom(self, x, y, w, h):
        """Update the region of interest."""
        if x is None:
            self.zoom_history.clear()
            self.ocr_params['zoom'] = None
            self.client_queue['set_zoom'] = [0, 0, 1, 1]
        else:
            self.zoom_history.append((x, y, w, h))
            self.ocr_params['zoom'] = (x, y, w, h)
            self.client_queue['set_zoom'] = [x, y, w, h]
        self.apply_ocr()

    def apply_ocr(self):
        if self.original_image is None:
            return
        # try:
        #     text, img = ocr(self.original_image, **self.ocr_params)
        # except Exception as e:
        #     msg = str(e)
        #     if msg.startswith('tesseract is not installed') or msg.endswith('Call ocr.set_ssocr_path(...)'):
        #         raise
        #     text, img = '', process(self.original_image, **self.ocr_params)
        if self.client is not None:
            zoom = self.ocr_params.pop('zoom')
        text, img = 'Not calling OCR', process(self.original_image, **self.ocr_params)
        if self.client is not None:
            self.ocr_params['zoom'] = zoom
        self.ocr_label.setText(text)
        self.canvas.setImage(img)

    def update_rotate(self, value):
        self.ocr_params['rotate'] = value if value != 0 else None
        self.rotate_label.setText('<html>Rotate [{}&deg;]</html>'.format(value))
        self.apply_ocr()

    def update_blur(self, value):
        self.ocr_params['blur'] = value if value > 0 else None
        self.blur_label.setText('Gaussian blur [{}]'.format(value))
        self.apply_ocr()

    def update_threshold(self, value):
        if self.threshold_checkbox.isChecked():
            self.ocr_params['threshold'] = value
        else:
            self.ocr_params['threshold'] = None
        self.threshold_label.setText('Threshold [{}]'.format(value))
        self.apply_ocr()

    def update_threshold_checkbox(self, value):
        self.threshold_slider.setEnabled(value)
        self.update_threshold(self.threshold_slider.value())

    def update_dilate(self, value):
        if value == 0:
            self.ocr_params['dilate'] = None
        else:
            self.ocr_params['dilate'] = {'radius': value, 'iterations': self.dilate_spinbox.value()}
        self.dilate_label.setText('Dilate [{}]'.format(value))
        self.apply_ocr()

    def update_dilate_iter(self, *ignore):
        self.update_dilate(self.dilate_slider.value())

    def update_erode(self, value):
        if value == 0:
            self.ocr_params['erode'] = None
        else:
            self.ocr_params['erode'] = {'radius': value, 'iterations': self.erode_spinbox.value()}
        self.erode_label.setText('Erode [{}]'.format(value))
        self.apply_ocr()

    def update_erode_iter(self, *ignore):
        self.update_erode(self.erode_slider.value())

    def update_algorithm(self, value):
        if not value:
            return

        text = self.sender().text().lower()
        if text == 'ssocr':
            self.tess_lang_combobox.setEnabled(False)
            self.ocr_params['lang'] = None
        else:
            self.tess_lang_combobox.setEnabled(True)
            self.ocr_params['lang'] = self.tess_lang_combobox.currentText()

        self.ocr_params['algorithm'] = text
        self.apply_ocr()

    def update_tess_lang(self, value):
        self.ocr_params['lang'] = value
        self.apply_ocr()

    def update_iso(self, value):
        self.client_queue['set_iso'] = value

    def update_resolution(self, value):
        self.client_queue['set_resolution'] = value

    def update_exposure_mode(self, value):
        self.client_queue['set_exposure_mode'] = value

    def capture(self):
        self.capture_index += 1
        self.original_image = self.capture_thread.original_image
        height, width = self.original_image.shape[:2]
        self.setWindowTitle('OCR || Capture {} [{} x {}]'.format(self.capture_index, width, height))
        self.apply_ocr()
        for k, v in self.client_queue.items():
            getattr(self.client, k)(v)
        self.client_queue.clear()
        if not self.close_event_occurred:
            self.capture_thread.start(self.client)


def rotate_zoom(angle, rect, width, height):
    x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()

    rect = rotate_highlighted(x, y, w, h, angle)
    corners = rotate_image_corners(0, 0, width, height, angle)
    inter_top = get_intersection(corners[0], corners[1], rect[0], rect[3])
    inter_bottom = get_intersection(corners[2], corners[3], rect[0], rect[3])

    if -45 <= angle <= 45:
        x = inter_top[0] - corners[0][0]
        y = rect[0][1] - inter_top[1]
        w = min(rect[1][0], corners[1][0]) - rect[0][0]
        h = min(rect[3][1], inter_bottom[1]) - rect[0][1]
    elif 45 < angle < 135:
        x = corners[0][1] - inter_top[1]
        y = rect[0][0] - inter_top[0]
        w = min(rect[0][1], corners[0][1]) - rect[1][1]
        h = min(rect[3][0], inter_bottom[0]) - rect[0][0]
    elif -45 > angle > -135:
        x = inter_top[1] - corners[0][1]
        y = inter_top[0] - rect[0][0]
        w = min(rect[1][1], corners[1][1]) - rect[0][1]
        h = rect[0][0] - max(rect[3][0], inter_bottom[0])
    else:
        x = corners[0][0] - inter_top[0]
        y = inter_top[1] - rect[0][1]
        w = rect[0][0] - max(rect[1][0], corners[1][0])
        h = rect[0][1] - max(rect[3][1], corners[3][1])

    width = math.sqrt((corners[1][0] - corners[0][0]) ** 2 + (corners[1][1] - corners[0][1]) ** 2)
    height = math.sqrt((corners[3][0] - corners[0][0]) ** 2 + (corners[3][1] - corners[0][1]) ** 2)

    # make sure that some region of the image is highlighted
    if x < 0:
        x, w = 0., x + w
    if y < 0:
        y, h = 0., y + h
    if w < 0 or h < 0 or y > height or x > width:
        return

    # normalize
    x /= width
    y /= height
    w /= width
    h /= height

    return x, y, w, h, width, height


def rotate_highlighted(x, y, w, h, angle):
    """Only to be used by rotate_zoom."""

    theta = angle
    if 45 < abs(angle) < 135:
        theta -= 90

    corners = ((x, y), (x + w, y), (x + w, y + h), (x, y + h))

    def rotate_point(x_val, y_val):
        xr = (x_val - cx) * cos - (y_val - cy) * sin + cx
        yr = (x_val - cx) * sin + (y_val - cy) * cos + cy
        return xr, yr

    # take negative of angle since we want clockwise rotation to be a positive angle
    a = math.radians(-theta)
    cos = math.cos(a)
    sin = math.sin(a)
    cx = x + (w * 0.5)
    cy = y + (h * 0.5)

    corners = tuple(rotate_point(*corner) for corner in corners)

    if 45 < abs(angle) < 135:
        return corners[3], corners[0], corners[1], corners[2]
    return corners


def rotate_image_corners(x, y, w, h, angle):
    """Only to be used by rotate_zoom."""
    corners = ((x, y), (x + w, y), (x + w, y + h), (x, y + h))
    if angle == 0:
        return corners
    return tuple(utils.rotate(np.asarray([a, b, w, h]), angle) for a, b in corners)


def get_intersection(a1, a2, b1, b2):
    """Only to be used by rotate_zoom.

    Returns the point of intersection of two lines.

    a1: [x, y] a point on the first line
    a2: [x, y] another point on the first line
    b1: [x, y] a point on the second line
    b2: [x, y] another point on the second line
    """
    v = np.vstack([a1, a2, b1, b2])
    h = np.hstack((v, np.ones((4, 1))))
    line1 = np.cross(h[0], h[1])
    line2 = np.cross(h[2], h[3])
    x, y, z = np.cross(line1, line2)
    return x/z, y/z


class CaptureWorker(Worker):

    def __init__(self, client):
        super(CaptureWorker, self).__init__()
        self.client = client
        self.original_image = None

    def process(self):
        self.original_image = utils.to_cv2(self.client.capture())


class Capture(Thread):

    def __init__(self):
        super(Capture, self).__init__(CaptureWorker)
