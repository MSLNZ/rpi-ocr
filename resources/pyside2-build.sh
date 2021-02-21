#!/bin/bash
#
# Build a stand-alone wheel of PySide2 and shiboken2.
#
# Runtime is about 1.5 hours on a Raspberry Pi 4 Model B Rev 1.2
# (4-GB RAM) using 4 parallel jobs for the build.
#
# To install PySide2 run:
#
#  cd path/to/wheels
#  pip3 install PySide2 --no-index --find-links .
#
set -e

# The PySide2 version should match the Qt5 version that is installed
VERSION=5.15.2

PARALLEL=4

SRC_DIR=~/pyside2-src

QMAKE=/usr/local/Qt-${VERSION}/bin/qmake

CMAKE=/usr/bin/cmake

# Install prerequisites
sudo apt-get install -y wget cmake python3-pip libclang-7-dev libxml2-dev libxslt1-dev mesa-common-dev libpulse-mainloop-glib0 libdouble-conversion1 libharfbuzz0b
python3 -m pip install -U setuptools wheel packaging

# Download and extract the source code (if necessary)
if [ ! -d "${SRC_DIR}" ]; then
  wget --continue https://download.qt.io/official_releases/QtForPython/pyside2/PySide2-${VERSION}-src/pyside-setup-opensource-src-${VERSION}.tar.xz
  tar -xvf pyside-setup-opensource-src-${VERSION}.tar.xz
  mv pyside-setup-opensource-src-${VERSION} ${SRC_DIR}
fi

# Change the name of the dynamic linker from "ld-linux.so.2" to "ld-linux.so.3"
sed -i 's/ld-linux.so.2/ld-linux.so.3/g' ${SRC_DIR}/build_scripts/utils.py

# Add the directory where the Clang libraries are located
export LLVM_INSTALL_DIR=/usr/lib/llvm-7

# Build the wheel with the Qt5 library included and use the CPython Stable ABI
cd ${SRC_DIR}
python3 setup.py bdist_wheel \
  --qmake=${QMAKE} \
  --cmake=${CMAKE} \
  --parallel=${PARALLEL} \
  --py-limited-api cp35.cp36.cp37.cp38.cp39 \
  --limited-api yes \
  --ignore-git \
  --standalone

# Move the wheels to the HOME directory
mv ${SRC_DIR}/dist/*.whl ~

echo
echo Created:
ls -1 ~/*.whl
echo Runtime: $(date -d@${SECONDS} -u +%H:%M:%S) [HH:MM:SS]
