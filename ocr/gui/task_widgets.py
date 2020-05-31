"""
Image-processing widgets.
"""
from msl.qt import (
    Qt,
    QtWidgets,
    SpinBox,
)


class TaskList(QtWidgets.QListWidget):

    def __init__(self, parent):
        """Image-processing tasks."""
        super(TaskList, self).__init__(parent=parent)

        # It is weired that defining this attribute is okay.
        # See ocr.gui.algorithm_widget.Algorithm where this caused
        # a server random crash of the GUI.
        self.roi_preview = parent

        self.widget_map = {
            'Greyscale': Greyscale,
            'Threshold': Threshold,
            'Gaussian blur': GaussianBlur,
            'Dilate': Dilate,
            'Erode': Erode,
            'Rotate': Rotate,
            'Invert': Invert,
            'Adaptive threshold': AdaptiveThreshold,
            'Opening': Opening,
            'Closing': Closing,
        }

        self.setDragDropMode(QtWidgets.QListWidget.InternalMove)
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)

    def keyReleaseEvent(self, event):
        """Overrides QListWidget.keyReleaseEvent event."""
        if event.key() == Qt.Key_Delete and self.hasFocus():
            self.takeItem(self.currentRow())
            self.roi_preview.process_image()
        super(TaskList, self).keyReleaseEvent(event)

    def dropEvent(self, event):
        """Overrides QListWidget.dropEvent event."""
        super(TaskList, self).dropEvent(event)
        self.roi_preview.process_image()

    def on_add_item(self):
        """Slot to add a new task."""
        name = self.sender().objectName()
        widget = self.widget_map[name](self.roi_preview)
        item = QtWidgets.QListWidgetItem()
        item.setSizeHint(widget.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, widget)
        self.roi_preview.process_image()


class Greyscale(QtWidgets.QWidget):

    def __init__(self, parent):
        super(Greyscale, self).__init__(parent=parent)

        self.checkbox = QtWidgets.QCheckBox()
        self.checkbox.setChecked(True)
        self.checkbox.stateChanged.connect(parent.process_image)
        self.checkbox.setToolTip('Apply?')

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Greyscale:'))
        layout.addWidget(self.checkbox)
        layout.addStretch()
        self.setLayout(layout)

    def task(self):
        if self.checkbox.isChecked():
            # return a tuple
            return 'greyscale', None


class Invert(QtWidgets.QWidget):

    def __init__(self, parent):
        super(Invert, self).__init__(parent=parent)

        self.checkbox = QtWidgets.QCheckBox()
        self.checkbox.setChecked(True)
        self.checkbox.stateChanged.connect(parent.process_image)
        self.checkbox.setToolTip('Apply?')

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Invert:'))
        layout.addWidget(self.checkbox)
        layout.addStretch()
        self.setLayout(layout)

    def task(self):
        if self.checkbox.isChecked():
            # return a tuple
            return 'invert', None


class Threshold(QtWidgets.QWidget):

    def __init__(self, parent):
        super(Threshold, self).__init__(parent=parent)

        self.spinbox = SpinBox(maximum=255, value=127, tooltip='0..255')
        self.spinbox.editingFinished.connect(parent.process_image)
        self.spinbox.setDisabled(False)
        self.spinbox.resize(self.spinbox.minimumSizeHint())

        self.checkbox = QtWidgets.QCheckBox()
        self.checkbox.setToolTip('Apply?')
        self.checkbox.setChecked(True)
        self.checkbox.stateChanged.connect(parent.process_image)
        self.checkbox.stateChanged.connect(lambda value: self.spinbox.setEnabled(value))

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Threshold:'))
        layout.addWidget(self.spinbox)
        layout.addWidget(self.checkbox)
        layout.addStretch()
        self.setLayout(layout)

    def task(self):
        if self.checkbox.isChecked():
            return 'threshold', self.spinbox.value()


class Rotate(QtWidgets.QWidget):

    def __init__(self, parent):
        super(Rotate, self).__init__(parent=parent)

        self.spinbox = SpinBox(minimum=-180, maximum=180, unit=' \u00B0')
        self.spinbox.editingFinished.connect(parent.process_image)
        self.spinbox.resize(self.spinbox.minimumSizeHint())

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Rotate:'))
        layout.addWidget(self.spinbox)
        layout.addStretch()
        self.setLayout(layout)

    def task(self):
        if self.spinbox.value():
            return 'rotate', self.spinbox.value()


class GaussianBlur(QtWidgets.QWidget):

    def __init__(self, parent):
        super(GaussianBlur, self).__init__(parent=parent)

        self.spinbox = SpinBox(tooltip='Gaussian blur radius', value=1)
        self.spinbox.editingFinished.connect(parent.process_image)
        self.spinbox.resize(self.spinbox.minimumSizeHint())

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Gaussian blur:'))
        layout.addWidget(self.spinbox)
        layout.addStretch()
        self.setLayout(layout)

    def task(self):
        if self.spinbox.value() > 0:
            return 'gaussian_blur', self.spinbox.value()


