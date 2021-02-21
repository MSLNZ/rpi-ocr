#!/bin/bash
#
# This script takes approximately 1 hour to complete and
# can use up to an additional 1 GB of disk space.
# Usage: source rpi-setup.sh
#

# install the rpi-ocr package in a virtual environment named 'ocrenv' which is
# located in /home/pi. If you change the name of the virtual environment
# then you must also change the value of RPI_EXE_PATH in ocr/__init__.py
ENV_NAME="ocrenv"

# prerequisites for cryptography
sudo apt-get install -y build-essential libssl-dev libffi-dev python3-dev

# prerequisites for opencv-python
sudo apt-get install -y libavutil56 libcairo-gobject2 libgtk-3-0 libqtgui4 libpango-1.0-0 libqtcore4 libavcodec58 libcairo2 libswscale5 libtiff5 libqt4-test libatk1.0-0 libavformat58 libgdk-pixbuf2.0-0 libilmbase23 libjasper1 libopenexr23 libpangocairo-1.0-0 libwebp6 libatlas-base-dev

cd ~

# build tesseract with training tools (only if tesseract is not already installed)
if ! [ -x "$(command -v tesseract)" ]; then
  # prerequisites for tesseract and the training tools
  sudo apt-get install -y g++ autoconf automake libtool pkg-config libpng-dev libjpeg-dev libtiff5-dev zlib1g-dev libleptonica-dev libicu-dev libpango1.0-dev libcairo2-dev
  git clone https://github.com/tesseract-ocr/tesseract.git
  cd tesseract/
  git checkout tags/5.0.0-alpha-20201231 -b 5.0.0-alpha-20201231
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
  # add trained models for tesseract to the tessdata directory
  wget https://raw.githubusercontent.com/tesseract-ocr/tessdata_best/master/eng.traineddata
  wget https://raw.githubusercontent.com/tesseract-ocr/tessdata_best/master/osd.traineddata
  wget https://raw.githubusercontent.com/Shreeshrii/tessdata_ssd/master/7seg.traineddata
  wget https://raw.githubusercontent.com/Shreeshrii/tessdata_ssd/master/ssd.traineddata
  wget https://raw.githubusercontent.com/Shreeshrii/tessdata_ssd/master/ssd_alphanum_plus.traineddata
  wget https://raw.githubusercontent.com/Shreeshrii/tessdata_ssd/master/ssd_int.traineddata
  wget https://raw.githubusercontent.com/Shreeshrii/tessdata_ssd/master/ssd_plus.traineddata
  wget https://raw.githubusercontent.com/arturaugusto/display_ocr/master/letsgodigital/letsgodigital.traineddata
  sudo mv *.traineddata $TESSDATA_PREFIX
  sudo cp -r ~/tesseract/tessdata $TESSDATA_PREFIX/..
  sudo cp ~/rpi-ocr/resources/tessdata/*.traineddata $TESSDATA_PREFIX
else
  echo "Tesseract-OCR is already installed"
  tesseract --version
fi

# build ssocr (only if ssocr is not already installed)
if ! [ -x "$(command -v ssocr)" ]; then
  # prerequisites for ssocr
  sudo apt-get install -y make build-essential libimlib2 libimlib2-dev
  git clone https://github.com/auerswal/ssocr.git
  cd ssocr/
  make
  sudo make install
  cd ..
else
  echo "ssocr is already installed"
  ssocr --version
fi

# create the virtual environment
sudo apt-get install -y python3-venv
python3 -m venv $ENV_NAME
source $ENV_NAME/bin/activate
python -m pip install --upgrade pip
python -m pip install --upgrade setuptools wheel

# install PySide2 and rpi-ocr
cd rpi-ocr
python -m pip install PySide2 --no-index --find-links resources/
python -m pip install .[tests]

# check tesseract and ssocr installation
echo
echo "Testing tesseract installation... you should see 619121"
tesseract ~/rpi-ocr/tests/images/tesseract_numbers.jpg stdout
echo "Testing ssocr installation... you should see 431432"
ssocr -T ~/rpi-ocr/tests/images/six_digits.png
echo

# run the rpi-ocr tests
export QT_QPA_PLATFORM="offscreen"
python -m pytest
unset QT_QPA_PLATFORM
deactivate

# cleanup
cd ~
rm -rf tesseract/
rm -rf ssocr/

echo
echo Runtime: $(date -d@${SECONDS} -u +%H:%M:%S) [HH:MM:SS]
