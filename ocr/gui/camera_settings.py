"""
Widget to interact with the camera settings.
"""
from msl.qt.convert import number_to_si
from msl.qt import (
    Qt,
    QtWidgets,
    SpinBox,
    DoubleSpinBox,
    application,
)

from ..utils import logger


class CameraSettings(QtWidgets.QWidget):

    def __init__(self, parent):
        """Interact with the camera settings.

        Parameters
        ----------
        parent : :class:`~ocr.gui.Configure`
            The main widget.
        """
        super(CameraSettings, self).__init__(parent=parent)

        self.camera = parent.camera
        self.main_widget_closing = False
        self.settings = self.camera.get_settings()
        constants = self.camera.get_constants()

        self.resolution_options = {
            'VGA': [640, 480],
            'SVGA': [800, 600],
            'XGA': [1024, 768],
            '720p': [1280, 720],
            'SXGA': [1280, 1024],
            'UXGA': [1600, 1200],
            '1080p': [1920, 1080],
            'MAX': constants['MAX_RESOLUTION'],
        }

        self.iso_options = {
            'AUTO': 0,
            '100': 100,
            '200': 200,
            '320': 320,
            '400': 400,
            '500': 500,
            '640': 640,
            '800': 800,
        }

        self.resolution = QtWidgets.QComboBox()
        self.resolution.setObjectName('resolution')
        for k, v in self.resolution_options.items():
            self.resolution.addItem(k, userData=v)
        text = self._key_from_value(self.resolution_options, self.settings['resolution'])
        if not text:
            text = '720p'
            self.camera.update_settings({'resolution': text})
        self.resolution.setCurrentText(text)
        self.resolution.currentTextChanged.connect(self.update_camera)

        self.iso = QtWidgets.QComboBox()
        self.iso.setObjectName('iso')
        for k, v in self.iso_options.items():
            self.iso.addItem(k, userData=v)
        text = self._key_from_value(self.iso_options, self.settings['iso'])
        if not text:
            text = 'AUTO'
            self.camera.update_settings({'iso': self.iso_options[text]})
        self.iso.setCurrentText(text)
        self.iso.currentTextChanged.connect(self.update_camera)

        self.digital_gain = QtWidgets.QLabel(f'{self.settings["digital_gain"]:.3f}')
        self.digital_gain.setObjectName('digital_gain')
        self.digital_gain.setToolTip('Digital gain')

        self.analog_gain = QtWidgets.QLabel(f'{self.settings["analog_gain"]:.3f}')
        self.analog_gain.setObjectName('analog_gain')
        self.analog_gain.setToolTip('Analog gain')

        self.meter_mode = QtWidgets.QComboBox()
        self.meter_mode.setObjectName('meter_mode')
        self.meter_mode.addItems(list(constants['METER_MODES'].keys()))
        self.meter_mode.setCurrentText(self.settings['meter_mode'])
        self.meter_mode.currentTextChanged.connect(self.update_camera)

        self.exposure_mode = QtWidgets.QComboBox()
        self.exposure_mode.setObjectName('exposure_mode')
        self.exposure_mode.addItems(list(constants['EXPOSURE_MODES'].keys()))
        self.exposure_mode.setCurrentText(self.settings['exposure_mode'])
        self.exposure_mode.currentTextChanged.connect(self.update_camera)

        self.flash_mode = QtWidgets.QComboBox()
        self.flash_mode.setObjectName('flash_mode')
        self.flash_mode.addItems(list(constants['FLASH_MODES'].keys()))
        self.flash_mode.setCurrentText(self.settings['flash_mode'])
        self.flash_mode.currentTextChanged.connect(self.update_camera)

        self.awb_mode = QtWidgets.QComboBox()
        self.awb_mode.setObjectName('awb_mode')
        self.awb_mode.addItems(list(constants['AWB_MODES'].keys()))
        self.awb_mode.setCurrentText(self.settings['awb_mode'])
        self.awb_mode.setToolTip('auto white balance mode')
        self.awb_mode.currentTextChanged.connect(self.update_camera)
        self.awb_mode.currentTextChanged.connect(self.enable_awb_gains)

        self.awb_gains_red = DoubleSpinBox(
            maximum=8.0, value=self.settings['awb_gains'][0], tooltip='Range=[0, 8]', decimals=2)
        self.awb_gains_red.setObjectName('awb_gains_red')
        self.awb_gains_red.setToolTip('<html>AWB gain for the red channel. '
                                      'Enabled if AWB mode is set to <i>off</i></html>.')
        self.awb_gains_red.resize(self.minimumSizeHint())
        self.awb_gains_red.editingFinished.connect(self.update_camera)

        self.awb_gains_blue = DoubleSpinBox(
            maximum=8.0, value=self.settings['awb_gains'][1], tooltip='Range=[0, 8]', decimals=2)
        self.awb_gains_blue.setObjectName('awb_gains_blue')
        self.awb_gains_blue.setToolTip('<html>AWB gain for the blue channel. '
                                       'Enabled if AWB mode is set to <i>off</i></html>.')
        self.awb_gains_blue.resize(self.minimumSizeHint())
        self.awb_gains_blue.editingFinished.connect(self.update_camera)
        self.enable_awb_gains(self.awb_mode.currentText())

        self.image_effect = QtWidgets.QComboBox()
        self.image_effect.setObjectName('image_effect')
        self.image_effect.setToolTip('Image effect')
        self.image_effect.addItems(list(constants['IMAGE_EFFECTS'].keys()))
        self.image_effect.setCurrentText(self.settings['image_effect'])
        self.image_effect.currentTextChanged.connect(self.update_camera)

        # image_effect_params -> goes with image_effect

        self.drc_strength = QtWidgets.QComboBox()
        self.drc_strength.setObjectName('drc_strength')
        self.drc_strength.addItems(list(constants['DRC_STRENGTHS'].keys()))
        self.drc_strength.setCurrentText(self.settings['drc_strength'])
        self.drc_strength.setToolTip('Dynamic range compression strength')
        self.drc_strength.currentTextChanged.connect(self.update_camera)

        self.rotation = QtWidgets.QComboBox()
        self.rotation.setObjectName('rotation')
        for item in ['0\u00b0', '90\u00b0', '180\u00b0', '270\u00b0']:
            self.rotation.addItem(item, userData=int(item.rstrip('\u00b0')))
        self.rotation.setCurrentText(str(self.settings['rotation']))
        self.rotation.setToolTip('Rotation')
        self.rotation.currentTextChanged.connect(self.update_camera)

        self.brightness = SpinBox(
            minimum=0, maximum=100, value=self.settings['brightness'], tooltip='Range=[0, 100]')
        self.brightness.setObjectName('brightness')
        self.brightness.editingFinished.connect(self.update_camera)

        self.contrast = SpinBox(
            minimum=-100, maximum=100, value=self.settings['contrast'], tooltip='Range=[-100, 100]')
        self.contrast.setObjectName('contrast')
        self.contrast.editingFinished.connect(self.update_camera)

        self.exposure_compensation = SpinBox(
            minimum=-25, maximum=25, value=self.settings['exposure_compensation'])
        self.exposure_compensation.setObjectName('exposure_compensation')
        self.exposure_compensation.setToolTip('Exposure compensation [-25, 25]')
        self.exposure_compensation.editingFinished.connect(self.update_camera)

        self.saturation = SpinBox(
            minimum=-100, maximum=100, value=self.settings['saturation'], tooltip='Range=[-100, 100]')
        self.saturation.setObjectName('saturation')
        self.saturation.editingFinished.connect(self.update_camera)

        self.sharpness = SpinBox(
            minimum=-100, maximum=100, value=self.settings['sharpness'],
            tooltip='Range=[-100, 100]')
        self.sharpness.setObjectName('sharpness')
        self.sharpness.editingFinished.connect(self.update_camera)

        self.shutter_speed = DoubleSpinBox(
            minimum=0, maximum=10, value=self.settings['shutter_speed'] * 1e-6,
            unit='s', use_si_prefix=True)
        self.shutter_speed.setObjectName('shutter_speed')
        self.shutter_speed.setToolTip('0 = auto')
        self.shutter_speed.editingFinished.connect(self.update_camera)

        self.exposure_speed = QtWidgets.QLabel(self._get_exposure_text(self.settings['exposure_speed']))
        self.exposure_speed.setObjectName('exposure_speed')
        self.exposure_speed.setToolTip('The actual shutter speed of the camera')

        # self.framerate = DoubleSpinBox(
        #     minimum=1, maximum=999, value=self.settings['framerate'], decimals=0,
        #     unit=' Hz', use_si_prefix=False)
        # self.framerate.setObjectName('framerate')
        # self.framerate.setToolTip('Frame rate')
        # self.framerate.editingFinished.connect(self.update_camera)

        self.quality = SpinBox(
            minimum=0, maximum=100, value=self.settings['quality'], tooltip='JPEG encoder quality factor, [0, 100]')
        self.quality.setObjectName('quality')
        self.quality.editingFinished.connect(self.update_camera)

        self.hflip = QtWidgets.QCheckBox()
        self.hflip.setObjectName('hflip')
        self.hflip.setToolTip('Horizontal flip')
        self.hflip.setChecked(self.settings['hflip'])
        self.hflip.stateChanged.connect(self.update_camera)

        self.vflip = QtWidgets.QCheckBox()
        self.vflip.setObjectName('vflip')
        self.vflip.setToolTip('Vertical flip')
        self.vflip.setChecked(self.settings['vflip'])
        self.vflip.stateChanged.connect(self.update_camera)

        # self.image_denoise = QtWidgets.QCheckBox()
        # self.image_denoise.setObjectName('image_denoise')
        # self.image_denoise.setChecked(self.settings['image_denoise'])
        # self.image_denoise.stateChanged.connect(self.update_camera)

        x, y, w, h = self.settings['zoom']
        self.zoom = QtWidgets.QLabel(f'x={x:.3f} y={y:.3f} w={w:.3f} h={h:.3f}')
        self.zoom.setObjectName('zoom')

        width = max(self.exposure_mode.sizeHint().width(), self.awb_mode.sizeHint().width())
        self.resolution.setFixedWidth(width)
        self.iso.setFixedWidth(width)
        self.meter_mode.setFixedWidth(width)
        self.exposure_mode.setFixedWidth(width)
        self.flash_mode.setFixedWidth(width)
        self.image_effect.setFixedWidth(width)
        self.drc_strength.setFixedWidth(width)
        self.brightness.setFixedWidth(width)
        self.contrast.setFixedWidth(width)
        self.exposure_compensation.setFixedWidth(width)
        self.saturation.setFixedWidth(width)
        self.sharpness.setFixedWidth(width)
        self.shutter_speed.setFixedWidth(width)
        self.rotation.setFixedWidth(width)
        self.quality.setFixedWidth(width)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(QtWidgets.QLabel('Resolution'), 0, 0, alignment=Qt.AlignRight)
        layout.addWidget(self.resolution, 0, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QtWidgets.QLabel('ISO'), 1, 0, alignment=Qt.AlignRight)
        layout.addWidget(self.iso, 1, 1, alignment=Qt.AlignLeft)
        layout.addWidget(self.digital_gain, 1, 2, alignment=Qt.AlignCenter)
        layout.addWidget(self.analog_gain, 1, 3, alignment=Qt.AlignCenter)
        layout.addWidget(QtWidgets.QLabel('Metering'), 2, 0, alignment=Qt.AlignRight)
        layout.addWidget(self.meter_mode, 2, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QtWidgets.QLabel('Exposure'), 3, 0, alignment=Qt.AlignRight)
        layout.addWidget(self.exposure_mode, 3, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QtWidgets.QLabel('Flash'), 4, 0, alignment=Qt.AlignRight)
        layout.addWidget(self.flash_mode, 4, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QtWidgets.QLabel('AWB'), 5, 0, alignment=Qt.AlignRight)
        layout.addWidget(self.awb_mode, 5, 1, alignment=Qt.AlignLeft)
        layout.addWidget(self.awb_gains_red, 5, 2, alignment=Qt.AlignLeft)
        layout.addWidget(self.awb_gains_blue, 5, 3, alignment=Qt.AlignLeft)
        layout.addWidget(QtWidgets.QLabel('Effect'), 6, 0, alignment=Qt.AlignRight)
        layout.addWidget(self.image_effect, 6, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QtWidgets.QLabel('DRC'), 7, 0, alignment=Qt.AlignRight)
        layout.addWidget(self.drc_strength, 7, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QtWidgets.QLabel('Brightness'), 8, 0, alignment=Qt.AlignRight)
        layout.addWidget(self.brightness, 8, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QtWidgets.QLabel('Contrast'), 9, 0, alignment=Qt.AlignRight)
        layout.addWidget(self.contrast, 9, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QtWidgets.QLabel('Compensation'), 10, 0, alignment=Qt.AlignRight)
        layout.addWidget(self.exposure_compensation, 10, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QtWidgets.QLabel('Saturation'), 11, 0, alignment=Qt.AlignRight)
        layout.addWidget(self.saturation, 11, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QtWidgets.QLabel('Sharpness'), 12, 0, alignment=Qt.AlignRight)
        layout.addWidget(self.sharpness, 12, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QtWidgets.QLabel('Shutter speed'), 13, 0, alignment=Qt.AlignRight)
        layout.addWidget(self.shutter_speed, 13, 1, alignment=Qt.AlignLeft)
        layout.addWidget(self.exposure_speed, 13, 2, 1, 2, alignment=Qt.AlignLeft)
        layout.addWidget(QtWidgets.QLabel('Orientation'), 14, 0, alignment=Qt.AlignRight)
        layout.addWidget(self.rotation, 14, 1, alignment=Qt.AlignLeft)
        layout.addWidget(self.hflip, 14, 2, alignment=Qt.AlignCenter)
        layout.addWidget(self.vflip, 14, 3, alignment=Qt.AlignCenter)
        layout.addWidget(QtWidgets.QLabel('Quality'), 15, 0, alignment=Qt.AlignRight)
        layout.addWidget(self.quality, 15, 1, alignment=Qt.AlignLeft)
        layout.addWidget(QtWidgets.QLabel('Zoom'), 16, 0, alignment=Qt.AlignRight)
        layout.addWidget(self.zoom, 16, 1, 1, 3, alignment=Qt.AlignLeft)
        # layout.addWidget(QtWidgets.QLabel('Denoise'), 15, 0, alignment=Qt.AlignRight)
        # layout.addWidget(self.image_denoise, 15, 1, alignment=Qt.AlignLeft)
        layout.addItem(QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding), 17, 0)
        self.setLayout(layout)

    def update_camera(self):
        if self.main_widget_closing:
            # if a SpinBox has focus and the parent widget is closing
            # then the SpinBox will first loose focus, before the close
            # event finishes, which cause self.update_camera() to be called
            # (which we don't want)
            return

        application().processEvents()

        self.parent().pause_capture()
        sender = self.sender()
        name = sender.objectName()
        settings = {}

        if isinstance(sender, QtWidgets.QComboBox):
            value = sender.currentData()
            if value is None:
                value = sender.currentText()
        elif isinstance(sender, QtWidgets.QAbstractSpinBox):
            value = sender.value()
            if name == 'shutter_speed':
                if value > 0:
                    settings.update(framerate=1.0/value)
                else:
                    settings.update(framerate=30)
                value = int(value * 1e6)
            elif name in ('awb_gains_red', 'awb_gains_blue'):
                name = 'awb_gains'
                value = [self.awb_gains_red.value(), self.awb_gains_blue.value()]
        else:  # QtWidgets.QCheckBox
            value = sender.isChecked()

        settings.update({name: value})
        logger.info('camera set %s', settings)
        self.camera.update_settings(settings)
        self.parent().start_capture()

    def update_displayed_values(self, settings):
        """Changing one setting can change others.

        This method ensures that the user sees the actual
        settings of the camera.
        """
        if self.main_widget_closing:
            return

        self.settings = settings
        for child in self.children():
            name = child.objectName()
            if not name:
                continue
            child.blockSignals(True)
            if isinstance(child, QtWidgets.QComboBox):
                text = self.settings[name]
                if name == 'resolution':
                    text = self._key_from_value(self.resolution_options, text)
                elif name == 'iso':
                    text = self._key_from_value(self.iso_options, text)
                elif name == 'rotation':
                    text = str(text)
                logger.debug('set %s to %s', child, text)
                child.setCurrentText(text)
            elif isinstance(child, QtWidgets.QAbstractSpinBox) and not child.hasFocus():
                if name == 'awb_gains_red':
                    value = self.settings['awb_gains'][0]
                elif name == 'awb_gains_blue':
                    value = self.settings['awb_gains'][1]
                else:
                    value = self.settings[name]
                    if name == 'shutter_speed':
                        value *= 1e-6
                logger.debug('set %s to %s', child, value)
                child.setValue(value)
            elif isinstance(child, QtWidgets.QCheckBox):
                checked = self.settings[name]
                logger.debug('set %s to %s', child, checked)
                child.setChecked(checked)
            elif isinstance(child, QtWidgets.QLabel):
                if name == 'zoom':
                    x, y, w, h = self.settings[name]
                    text = f'x={x:.3f} y={y:.3f} w={w:.3f} h={h:.3f}'
                elif name == 'exposure_speed':
                    text = self._get_exposure_text(self.settings[name])
                else:
                    text = f'{self.settings[name]:.3f}'
                logger.debug('set %s to %s', child, text)
                child.setText(text)
            child.blockSignals(False)

    def enable_awb_gains(self, text):
        """Slot for the AWB combobox."""
        self.awb_gains_red.setEnabled(text == 'off')
        self.awb_gains_blue.setEnabled(text == 'off')

    def main_closing(self):
        """Slot for the parent widgets closing event."""
        self.main_widget_closing = True

    def _key_from_value(self, options, actual_value):
        for name, value in options.items():
            if actual_value == value:
                return name

    def _get_exposure_text(self, exposure_speed):
        value, suffix = number_to_si(exposure_speed * 1e-6)
        if suffix:
            return f'{value:.2f} {suffix}s'
        return f'{value:.2f} s'
