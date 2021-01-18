from msl.qt import (
    Qt,
    QtWidgets,
    SpinBox,
    application,
    prompt,
)

from .. import (
    ON_RPI,
    camera,
    service,
)
from ..cameras import kill_camera_service
from ..services import kill_ocr_service


class ConnectRPi(QtWidgets.QDialog):

    def __init__(self, parent=None):
        """Create a dialog to get the information to conenct to a Raspberry Pi."""
        super(ConnectRPi, self).__init__(parent, Qt.WindowCloseButtonHint)
        self.setWindowTitle('Connect to a Raspberry Pi')

        self.host = QtWidgets.QLineEdit('raspberrypi')
        self.port = SpinBox(maximum=65535, value=1875)
        self.username = QtWidgets.QLineEdit('pi')
        self.password = QtWidgets.QLineEdit()
        self.password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

        self.assert_hostname = QtWidgets.QCheckBox()
        self.assert_hostname.setChecked(False)

        buttonbox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)

        layout = QtWidgets.QFormLayout()
        layout.addRow('Host', self.host)
        layout.addRow('Port', self.port)
        layout.addRow('Username', self.username)
        layout.addRow('Password', self.password)
        layout.addRow('Assert hostname', self.assert_hostname)
        layout.addWidget(buttonbox)
        self.setLayout(layout)


def get_kwargs(config):
    """Get the keyword arguments from the config"""
    if not config:
        rpi = ConnectRPi()
        if not rpi.exec_():
            return

        config = {
            'host': rpi.host.text(),
            'port': rpi.port.value(),
            'rpi_username': rpi.username.text(),
            'rpi_password': rpi.password.text(),
            'assert_hostname': rpi.assert_hostname.isChecked(),
        }

    if not config.get('rpi_password'):
        pw = prompt.password('Enter the password for the Raspberry Pi')
        if not pw:
            return
        config['rpi_password'] = pw

    return config


def prompt_for_camera_kwargs(config=None):
    """Prompt the user for the kwargs to send to :func:`ocr.camera`.

    Parameters
    ----------
    config : :class:`dict`, optional
        If executing on a Raspberry Pi then no prompt is displayed and `config`
        is passed to :func:`ocr.camera`. Otherwise, if `config` is not specified
        then a dialog is displayed for the user to enter the information necessary
        to connect to the camera. If only the ``rpi_password`` key is missing from
        `config` then the password will be asked for in a simple text prompt.

    Returns
    -------
    The object returned by :func:`ocr.camera` or :data:`None` if the user chose
    to cancel the prompt.
    """
    if config is None:
        config = {}

    if ON_RPI:
        return camera(**config)

    kwargs = get_kwargs(config)
    if kwargs is None:
        return

    try:
        application().setOverrideCursor(Qt.WaitCursor)
        kill_camera_service(**kwargs)
        return camera(**kwargs)
    except Exception as e:
        err = str(e)
        if err.endswith('address already in use'):
            kwargs['port'] = 1876  # assume this port is available
            return camera(**kwargs)
        raise
    finally:
        application().restoreOverrideCursor()


def prompt_for_service_kwargs(config=None):
    """Prompt the user for the kwargs to send to :func:`ocr.service`.

    Parameters
    ----------
    config : :class:`dict`, optional
        If `config` is not specified then a dialog is displayed for the user
        to enter the information necessary to connect to the service. If
        only the ``rpi_password`` key is missing from `config` then the
        password will be asked for in a simple text prompt.

    Returns
    -------
    :class:`~ocr.service.RemoteOCR` or :data:`None`
        The connection to the :class:`~ocr.service.OCR` service on the Raspberry Pi
         or :data:`None` if the user chose to cancel the prompt.
    """
    kwargs = get_kwargs(config)
    if kwargs is None:
        return

    try:
        application().setOverrideCursor(Qt.WaitCursor)
        kill_ocr_service(**kwargs)
        return service(**kwargs)
    except Exception as e:
        err = str(e)
        if err.endswith('address already in use'):
            kwargs['port'] = 1876  # assume this port is available
            return service(**kwargs)
        raise
    finally:
        application().restoreOverrideCursor()
