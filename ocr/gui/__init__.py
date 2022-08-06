"""
The main GUI for configuring the OCR parameters.
"""
import os
import json

from msl.qt import (
    Qt,
    QtGui,
    QtCore,
    QtWidgets,
    Signal,
    Thread,
    Worker,
    Button,
    convert,
    utils,
    prompt,
)
import pyqtgraph as pg

from .. import to_cv2
from . import icons
from .camera_settings import CameraSettings
from .roi_preview import ROIPreview
from .connection import prompt_for_camera_kwargs


class CaptureWorker(Worker):

    def __init__(self, camera):
        """Capture an image without freezing the GUI."""
        super(CaptureWorker, self).__init__()
        self.camera = camera
        self.image = None
        self.settings = None

    def process(self):
        try:
            self.image, self.settings = self.camera.capture_with_settings()
        except:
            self.image, self.settings = None, None


class CaptureThread(Thread):

    def __init__(self):
        """Capture an image without freezing the GUI."""
        super(CaptureThread, self).__init__(CaptureWorker)


class Configure(QtWidgets.QWidget):

    sig_new_camera = Signal(object)  # Camera or RemoteCamera object
    sig_closing = Signal()

    def __init__(self, config=None):
        """The main GUI for configuring the OCR parameters.

        Parameters
        ----------
        config : :class:`str` or :class:`dict`, optional
            The path to a JSON configuration file to load
            or an already-loaded configuration file.
        """
        super(Configure, self).__init__()

        self.setAcceptDrops(True)
        self.setWindowTitle('Drag and drop an image file')

        self.camera = None
        self.camera_settings = None  # reserved for CameraSettings
        self.ocr_service = None  # reserved for ocr.service.RemoteOCR
        self.capture_index = 0
        self.is_capture_paused = False
        self.capture_thread = CaptureThread()
        self.capture_thread.finished.connect(self.captured)
        self.rois = {}  # key: pg.RectROI, value: ROIPreview widget
        self.ocr_params = {'rois': {}, 'camera': {}}
        self.dragged_image, self.dragged_path = [], ''
        self.zoom_history = []

        if isinstance(config, dict):
            self.config = config
        elif isinstance(config, str):
            with open(config, mode='rt') as fp:
                self.config = json.load(fp)
        else:
            self.config = {}

        self.graphics_view = pg.GraphicsView(background=None)
        self.image_item = pg.ImageItem(axisOrder='row-major')
        self.view_box = pg.ViewBox(invertY=True, lockAspect=True, enableMenu=False)
        self.view_box.addItem(self.image_item)
        self.graphics_view.setCentralItem(self.view_box)
        self.graphics_view.sceneObj.contextMenu = []  # remove "Export ..." option

        pen = self.config.get('roi', {})
        width = pen.get('line_width', pen.get('width', 4))
        color = convert.to_qcolor(pen.get('colour', pen.get('color', '#00ff00')))
        self.roi_pen = QtGui.QPen(QtGui.QBrush(color), width)
        self.roi_pen.setCosmetic(True)

        self.zoom_roi = None
        pen = self.config.get('zoom', {})
        width = pen.get('line_width', pen.get('width', 4))
        color = convert.to_qcolor(pen.get('colour', pen.get('color', '#0000ff')))
        self.zoom_pen = QtGui.QPen(QtGui.QBrush(color), width)
        self.zoom_pen.setCosmetic(True)

        icon_size = max(32, int(utils.screen_geometry(self).height() * 0.04))
        self.camera_button = Button(
            icon=convert.to_qicon(icons.camera, size=icon_size),
            tooltip='Connect to a camera',
            left_click=self.camera_button_clicked,
        )

        self.roi_button = Button(
            icon=convert.to_qicon(icons.roi, size=icon_size),
            tooltip='Add a new region of interest to apply OCR to',
            left_click=self.add_roi,
        )
        self.roi_button.add_menu_item(
            text='Line width',
            triggered=self.change_roi_width,
            tooltip='Edit the line width to draw the ROI'
        )
        self.roi_button.add_menu_item(
            text='Colour',
            triggered=self.change_roi_colour,
            tooltip='Edit the colour of the ROI'
        )

        self.auto_range_button = Button(
            icon=convert.to_qicon(icons.reset, size=icon_size),
            left_click=self.view_box.autoRange,
            tooltip='Reset view'
        )

        self.zoom_button = Button(
            icon=convert.to_qicon(icons.zoom, size=icon_size),
            left_click=self.create_zoom,
            tooltip='Camera zoom (pressing the Escape key will abort)'
        )
        self.zoom_button.add_menu_item(text='Clear', icon=icons.clear, triggered=self.clear_zoom)
        self.zoom_button.add_menu_item(text='Undo', icon=icons.undo, triggered=self.undo_zoom, shortcut='CTRL+Z')
        self.zoom_button.setEnabled(False)

        spacer = QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        icon_layout = QtWidgets.QHBoxLayout()
        icon_layout.addWidget(self.camera_button)
        icon_layout.addWidget(self.zoom_button)
        icon_layout.addWidget(self.auto_range_button)
        icon_layout.addWidget(self.roi_button)
        icon_layout.addSpacerItem(spacer)

        camera_layout = QtWidgets.QVBoxLayout()
        camera_layout.addLayout(icon_layout)
        camera_layout.addWidget(self.graphics_view)

        layout = QtWidgets.QHBoxLayout()
        layout.addLayout(camera_layout, stretch=100)
        self.setLayout(layout)

        if self.config.get('image'):
            path = self.config['image']
            self.set_image(path, os.path.basename(path))

    def dragEnterEvent(self, event):
        """Override the :meth:`QWidget.dragEnterEvent` method."""
        try:
            self.dragged_path = utils.drag_drop_paths(event)[0]
            self.dragged_image = to_cv2(self.dragged_path)
            event.accept()
        except:
            self.dragged_image, self.dragged_path = [], ''
            event.ignore()

    def dropEvent(self, event):
        """Override the :meth:`QWidget.dropEvent` method."""
        event.accept()
        self.pause_capture()
        if self.camera_settings is not None:
            self.camera_settings.hide()
            self.zoom_button.setEnabled(False)
        self.set_image(self.dragged_image, os.path.basename(self.dragged_path))

    def closeEvent(self, event):
        """Override the :meth:`QWidget.closeEvent` method."""
        self.sig_closing.emit()
        self.pause_capture()
        if self.camera:
            self.camera.disconnect()
        if self.ocr_service:
            self.ocr_service.disconnect()
        if self.ocr_params['rois']:
            if self.camera_settings is not None:
                self.ocr_params['camera'] = self.camera_settings.settings
            path = prompt.save(title='Save the OCR parameters', filters='OCR (*.json)')
            if path:
                with open(path, mode='wt') as fp:
                    json.dump(self.ocr_params, fp, indent=2)
        super(Configure, self).closeEvent(event)

    def keyPressEvent(self, event):
        """Override the :meth:`QWidget.closeEvent` method."""
        key = event.key()
        if key == Qt.Key_Space:
            self.camera_button.click()
        elif self.zoom_roi is not None:
            if key == Qt.Key_Return or key == Qt.Key_Enter:
                self.pause_capture()
                rz = self.zoom_roi.parentBounds()
                ri = self.image_item.boundingRect()
                if self.zoom_history:
                    x2, y2, w2, h2 = self.zoom_history[-1]
                    x = x2 + rz.x() * w2 / ri.width()
                    y = y2 + rz.y() * h2 / ri.height()
                    w = w2 * rz.width() / ri.width()
                    h = h2 * rz.height() / ri.height()
                else:
                    x = rz.x() / ri.width()
                    y = rz.y() / ri.height()
                    w = rz.width() / ri.width()
                    h = rz.height() / ri.height()
                self.zoom_history.append([x, y, w, h])
                self.camera.update_settings({'zoom': self.zoom_history[-1]})
                self.view_box.removeItem(self.zoom_roi)
                self.zoom_roi = None
                self.start_capture()
            elif key == Qt.Key_Escape:
                self.view_box.removeItem(self.zoom_roi)
                self.zoom_roi = None
        super(Configure, self).keyPressEvent(event)

    def create_zoom(self):
        """Slot for the Zoom button click."""
        if self.zoom_roi is not None:
            return

        if self.rois:
            if not prompt.yes_no('Zooming will remove all ROIs. Do you want to continue?'):
                return

        for preview in list(self.rois.values()):
            preview.close()

        height, width = self.image_item.image.shape[:2]
        size = min(width//2, height//2)  # want w=h and the aspect ratio locked
        pos, size = (width//2 - size//2, height//2 - size//2), (size, size)
        self.zoom_roi = pg.RectROI(pos, size, pen=self.zoom_pen, invertible=True,
                                   rotatable=False, maxBounds=self.image_item.boundingRect())
        self.zoom_roi.aspectLocked = True
        self.view_box.addItem(self.zoom_roi)

    def clear_zoom(self):
        """Slot for the Zoom button menu action."""
        if not self.zoom_history:
            return
        self.pause_capture()
        self.zoom_history.clear()
        self.camera.update_settings({'zoom': [0.0, 0.0, 1.0, 1.0]})
        self.auto_range_button.click()
        self.start_capture()

    def undo_zoom(self):
        """Slot for the Zoom button menu action."""
        try:
            self.zoom_history.pop()
            zoom = self.zoom_history[-1]
        except IndexError:
            zoom = [0.0, 0.0, 1.0, 1.0]
            if self.camera_settings.settings['zoom'] == zoom:
                return
        self.pause_capture()
        self.camera.update_settings({'zoom': zoom})
        self.start_capture()

    def on_new_service(self, service):
        """Slot for a new ocr.service.OCR object."""
        self.ocr_service = service
        for preview in self.rois.values():  # notify all ROIPreview's
            for index in range(preview.tab.count()):
                algorithm_widget = preview.tab.widget(index)
                algorithm_widget.refresh_layout(service)
            preview.apply_ocr()

    def set_image(self, image, prefix):
        """Set the image and the title of the Window."""
        img = to_cv2(image)
        self.image_item.setImage(img, autoLevels=False)
        self.setWindowTitle(f'{prefix} [{img.width}x{img.height}]')
        for roi, preview in self.rois.items():
            roi.maxBounds = self.image_item.boundingRect()
            preview.update_image(roi)

    def add_roi(self):
        """Slot for the region-of-interest button."""
        if self.image_item.image is None:
            return

        height, width = self.image_item.image.shape[:2]
        pos, size = (width//4, height//4), (width//2, height//2)
        roi = pg.RectROI(pos, size, invertible=True, rotatable=False, maxBounds=self.image_item.boundingRect())
        self.view_box.addItem(roi)
        roi.sigRemoveRequested.connect(self.remove_roi)

        preview = ROIPreview(self, roi)
        preview.sig_closing.connect(self.remove_roi)
        preview.show()
        # didn't like either size hint -> so take the average
        a = preview.minimumSizeHint()
        b = preview.sizeHint()
        preview.resize((a.width()+b.width())//2, (a.height()+b.height())//2)

        self.rois[roi] = preview
        self.update_roi_pen()

    def remove_roi(self, roi):
        """Slot for the RoiPreview.sig_closing signal."""
        self.view_box.removeItem(roi)
        self.rois.pop(roi)

    def change_roi_width(self):
        """Change the line width of each ROI."""
        width = prompt.integer('Enter the line width to draw the ROI', minimum=1, value=self.roi_pen.width())
        if not width:
            return
        self.roi_pen.setWidth(width)
        self.update_roi_pen()

    def change_roi_colour(self):
        """Change the colour of each ROI."""
        dialog = QtWidgets.QColorDialog()
        dialog.setCurrentColor(self.roi_pen.color())
        if not dialog.exec_():
            return
        self.roi_pen.setColor(dialog.currentColor())
        self.update_roi_pen()

    def update_roi_pen(self):
        """Update the colour and line width of each ROI and its handles."""
        for roi in self.rois:
            roi.setPen(self.roi_pen)
            for handle in roi.getHandles():
                handle.pen.setWidth(self.roi_pen.width())
                handle.pen.setColor(self.roi_pen.color())

    def camera_button_clicked(self):
        """Slot for the camera button clicked signal."""
        if self.camera_button.toolTip() == 'Pause':
            self.pause_capture()
        else:
            if not self.camera:
                try:
                    settings = self.config.get('camera')
                    self.camera = prompt_for_camera_kwargs(settings)
                    if not self.camera:
                        return
                    self.camera_settings = CameraSettings(self)
                    self.sig_closing.connect(self.camera_settings.main_closing)
                    self.layout().addWidget(self.camera_settings)
                except Exception as e:
                    prompt.critical(e)
                    return
            if self.camera_settings is not None:
                self.camera_settings.show()
                self.zoom_button.setEnabled(True)
            self.start_capture()

    def start_capture(self):
        """Start capturing images."""
        self.is_capture_paused = False
        self.single_capture()

    def single_capture(self):
        """Start one capture."""
        if self.is_capture_paused:
            return
        self.camera_button.setIcon(icons.pause)
        self.camera_button.setToolTip('Pause')
        self.capture_thread.start(self.camera)

    def pause_capture(self):
        """Wait for the current capture to finish before pausing."""
        if self.is_capture_paused:
            return
        self.is_capture_paused = True
        self.capture_thread.stop(10000)
        if self.camera:
            self.camera_button.setIcon(icons.play)
            self.camera_button.setToolTip('Resume')

    def captured(self):
        """Slot for when the capture thread finishes."""
        image = self.capture_thread.image
        if image is None or self.is_capture_paused:
            return
        self.capture_index += 1
        self.set_image(image, f'Capture {self.capture_index}')
        self.camera_settings.update_displayed_values(self.capture_thread.settings)
        self.single_capture()
