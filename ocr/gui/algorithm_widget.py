import sys

from msl.qt import (
    QtWidgets,
    Button,
    Signal,
    prompt,
)

from . import (
    icons,
    ON_RPI,
)
from .connection import prompt_for_service_kwargs

if not ON_RPI:
    # The only reason why we need to import shiboken2 is to delete a layout.
    # When installing PySide2 in the virtual environment on the Raspberry Pi
    # the shiboken2 module does not get installed. However, we don't need to
    # delete a layout on the Raspberry Pi since ssocr and tesseract are
    # automatically installed in the rpi-setup.sh script and therefore are
    # always available. The layout needed to be deleted if the user was on,
    # for example, Windows and the ssocr/tesseract executables were not
    # available on the local computer and the user uses a Button on the layout
    # to either connect to the OCR Service on a Raspberry Pi or to add the
    # location of the executable to PATH. After the OCR Service is available or
    # the path tot he executable is know the layout is redrawn with the widgets
    # for changing the kwargs passed to the OCR algorithm.
    import shiboken2


class Algorithm(QtWidgets.QWidget):

    sig_new_service = Signal(object)

    def __init__(self, parent, grandparent):
        """Base class for displaying the widgets of an algorithm."""
        super(Algorithm, self).__init__(parent=parent)

        # Defining this caused the GUI to (sometimes) crash randomly
        # and unexpectedly when the ROIPreview widget closed.
        # Created the self.find_roi_preview_widget() method instead.
        # However, defining "self.roi_preview = parent" in
        # ocr.gui.task_widgets.TaskList does not cause the crash.
        #self.roi_preview = parent

        self.sig_new_service.connect(grandparent.on_new_service)

        if grandparent.camera is not None and not ON_RPI:
            # create a new connection so that captures and OCR requests can be
            # made simultaneously, otherwise if the same connection is used
            # then the following exception will be raised
            #   ValueError: Requests are pending ...
            self.camera = grandparent.camera.spawn(name=grandparent.camera.name)
        else:
            self.camera = None

        if grandparent.ocr_service is not None and not ON_RPI:
            self.ocr_service = grandparent.ocr_service.spawn(name=grandparent.ocr_service.name)
        else:
            self.ocr_service = None

    def closeEvent(self, event):
        """Override :meth:`QWidget.closeEvent`."""
        if self.camera is not None:
            self.camera.disconnect()
        if self.ocr_service is not None:
            self.ocr_service.disconnect()
        super(Algorithm, self).closeEvent(event)

    def create_default_layout(self):
        """The default layout to display if the algorithm is not available."""
        message = '<html>{0} is not available. You have three options:' \
                  '<ul>' \
                  '<li>set the path to the {0} executable by calling' \
                  ' ocr.set_{0}_path() before showing the GUI,</li>' \
                  '<li>connect to a Raspberry Pi, or</li>' \
                  '<li>browse for the executable.</li>' \
                  '</ul>' \
                  '</html>'.format(self.name)
        layout = QtWidgets.QFormLayout()
        label = QtWidgets.QLabel(message)
        label.setWordWrap(True)
        layout.addWidget(label)
        hbox = QtWidgets.QHBoxLayout()
        size = icons.browse.availableSizes()[-1]
        hbox.addWidget(Button(tooltip='Connect', icon=icons.rpi, icon_size=size, left_click=self.connect_to_rpi))
        hbox.addWidget(Button(tooltip='Browse', icon=icons.browse, icon_size=size, left_click=self.browse))
        layout.addItem(hbox)
        self.setLayout(layout)

    def find_roi_preview_widget(self):
        """Search the parent tree for :class:`ocr.gui.ROIPreview`."""
        # The ROIPreview widget can change where it is located in the ancestor tree.
        # For example, if self.create_layout() is called when the subclass is
        # instantiated then self.parent() == ROIPreview. If self.create_default_layout()
        # is called when the subclass is instantiated then the parents are:
        #   PySide2.QtWidgets.QStackedWidget
        #   PySide2.QtWidgets.QTabWidget
        #   PySide2.QtWidgets.QWidget
        #   PySide2.QtWidgets.QSplitter
        #   ocr.gui.roi_preview.ROIPreview
        parent = self.parent()
        while parent.objectName() != 'ROIPreview':
            parent = parent.parent()
        return parent

    def browse(self):
        title = 'Select the {} executable'.format(self.name)
        extn = '.exe' if sys.platform == 'win32' else ''
        filters = 'OCR ({}{})'.format(self.name, extn)
        filename = prompt.filename(title=title, filters=filters)
        if filename:
            self.update_executable_path(filename)
            self.delete_layout(self.layout())
            self.create_layout()
            self.find_roi_preview_widget().apply_ocr()

    def connect_to_rpi(self):
        """Connect to a Raspberry Pi to apply OCR."""
        kwargs = self.find_roi_preview_widget().config.get('camera')
        service = prompt_for_service_kwargs(kwargs)
        if service is None:
            return
        # emit the new service so that all ROIPreview's will
        # call Algorithm.refresh_layout() for each Algorithm widget
        self.sig_new_service.emit(service)

    def refresh_layout(self, service):
        """Called by the Configure.on_new_service() slot."""
        if self.ocr_service is None:
            self.ocr_service = service.spawn(name=service.name)
        self.new_service_connection(service)
        self.delete_layout(self.layout())
        self.create_layout()

    def delete_layout(self, layout):
        """Delete the layout and all its children widgets."""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            elif isinstance(item, QtWidgets.QLayout):
                self.delete_layout(item)
        shiboken2.delete(layout)

    @property
    def name(self):
        """The subclass must return a :class:`str` of the name of the algorithm."""
        raise NotImplementedError

    @property
    def apply_locally(self):
        """:class:`bool`: Whether the algorithm can be applied on the local computer."""
        raise NotImplementedError

    def new_service_connection(self, service):
        """Called after a connection to a Raspberry Pi was successfully established."""
        raise NotImplementedError

    def create_layout(self):
        """Create the widgets for the algorithm and add them to a layout."""
        raise NotImplementedError

    def parameters(self):
        """Return a :class:`dict` of the keyword arguments passed to :func:`ocr.ocr`."""
        raise NotImplementedError

    def update_executable_path(self, path):
        """Called after the executable was selected from the prompt."""
        raise NotImplementedError
