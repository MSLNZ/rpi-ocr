#!/bin/bash

# install prerequisites
sudo apt install python3-venv libffi-dev libssl-dev build-essential libimlib2 libimlib2-dev automake libtool libleptonica-dev make pkg-config libicu-dev libpango1.0-dev libcairo2-dev libatlas-base-dev -y

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

# test tesseract and ssocr installation
wget https://files.realpython.com/media/sample2.36f8074c5273.jpg
wget https://www.unix-ag.uni-kl.de/~auerswal/ssocr/six_digits.png
echo Testing tesseract installation... you should see 619121
tesseract sample2.36f8074c5273.jpg out && more out.txt
echo Testing ssocr installation... you should see 431432
ssocr -T six_digits.png

# delete the files that are no longer required
rm -rf tesseract/
rm -rf ssocr/
rm six_digits.png
rm sample2.36f8074c5273.jpg
rm out.txt

# create a python virtual environment and install rpi-ocr
python3 -m venv ocrenv
source ocrenv/bin/activate
pip install --upgrade pip
pip install --upgrade setuptools
pip install https://github.com/MSLNZ/rpi-ocr/archive/master.tar.gz
deactivate
