from queue import Queue
from time import perf_counter

import pyqtgraph as pg
from msl.qt import (
    Qt,
    QtWidgets,
    Signal,
    Button,
    Thread,
    LED,
    Worker,
    prompt,
    convert,
)

from . import icons
from .tesseract_widget import Tesseract
from .ssocr_widget import SSOCR
from .task_widgets import TaskList
from .. import (
    apply,
    to_base64,
    process,
)
from ..utils import (
    OpenCVImage,
    logger,
)


class OCRThread(Thread):

    def __init__(self):
        """Perform OCR without freezing the GUI."""
        super(OCRThread, self).__init__(OCRWorker)


class OCRWorker(Worker):

    sig_ocr_text = Signal(str)  # the OCR text

    def __init__(self, parent):
        """Apply the OCR algorithm without freezing the GUI."""
        super(OCRWorker, self).__init__()
        self.queue = parent.queue
        self.sig_ocr_text.connect(parent.on_update_text)

    def process(self):
        while True:
            function, image, algorithm, parameters = self.queue.get()
            if not function:
                break
            try:
                t0 = perf_counter()
                text, _ = function(image, algorithm=algorithm, **parameters)
                dt = perf_counter() - t0
                logger.info('applying OCR with {!r} took {:.3f} seconds'.format(algorithm, dt))
            except BaseException as e:
                message = e.message if hasattr(e, 'message') else str(e)
                logger.error(message)
                text = ''
            self.sig_ocr_text.emit(text)