class Dilate(QtWidgets.QWidget):

    def __init__(self, parent):
        super(Dilate, self).__init__(parent=parent)

        self.radius = SpinBox(tooltip='radius', value=1)
        self.radius.editingFinished.connect(parent.process_image)
        self.radius.resize(self.radius.minimumSizeHint())

        self.iterations = SpinBox(tooltip='number of iterations', minimum=1)
        self.iterations.editingFinished.connect(parent.process_image)
        self.iterations.resize(self.iterations.minimumSizeHint())

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Dilate:'))
        layout.addWidget(self.radius)
        layout.addWidget(self.iterations)
        layout.addStretch()
        self.setLayout(layout)

    def task(self):
        if self.radius.value() > 0:
            return 'dilate', {'radius': self.radius.value(), 'iterations': self.iterations.value()}


class Erode(QtWidgets.QWidget):

    def __init__(self, parent):
        super(Erode, self).__init__(parent=parent)

        self.radius = SpinBox(tooltip='radius', value=1)
        self.radius.editingFinished.connect(parent.process_image)
        self.radius.resize(self.radius.minimumSizeHint())

        self.iterations = SpinBox(tooltip='number of iterations', minimum=1)
        self.iterations.editingFinished.connect(parent.process_image)
        self.iterations.resize(self.iterations.minimumSizeHint())

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Erode:'))
        layout.addWidget(self.radius)
        layout.addWidget(self.iterations)
        layout.addStretch()
        self.setLayout(layout)

    def task(self):
        if self.radius.value() > 0:
            return 'erode', {'radius': self.radius.value(), 'iterations': self.iterations.value()}


class AdaptiveThreshold(QtWidgets.QWidget):

    def __init__(self, parent):
        super(AdaptiveThreshold, self).__init__(parent=parent)

        self.use_mean = QtWidgets.QCheckBox()
        self.use_mean.setToolTip('Checked: Use mean algorithm\nUnchecked: Use gaussian algorithm')
        self.use_mean.setChecked(True)
        self.use_mean.stateChanged.connect(parent.process_image)

        self.radius = SpinBox(tooltip='radius', value=2)
        self.radius.editingFinished.connect(parent.process_image)
        self.radius.resize(self.radius.minimumSizeHint())

        self.constant = SpinBox(
            tooltip='A constant which is subtracted from the mean or weighted mean calculated',
            maximum=255,
            minimum=-255,
        )
        self.constant.editingFinished.connect(parent.process_image)
        self.constant.resize(self.constant.minimumSizeHint())

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Adaptive threshold:'))
        layout.addWidget(self.use_mean)
        layout.addWidget(self.radius)
        layout.addWidget(self.constant)
        layout.addStretch()
        self.setLayout(layout)

    def task(self):
        if self.radius.value() > 0:
            kwargs = {
                'use_mean': self.use_mean.isChecked(),
                'radius': self.radius.value(),
                'c': self.constant.value()
            }
            return 'adaptive_threshold', kwargs


class Opening(QtWidgets.QWidget):

    def __init__(self, parent):
        super(Opening, self).__init__(parent=parent)

        self.radius = SpinBox(tooltip='radius', value=1)
        self.radius.editingFinished.connect(parent.process_image)
        self.radius.resize(self.radius.minimumSizeHint())

        self.iterations = SpinBox(tooltip='number of iterations', minimum=1)
        self.iterations.editingFinished.connect(parent.process_image)
        self.iterations.resize(self.iterations.minimumSizeHint())

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Opening:'))
        layout.addWidget(self.radius)
        layout.addWidget(self.iterations)
        layout.addStretch()
        self.setLayout(layout)

    def task(self):
        if self.radius.value() > 0:
            return 'opening', {'radius': self.radius.value(), 'iterations': self.iterations.value()}


class Closing(QtWidgets.QWidget):

    def __init__(self, parent):
        super(Closing, self).__init__(parent=parent)

        self.radius = SpinBox(tooltip='radius', value=1)
        self.radius.editingFinished.connect(parent.process_image)
        self.radius.resize(self.radius.minimumSizeHint())

        self.iterations = SpinBox(tooltip='number of iterations', minimum=1)
        self.iterations.editingFinished.connect(parent.process_image)
        self.iterations.resize(self.iterations.minimumSizeHint())

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel('Closing:'))
        layout.addWidget(self.radius)
        layout.addWidget(self.iterations)
        layout.addStretch()
        self.setLayout(layout)

    def task(self):
        if self.radius.value() > 0:
            return 'closing', {'radius': self.radius.value(), 'iterations': self.iterations.value()}
