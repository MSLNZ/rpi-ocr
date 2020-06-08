.. _rpi-ocr-install:

===============
Install RPi-OCR
===============

Raspbian
--------
To set up the Raspberry Pi run the following commands. Instructions for using SSH_
to remotely access the terminal of the Raspberry Pi can be found `here <ssh_instructions_>`_.

The following commands are optional *(but recommended)*. They will update the
installed packages on the Raspberry Pi.

Open a terminal and run

.. code-block:: console

   sudo apt update
   sudo apt upgrade

Make sure that you have git_ installed and then clone the repository

.. code-block:: console

   sudo apt install git
   git clone --depth 1 https://github.com/MSLNZ/rpi-ocr

The following will install the **RPi-OCR** package in a `virtual environment`_ in the
``/home/pi/ocrenv`` directory *(the* ``ocrenv`` *directory will be created automatically)*.
Running the following command can take approximately 1 hour and can use up to an
additional 1 GB of disk space.

.. code-block:: console

   source rpi-ocr/rpi-setup.sh

If you want to acquire images with the Raspberry Pi then you must have a desktop version
of Raspbian_ installed (not the Lite version), you will need to attach a camera and
enable the camera in the configuration settings.

There are various camera options available, such as,

* `High Quality Camera <https://www.raspberrypi.org/products/raspberry-pi-high-quality-camera/>`_
* `Camera Module V2 <https://www.raspberrypi.org/products/camera-module-v2/>`_
* `Pi NoIR Camera V2 <https://www.raspberrypi.org/products/pi-noir-camera-v2/>`_

and make sure that the camera is enabled in the configuration settings

1. Open a terminal and run the following command

   .. code-block:: console

       sudo raspi-config

2. Select ``5 Interfacing Options``.

3. Select the ``P1 Camera`` peripheral.

4. Select ``Yes`` to enable the camera interface.

5. Select ``Ok``.

6. Select ``Finish`` to leave the configuration menu.

7. Select ``Yes`` to reboot.

If you want to establish a remote desktop session with the Raspberry Pi, you
must first install the `xrdp <http://xrdp.org/>`_ program

.. code-block:: console

   sudo apt install xrdp

and then reboot the Raspberry Pi.

Windows, Linux or macOS
-----------------------
To install **RPi-OCR** on a computer that is not a Raspberry Pi run

.. code-block:: console

   pip install https://github.com/MSLNZ/rpi-ocr/archive/master.tar.gz

Alternatively, using the :ref:`msl-package-manager-welcome` run

.. code-block:: console

   msl install rpi-ocr

Dependencies
------------
Tested with a Raspberry Pi 3 Model B+ and a Raspberry Pi 4 Model B
running either Raspbian Stretch or Buster.

* Python 3.5+
* :ref:`msl-network-welcome`
* :ref:`msl-qt-welcome`
* pillow_
* opencv-python_
* pyqtgraph_
* pytesseract_
* `Qt for Python`_
* picamera_ -- only required on the Raspberry Pi

The following programs are automatically installed on the Raspberry Pi by
running the ``rpi-setup.sh`` script. If you want to perform OCR on a computer
running Windows, Linux or macOS then follow the instructions below.

* Tesseract-OCR_ -- You can also use the trained models in the tessdata_ directory.
* ssocr_ -- An executable that runs on Windows (without Cygwin_) can be found at ssocr-win64_

.. _virtual environment: https://docs.python.org/3/tutorial/venv.html
.. _SSH: https://www.ssh.com/ssh/
.. _ssh_instructions: https://www.raspberrypi.org/documentation/remote-access/ssh/
.. _git: https://git-scm.com/
.. _pillow: https://pillow.readthedocs.io/en/stable/
.. _opencv-python: https://opencv-python-tutroals.readthedocs.io/en/latest/py_tutorials/py_tutorials.html
.. _pyqtgraph: https://pyqtgraph.readthedocs.io/en/latest/
.. _pytesseract: https://pytesseract.readthedocs.io/en/latest/
.. _Qt for Python: https://doc.qt.io/qtforpython/
.. _picamera: https://picamera.readthedocs.io/en/latest/
.. _Tesseract-OCR: https://tesseract-ocr.github.io/tessdoc/Home.html
.. _tessdata: https://github.com/MSLNZ/rpi-ocr/tree/master/resources/tessdata
.. _ssocr: https://www.unix-ag.uni-kl.de/~auerswal/ssocr/
.. _Cygwin: https://www.cygwin.com/
.. _ssocr-win64: https://github.com/MSLNZ/rpi-ocr/tree/master/resources/ssocr-win64
.. _Raspbian: https://www.raspberrypi.org/downloads/raspbian/
