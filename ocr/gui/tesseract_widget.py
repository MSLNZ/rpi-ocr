"""Widget for the tesseract algorithm."""
import sys

from msl.qt import QtWidgets

from ..tesseract import (
    languages,
    version,
    set_tesseract_path,
)
from .algorithm_widget import Algorithm

IS_WINDOWS = sys.platform == 'win32'


class Tesseract(Algorithm):

    def __init__(self, parent, grandparent):
        """Widget for the tesseract algorithm."""
        super(Tesseract, self).__init__(parent, grandparent)

        self._apply_locally = False

        try:
            self._languages, self._version = languages(), version()
            self._apply_locally = True
        except FileNotFoundError:
            if self.camera is not None:
                self._languages, self._version = self.camera.tesseract_info()
            elif grandparent.ocr_service is not None:
                self._languages, self._version = grandparent.ocr_service.tesseract_info()
            else:
                self._version = ''

        if self._version:
            self.create_layout()
        else:
            self.create_default_layout()

    @property
    def name(self):
        return 'tesseract'

    @property
    def apply_locally(self):
        return self._apply_locally

    def parameters(self):
        if not self._version:
            return {}
        return {
            'language': self.languages.currentText(),
            'psm': self.psm.currentData(),
            'oem': self.oem.currentData(),
            'whitelist': self.whitelist.text(),
            'timeout': self.timeout.value(),
            'nice': 0 if IS_WINDOWS else self.nice.value(),
            'config': self.config.text(),
        }

    def update_executable_path(self, path):
        set_tesseract_path(path)
        self._languages, self._version = languages(), version()
        self._apply_locally = True

    def new_service_connection(self, service):
        self._languages, self._version = service.tesseract_info()

    def create_layout(self):
        """Create the widgets and the layout (only if tesseract is available)."""

        apply_ocr = self.find_roi_preview_widget().apply_ocr

        self.languages = QtWidgets.QComboBox()
        self.languages.addItems(self._languages)
        self.languages.currentTextChanged.connect(apply_ocr)

        self.psm = QtWidgets.QComboBox()
        items = [
            # ('Orientation and script detection (OSD) only', 0),
            # ('Automatic page segmentation with OSD', 1),
            # ('Automatic page segmentation, but no OSD, or OCR. (not implemented)', 2),
            # ('Fully automatic page segmentation, but no OSD', 3),
            ('Single column of text of variable sizes', 4),
            ('Single uniform block of vertically aligned text', 5),
            ('Single uniform block of text', 6),
            ('Single text line', 7),
            ('Single word', 8),
            ('Single word in a circle', 9),
            ('Single character', 10),
            ('Sparse text', 11),
            ('Sparse text with OSD', 12),
            ('Raw line', 13),
        ]
        for text, value in items:
            self.psm.addItem(text, userData=value)
        self.psm.setCurrentText('Single word')
        self.psm.setToolTip('Page segmentation mode')
        self.psm.currentTextChanged.connect(apply_ocr)

        self.oem = QtWidgets.QComboBox()
        items = [
            ('Legacy engine only', 0),
            ('Neural nets LSTM engine only', 1),
            ('Legacy + LSTM engines', 2),
            ('Based on what is available', 3)
        ]
        for text, value in items:
            self.oem.addItem(text, userData=value)
        self.oem.setCurrentIndex(3)
        self.oem.setToolTip('OCR engine mode')
        self.oem.currentTextChanged.connect(apply_ocr)

        self.whitelist = QtWidgets.QLineEdit()
        self.whitelist.setText('0123456789+-.')
        self.whitelist.setToolTip('The character set that the result must be in')
        self.whitelist.textChanged.connect(apply_ocr)

        self.timeout = QtWidgets.QDoubleSpinBox()
        self.timeout.setSuffix(' s')
        self.timeout.setToolTip('Timeout. The maximum number of seconds to wait for the result')

        if not IS_WINDOWS:
            self.nice = QtWidgets.QSpinBox()
            self.nice.setMaximum(9)
            self.nice.setToolTip('The processor priority')
            # self.nice.valueChanged.connect(parent.apply_ocr)

        self.config = QtWidgets.QLineEdit()
        self.config.setToolTip('<html>Any additional configuration parameters, e.g.,<br>'
                               '-c tessedit_char_blacklist=C</html>')
        self.config.editingFinished.connect(apply_ocr)

        layout = QtWidgets.QFormLayout()
        layout.addRow('Language', self.languages)
        layout.addRow('PSM', self.psm)
        layout.addRow('OEM', self.oem)
        layout.addRow('Whitelist', self.whitelist),
        # TODO Displaying the timeout can be misleading if sending a request to a remote camera
        #  since pytesseract accepts a timeout kwarg and there could be a network timeout.
        #  Ideally timeout = tesseract execution + network delay. Still include the timeout
        #  in self.parameters() to remind people that the parameter still exists.
        # layout.addWidget(self.timeout),
        if not IS_WINDOWS:
            layout.addRow('Nice', self.nice),
        layout.addRow('Additional', self.config)
        layout.addWidget(QtWidgets.QLabel(f'<html><i>Tesseract-OCR {self._version}</i></html>'))
        layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.setLayout(layout)
