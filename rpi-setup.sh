#!/bin/bash

# This script takes approximately 1 hour to complete and
# can use up to an additional 1 GB of hard drive space.

# install the rpi-ocr package in a virtual environment named 'ocrenv' which is
# located in /home/pi. If you change the name of the virtual environment
# then you must also change the value of RPI_EXE_PATH in ocr/__init__.py
ENV_NAME="ocrenv"

# prerequisites for cryptography
sudo apt install -y build-essential libssl-dev libffi-dev python3-dev

# prerequisites for tesseract and the training tools
sudo apt install -y g++ autoconf automake libtool pkg-config libpng-dev libjpeg-dev libtiff5-dev zlib1g-dev libleptonica-dev libicu-dev libpango1.0-dev libcairo2-dev

# prerequisites for ssocr
sudo apt install -y make build-essential libimlib2 libimlib2-dev

# prerequisites for opencv-python
sudo apt install -y libavutil56 libcairo-gobject2 libgtk-3-0 libqtgui4 libpango-1.0-0 libqtcore4 libavcodec58 libcairo2 libswscale5 libtiff5 libqt4-test libatk1.0-0 libavformat58 libgdk-pixbuf2.0-0 libilmbase23 libjasper1 libopenexr23 libpangocairo-1.0-0 libwebp6 libatlas-base-dev

# install Qt5
sudo apt install -y qt5-default libqt5qml5 libpyside2-py3-5.11 libqt53dcore5 libqt53dinput5 libqt53dlogic5 libqt53drender5 libqt5charts5 libqt5location5 libqt5positioningquick5 libqt5positioning5 libqt5quick5 libqt5multimedia5 libqt5multimediawidgets5 libqt5quickwidgets5 libqt5script5 libqt5scripttools5 libqt5sensors5 libqt5texttospeech5 libqt5webchannel5 libqt5websockets5 libqt5x11extras5 libqt5xmlpatterns5

cd ~

# build tesseract with training tools (only if tesseract is not already installed)
if ! [ -x "$(command -v tesseract)" ]; then
  git clone https://github.com/tesseract-ocr/tesseract.git
  cd tesseract/
  ./autogen.sh
  ./configure
  make
  sudo make install
  sudo ldconfig
  make training
  sudo make training-install
  export TESSDATA_PREFIX=/usr/local/share/tessdata
  echo -e "\n# Used by tesseract-ocr\nexport TESSDATA_PREFIX="$TESSDATA_PREFIX >> ~/.bashrc
  cd ..
else
  echo "Tesseract-OCR is already installed"
  tesseract --version
fi

# add trained models for tesseract to the tessdata directory
wget https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/master/eng.traineddata
wget https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/master/osd.traineddata
sudo mv *.traineddata $TESSDATA_PREFIX
sudo cp -r ~/tesseract/tessdata $TESSDATA_PREFIX
sudo cp ~/rpi-ocr/resources/tessdata/*.traineddata $TESSDATA_PREFIX

# build ssocr (only if ssocr is not already installed)
if ! [ -x "$(command -v ssocr)" ]; then
  git clone https://github.com/auerswal/ssocr.git
  cd ssocr/
  sudo make install
  cd ..
else
  echo "ssocr is already installed"
  ssocr --version
fi

# create the virtual environment
sudo apt install -y python3-venv
python3 -m venv $ENV_NAME
source $ENV_NAME/bin/activate
pip install --upgrade pip
pip install --upgrade setuptools wheel

# install PySide2 in the virtual environment
mkdir pyside2-deb-tmp
cd pyside2-deb-tmp
apt download python3-pyside2.qt3dcore python3-pyside2.qt3dinput python3-pyside2.qt3dlogic python3-pyside2.qt3drender python3-pyside2.qtcharts python3-pyside2.qtconcurrent python3-pyside2.qtcore python3-pyside2.qtgui python3-pyside2.qthelp python3-pyside2.qtlocation python3-pyside2.qtmultimedia python3-pyside2.qtmultimediawidgets python3-pyside2.qtnetwork python3-pyside2.qtopengl python3-pyside2.qtpositioning python3-pyside2.qtprintsupport python3-pyside2.qtqml python3-pyside2.qtquick python3-pyside2.qtquickwidgets python3-pyside2.qtscript python3-pyside2.qtscripttools python3-pyside2.qtsensors python3-pyside2.qtsql python3-pyside2.qtsvg python3-pyside2.qttest python3-pyside2.qttexttospeech python3-pyside2.qtuitools python3-pyside2.qtwebchannel python3-pyside2.qtwebsockets python3-pyside2.qtwidgets python3-pyside2.qtx11extras python3-pyside2.qtxml python3-pyside2.qtxmlpatterns python3-pyside2uic
for f in *.deb; do dpkg -x $f ./pyside2; done;
cp -r ./pyside2/usr/lib/python3/dist-packages/* ~/$ENV_NAME/lib/python*/site-packages/
cd ~

# install rpi-ocr
cd rpi-ocr
pip install .

# check tesseract and ssocr installation
echo Testing tesseract installation... you should see 619121
tesseract ~/rpi-ocr/tests/images/tesseract_numbers.jpg stdout
echo Testing ssocr installation... you should see 431432
ssocr -T ~/rpi-ocr/tests/images/six_digits.png

# run the rpi-ocr tests
pip install pytest pytest-cov
pytest

# cleanup
cd ~
rm -rf tesseract/
rm -rf ssocr/
rm -rf pyside2-deb-tmp/
