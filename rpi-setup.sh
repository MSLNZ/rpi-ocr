#!/bin/bash

# install prerequisites
sudo apt install python3-venv libffi-dev libssl-dev build-essential libimlib2 libimlib2-dev automake libtool libleptonica-dev make pkg-config libicu-dev libpango1.0-dev libcairo2-dev libatlas-base-dev libjasper-dev libqtgui4 libqt4-test -y

# build tesseract with training tools
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
cd ..

# add trained data for tesseract
wget https://github.com/tesseract-ocr/tessdata/raw/master/eng.traineddata
wget https://github.com/arturaugusto/display_ocr/raw/master/letsgodigital/letsgodigital.traineddata
sudo mv *.traineddata $TESSDATA_PREFIX

# build ssocr
git clone https://github.com/auerswal/ssocr.git
cd ssocr/
sudo make install
cd ..

# install the rpi-ocr package in a virtual environment named 'ocrenv'
# which is located in the home directory. If you change the name of the
# virtual environment then you must also change the value of RPI_EXE_PATH
# in ocr/__init__.py
python3 -m venv ocrenv
source ocrenv/bin/activate
pip install --upgrade pip
pip install --upgrade setuptools
pip install https://github.com/MSLNZ/rpi-ocr/archive/master.tar.gz
deactivate

# test tesseract and ssocr installation
echo Testing tesseract installation... you should see 619121
tesseract rpi-ocr/tests/images/tesseract_numbers.jpg stdout
echo Testing ssocr installation... you should see 431432
ssocr -T rpi-ocr/tests/images/six_digits.png

# cleanup
rm -rf tesseract/
rm -rf ssocr/
