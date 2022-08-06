"""Widget for the ssocr algorithm."""
from msl.qt import (
    QtWidgets,
    SpinBox,
)

from ..ssocr import (
    version,
    Luminance,
    set_ssocr_path,
    charset_map,
)
from .algorithm_widget import Algorithm


class SSOCR(Algorithm):

    def __init__(self, parent, grandparent):
        """Widget for the ssocr algorithm."""
        super(SSOCR, self).__init__(parent, grandparent)

        self._apply_locally = False

        try:
            self._version = version()
            self._apply_locally = True
        except FileNotFoundError:
            if self.camera is not None:
                self._version = self.camera.ssocr_version()
            elif grandparent.ocr_service is not None:
                self._version = grandparent.ocr_service.ssocr_version()
            else:
                self._version = ''

        if self._version:
            self.create_layout()
        else:
            self.create_default_layout()

    @property
    def name(self):
        return 'ssocr'

    @property
    def apply_locally(self):
        return self._apply_locally

    def parameters(self):
        if not self._version:
            return {}
        return {
            # 'threshold': self.threshold.value(),
            # 'absolute_threshold': not self.absolute_threshold.isChecked(),
            # 'iter_threshold': self.iter_threshold.isChecked(),
            'needed_pixels': self.needed_pixels.value(),
            'ignored_pixels': self.ignored_pixels.value(),
            'num_digits': self.num_digits.value(),
            'one_ratio': self.one_ratio.value(),
            'minus_ratio': self.minus_ratio.value(),
            # 'foreground': 'black' if self.fg_black.isChecked() else 'white',
            'luminance': self.luminance.currentData(),
            'as_hex': self.as_hex.isChecked(),
            'omit_decimal_point': self.omit_decimal_point.isChecked(),
            'charset': self.charset.currentData(),
        }

    def update_executable_path(self, path):
        set_ssocr_path(path)
        self._version = version()
        self._apply_locally = True

    def new_service_connection(self, service):
        self._version = service.ssocr_version()

    def create_layout(self):
        """Create the widgets and the layout (only if ssocr is available)."""
        apply_ocr = self.find_roi_preview_widget().apply_ocr

        # self.threshold = SpinBox(value=50, unit=' %')
        # self.threshold.setEnabled(False)
        # self.threshold.valueChanged.connect(apply_ocr)
        #
        # self.iter_threshold = QtWidgets.QCheckBox()
        # self.iter_threshold.setEnabled(False)
        # self.iter_threshold.setToolTip('Use an iterative threshold method?')
        # self.iter_threshold.stateChanged.connect(apply_ocr)
        #
        # self.absolute_threshold = QtWidgets.QCheckBox()
        # self.absolute_threshold.setToolTip('Apply?')
        # self.absolute_threshold.stateChanged.connect(self.threshold.setEnabled)
        # self.absolute_threshold.stateChanged.connect(self.iter_threshold.setEnabled)
        # self.absolute_threshold.stateChanged.connect(apply_ocr)

        self.needed_pixels = SpinBox(minimum=1)
        self.needed_pixels.setToolTip('Number of pixels needed to recognize a segment')
        self.needed_pixels.valueChanged.connect(apply_ocr)

        self.ignored_pixels = SpinBox()
        self.ignored_pixels.setToolTip('Number of pixels ignored when searching digit boundaries')
        self.ignored_pixels.valueChanged.connect(apply_ocr)

        self.num_digits = SpinBox(minimum=-1, value=-1)
        self.num_digits.setToolTip('Number of digits in image (-1 for auto)')
        self.num_digits.valueChanged.connect(apply_ocr)

        self.one_ratio = SpinBox(minimum=1, value=3)
        self.one_ratio.setToolTip('Minimum height/width ratio to recognize the number one')
        self.one_ratio.valueChanged.connect(apply_ocr)

        self.minus_ratio = SpinBox(minimum=1, value=2)
        self.minus_ratio.setToolTip('Minimum width/height ratio to recognize a minus sign')
        self.minus_ratio.valueChanged.connect(apply_ocr)

        # foreground = QtWidgets.QGroupBox()
        # self.fg_black = QtWidgets.QRadioButton('black')
        # self.fg_white = QtWidgets.QRadioButton('white')
        # self.fg_black.setChecked(True)
        # self.fg_black.clicked.connect(apply_ocr)
        # self.fg_white.clicked.connect(apply_ocr)
        # fg_hbox = QtWidgets.QHBoxLayout()
        # fg_hbox.addWidget(self.fg_black)
        # fg_hbox.addWidget(self.fg_white)
        # foreground.setLayout(fg_hbox)

        self.as_hex = QtWidgets.QCheckBox()
        self.as_hex.setToolTip('Change the output text to hexadecimal?')
        self.as_hex.stateChanged.connect(apply_ocr)

        self.omit_decimal_point = QtWidgets.QCheckBox()
        self.omit_decimal_point.setToolTip('Whether to omit decimal points from the output. Decimal points are '
                                           'still recognized and counted against the number of digits. This '
                                           'can be used together with automatically detecting the number of '
                                           'digits to ignore isolated groups of pixels in an image.')
        self.omit_decimal_point.stateChanged.connect(apply_ocr)

        self.luminance = QtWidgets.QComboBox()
        for name, value in Luminance.__members__.items():
            self.luminance.addItem(name, userData=value.name)
        self.luminance.setToolTip('Compute luminance using this formula')
        self.luminance.setCurrentText(Luminance.REC709.name)
        self.luminance.currentTextChanged.connect(apply_ocr)

        self.charset = QtWidgets.QComboBox()
        index = 0
        for i, (name, value) in enumerate(charset_map):
            self.charset.addItem(value, userData=name)
            if name == 'decimal':
                index = i
        self.charset.setToolTip('The set of characters that ssocr can recognize')
        self.charset.setCurrentIndex(index)
        self.charset.currentTextChanged.connect(apply_ocr)

        # threshold_layout = QtWidgets.QHBoxLayout()
        # threshold_layout.addWidget(self.threshold)
        # threshold_layout.addWidget(self.iter_threshold)
        # threshold_layout.addWidget(self.absolute_threshold)

        layout = QtWidgets.QFormLayout()
        # layout.addRow('Threshold', threshold_layout)
        layout.addRow('Needed pixels', self.needed_pixels)
        layout.addRow('Ignored pixels', self.ignored_pixels)
        layout.addRow('# digits', self.num_digits)
        layout.addRow('One ratio', self.one_ratio)
        layout.addRow('Minus ratio', self.minus_ratio)
        # layout.addRow('Foreground', foreground)
        layout.addRow('Luminance', self.luminance)
        layout.addRow('As hex', self.as_hex)
        layout.addRow('Omit decimal', self.omit_decimal_point)
        layout.addRow('Charset', self.charset)
        layout.addWidget(QtWidgets.QLabel(f'<html><i>ssocr {self._version}</i></html>'))
        layout.addItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        self.setLayout(layout)
