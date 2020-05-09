#!/bin/bash

# install the rpi-ocr package in a virtual environment named 'ocrenv' which is
# located in /home/pi. If you change the name of the virtual environment
# then you must also change the value of RPI_EXE_PATH in ocr/__init__.py
ENV_NAME="ocrenv"

# install prerequisites
sudo apt install -y python3-dev python3-venv libffi-dev libssl-dev build-essential libimlib2 libimlib2-dev automake libtool libleptonica-dev make pkg-config libicu-dev libpango1.0-dev libcairo2-dev libatlas-base-dev libjasper-dev libqtgui4 libqt4-test

# install Qt5
sudo apt install -y qt5-default libqt5qml5 libpyside2-py3-5.11 libqt53dcore5 libqt53dinput5 libqt53dlogic5 libqt53drender5 libqt5charts5 libqt5location5 libqt5positioningquick5 libqt5positioning5 libqt5quick5 libqt5multimedia5 libqt5multimediawidgets5 libqt5quickwidgets5 libqt5script5 libqt5scripttools5 libqt5sensors5 libqt5texttospeech5 libqt5webchannel5 libqt5websockets5 libqt5x11extras5 libqt5xmlpatterns5

# build tesseract with training tools
cd ~
git clone https://github.com/tesseract-ocr/tesseract.git
cd tesseract/
./autogen.sh
./configure
make
sudo make install
sudo ldconfig
make training
sudo make training-install
echo -e "\nexport TESSDATA_PREFIX=/usr/local/share/" >> ~/.bashrc
export TESSDATA_PREFIX=/usr/local/share/
cd ~

# add trained data for tesseract
wget https://github.com/tesseract-ocr/tessdata/raw/master/eng.traineddata
wget https://github.com/arturaugusto/display_ocr/raw/master/letsgodigital/letsgodigital.traineddata
sudo mv *.traineddata $TESSDATA_PREFIX

# build ssocr
git clone https://github.com/auerswal/ssocr.git
cd ssocr/
sudo make install
cd ~

# check tesseract and ssocr installation
echo Testing tesseract installation... you should see 619121
tesseract rpi-ocr/tests/images/tesseract_numbers.jpg stdout
echo Testing ssocr installation... you should see 431432
ssocr -T rpi-ocr/tests/images/six_digits.png

# create virtual environment
python3 -m venv $ENV_NAME
source $ENV_NAME/bin/activate
pip install --upgrade pip
pip install --upgrade setuptools

# install PySide2 in the virtual environment
apt download python3-pyside2.qt3dcore python3-pyside2.qt3dinput python3-pyside2.qt3dlogic python3-pyside2.qt3drender python3-pyside2.qtcharts python3-pyside2.qtconcurrent python3-pyside2.qtcore python3-pyside2.qtgui python3-pyside2.qthelp python3-pyside2.qtlocation python3-pyside2.qtmultimedia python3-pyside2.qtmultimediawidgets python3-pyside2.qtnetwork python3-pyside2.qtopengl python3-pyside2.qtpositioning python3-pyside2.qtprintsupport python3-pyside2.qtqml python3-pyside2.qtquick python3-pyside2.qtquickwidgets python3-pyside2.qtscript python3-pyside2.qtscripttools python3-pyside2.qtsensors python3-pyside2.qtsql python3-pyside2.qtsvg python3-pyside2.qttest python3-pyside2.qttexttospeech python3-pyside2.qtuitools python3-pyside2.qtwebchannel python3-pyside2.qtwebsockets python3-pyside2.qtwidgets python3-pyside2.qtx11extras python3-pyside2.qtxml python3-pyside2.qtxmlpatterns python3-pyside2uic
for f in *.deb; do dpkg -x $f ./pyside2-tmp; done;
cp -r ./pyside2-tmp/usr/lib/python3/dist-packages/* ./$ENV_NAME/lib/python*/site-packages/

# install rpi-ocr
cd rpi-ocr
python setup.py install

# run the Python tests
pip install pytest
pytest

cd ~
deactivate

# cleanup
rm -rf tesseract/
rm -rf ssocr/
rm -rf pyside2-tmp/
rm *.deb