class ROIPreview(QtWidgets.QWidget):

    sig_closing = Signal(object)  # pg.RectROI

    def __init__(self, parent, roi):
        super(ROIPreview, self).__init__()
        self.setObjectName('ROIPreview')

        self.main_image_item = parent.image_item
        self.roi = roi
        self.setWindowTitle('ROI-{}'.format(1+len(parent.rois)))
        self.ocr_params = parent.ocr_params
        self.image_processed = OpenCVImage([])
        self.image_unprocessed = OpenCVImage([])
        self.cropped = (-1, -1, -1, -1)  # x, y, w, h

        roi.sigRegionChanged.connect(self.update_image)

        self.ocr_text = QtWidgets.QLabel()
        self.ocr_text.setFont(convert.to_qfont(parent.config.get('ocr_font', ('Ariel', 16))))

        self.queue = Queue()
        self.ocr_thread = OCRThread()  # apply OCR in a separate thread
        self.ocr_thread.start(self)

        self.graphics_view = pg.GraphicsView(background=None)
        self.image_item = pg.ImageItem(axisOrder='row-major')
        self.view_box = pg.ViewBox(invertY=True, enableMouse=False, lockAspect=True, enableMenu=False)
        self.view_box.addItem(self.image_item)
        self.graphics_view.setCentralItem(self.view_box)
        self.graphics_view.sceneObj.contextMenu = []  # remove "Export ..." option

        self.task_list = TaskList(self)
        self.task_list.setToolTip('Image-processing tasks.\n'
                                  'Click a button on the right to add a task.\n'
                                  'Drag and drop tasks to rearrange order.\n'
                                  'Delete key removes the selected task.')

        self.led = LED(on_color='#00ff00', tooltip='Executing OCR algorithm')
        self.led.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.update_name_button = Button(
            icon=icons.update_roi_name,
            left_click=self.update_name,
            tooltip='<html>Change the name of this ROI. <i>The name is shown in the titlebar</i></html>'
        )

        self.cache_button = Button(icon=icons.cache, left_click=self.cache, tooltip='Cache settings')

        self.tab = QtWidgets.QTabWidget()
        self.tab.addTab(Tesseract(self, parent), 'tesseract')
        self.tab.addTab(SSOCR(self, parent), 'ssocr')
        self.tab.currentChanged.connect(self.apply_ocr)

        button_layout = QtWidgets.QVBoxLayout()
        button_layout.addWidget(self.cache_button)
        button_layout.addWidget(self.update_name_button)
        for n in sorted(self.task_list.widget_map):
            b = Button(text=n, left_click=self.task_list.on_add_item, tooltip='Add a {} task'.format(n))
            b.setObjectName(n)
            button_layout.addWidget(b)
        button_layout.addStretch()

        task_layout = QtWidgets.QHBoxLayout()
        task_layout.addWidget(self.task_list)
        task_layout.addLayout(button_layout)
        task_layout.setMargin(0)

        image_layout = QtWidgets.QVBoxLayout()
        image_layout.addWidget(self.ocr_text, alignment=Qt.AlignHCenter)
        image_layout.addWidget(self.graphics_view)
        image_layout.addWidget(self.led, alignment=Qt.AlignRight)
        image_layout.addWidget(self.tab)
        image_layout.setMargin(0)
        image_layout.setContentsMargins(0, 0, 0, 0)

        left_widget = QtWidgets.QWidget()
        left_widget.setLayout(image_layout)
        right_widget = QtWidgets.QWidget()
        right_widget.setLayout(task_layout)

        splitter = QtWidgets.QSplitter()
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)

        # set the initial image
        self.update_image(roi)
        self.ask_cache = False

    @property
    def name(self):
        """The name of the ROI."""
        return self.windowTitle()

    def update_name(self):
        """Slot for the update-name button."""
        text = prompt.text('Enter a new name, currently {!r}'.format(self.name))
        if text:
            if self.name in self.ocr_params['rois']:
                self.ocr_params['rois'][text] = self.ocr_params['rois'].pop(self.name)
            self.setWindowTitle(text)

    def cache(self):
        """Slot for the cache button."""
        self.ocr_params['rois'][self.name] = self.parameters(include_crop=True)
        self.ask_cache = False

    def closeEvent(self, event):
        """Override :meth:`QWidget.closeEvent`."""
        if self.ask_cache:
            if prompt.yes_no('The OCR parameters have been modified. '
                             'Do you want to use the current settings?'):
                self.cache()

        self.sig_closing.emit(self.roi)

        # abort the thread
        self.queue.put((None, None, None, None))
        self.ocr_thread.stop(10000)

        # possibly disconnect from the spawned camera
        for index in range(self.tab.count()):
            self.tab.widget(index).close()

        super(ROIPreview, self).closeEvent(event)

    def update_image(self, roi):
        """Slot for sigRegionChanged signal and called after a new capture."""
        data = self.main_image_item.image
        s, _ = roi.getArraySlice(data, self.main_image_item)
        x, y = s[1].start, s[0].start
        xywh = (x, y, s[1].stop - x, s[0].stop - y)
        self.image_unprocessed = OpenCVImage(data[s])
        self.process_image()
        self.ask_cache = self.cropped != xywh
        self.cropped = xywh

    def get_tasks(self, include_crop=False):
        """Get the list of tasks that can be passed to "func:`ocr.process`."""
        tasks = []
        if include_crop:
            tasks.append(('crop', self.cropped))
        for index in range(self.task_list.count()):
            item = self.task_list.item(index)
            task = self.task_list.itemWidget(item).task()
            if task:
                tasks.append(task)
        return tasks

    def parameters(self, include_crop=False):
        """Returns a :class:`dict` of all keyword arguments that can be passed to :func:`ocr.apply`"""
        widget = self.tab.currentWidget()
        return dict(tasks=self.get_tasks(include_crop=include_crop), algorithm=widget.name, **widget.parameters())

    def process_image(self):
        """Calls :func:`ocr.process` using the current task list."""
        self.image_processed = process(self.image_unprocessed, tasks=self.get_tasks())
        self.image_item.setImage(self.image_processed)
        self.apply_ocr()

    def apply_ocr(self):
        """Apply OCR on an image that was already processed."""
        widget = self.tab.currentWidget()
        params = widget.parameters()
        if not params:
            # then the algorithm is not available
            self.ocr_text.setText('')
            return

        if widget.apply_locally:
            function = apply
            image = self.image_processed
        elif widget.ocr_service is not None:
            function = widget.ocr_service.apply
            image = to_base64(self.image_processed)
        elif widget.camera is not None:
            function = widget.camera.apply
            image = to_base64(self.image_processed)
        else:
            assert False, 'should never get here: {}'.format(self)

        # Only keep the latest request in the queue.
        # In particular, if the ROI is being dragged then this
        # method could be called numerous times for each
        # roi.sigRegionChanged signal
        while not self.queue.empty():
            self.queue.get()
        self.led.turn_on()
        self.queue.put((function, image, widget.name, params))
        self.ask_cache = True

    def on_update_text(self, text):
        """Slot for the OCRWorker.sig_ocr_text signal."""
        self.ocr_text.setText(text)
        self.led.turn_off()
