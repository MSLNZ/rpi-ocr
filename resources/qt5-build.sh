#!/bin/bash
#
# Build and install Qt5 from source.
#
# Runtime is about 4 hours on a Raspberry Pi 4 Model B Rev 1.2
# (4-GB RAM) using 4 jobs for the build.
#
# To install from the archive file run:
#   tar -xvf Qt*.tgz -C /
#
set -e

MAJOR=5
MINOR=15
MICRO=2

JOBS=4

VERSION=${MAJOR}.${MINOR}.${MICRO}

SRC_DIR=~/qt${MAJOR}-src

BUILD_DIR=${SRC_DIR}/build

PREFIX=/usr/local/Qt-${VERSION}

ARCHIVE=~/Qt-${VERSION}-$(dpkg --print-architecture).tgz

BUILD_REQUIREMENTS=(
  autotools-dev bison bluez build-essential default-libmysqlclient-dev dpkg-dev ffmpeg firebird-dev
  flex freetds-dev gperf gstreamer1.0-alsa gstreamer1.0-libav gstreamer1.0-omx gstreamer1.0-omx-rpi
  gstreamer1.0-omx-rpi-config gstreamer1.0-plugins-bad gstreamer1.0-plugins-base gstreamer1.0-plugins-good
  gstreamer1.0-x icu-devtools libasound2-dev libassimp-dev libatk-bridge2.0-dev libatk1.0-dev
  libatspi2.0-dev libaudit-dev libavcodec-dev libavformat-dev libbison-dev libbluetooth-dev libbsd-dev
  libc-dev-bin libc6-dev libcairo2-dev libcap-ng-dev libclang-dev libcups2-dev libcupsimage2-dev
  libdbus-1-dev libdevmapper-dev libdmx-dev libdouble-conversion-dev libdrm-dev libegl1-mesa-dev
  libepoxy-dev libexpat1-dev libfontconfig1-dev libfontenc-dev libfreetype6-dev libgbm-dev libgcc-6-dev
  libgcrypt20-dev libgdk-pixbuf2.0-dev libgl1-mesa-dev libgles2-mesa-dev libglib2.0-dev libglu1-mesa-dev
  libgmp-dev libgpg-error-dev libgraphite2-dev libgstreamer-plugins-bad1.0-0 libgstreamer-plugins-base1.0-0
  libgstreamer-plugins-base1.0-dev libgstreamer1.0 libgstreamer1.0-0 libgstreamer1.0-dev libgtk-3-dev
  libharfbuzz-dev libhunspell-dev libice-dev libicu-dev libinput-dev libjbig-dev libjpeg-dev
  libjpeg62-turbo-dev libltdl-dev liblzma-dev libmariadbclient-dev libmariadb-dev-compat libmnl-dev
  libmtdev-dev libncurses5 libncurses5-dev libncursesw5-dev libpango1.0-dev libpciaccess-dev libpcre3-dev
  libpipeline-dev libpixman-1-dev libpng-dev libpq-dev libproxy-dev libpthread-stubs0-dev libpulse-dev
  libpython-all-dev libpython-dev libpython2.7-dev libpython3-dev libpython3.7-dev libraspberrypi-dev
  librtimulib-dev libselinux1-dev libsepol1-dev libsgutils2-dev libsm-dev libsqlite3-dev libssl1.0-dev
  libstdc++-6-dev libswscale-dev libsystemd-dev libtiff5-dev libudev-dev libwayland-dev libx11-dev
  libx11-xcb-dev libx11-xcb1 libxau-dev libxaw7-dev libxcb-dri2-0-dev libxcb-dri3-dev libxcb-glx0-dev
  libxcb-icccm4 libxcb-icccm4-dev libxcb-image0 libxcb-image0-dev libxcb-keysyms1 libxcb-keysyms1-dev
  libxcb-present-dev libxcb-randr0-dev libxcb-render-util0 libxcb-render-util0-dev libxcb-render0-dev
  libxcb-shape0-dev libxcb-shm0 libxcb-shm0-dev libxcb-sync-dev libxcb-sync1 libxcb-util0-dev
  libxcb-xf86dri0-dev libxcb-xfixes0-dev libxcb-xinerama0 libxcb-xinerama0-dev libxcb-xkb-dev
  libxcb-xv0-dev libxcb1 libxcb1-dev libxcomposite-dev libxcursor-dev libxdamage-dev libxdmcp-dev
  libxext-dev libxfixes-dev libxfont-dev libxft-dev libxi-dev libxinerama-dev libxkbcommon-dev
  libxkbcommon-x11-dev libxkbfile-dev libxml2-dev libxmu-dev libxmuu-dev libxpm-dev libxrandr-dev
  libxrender-dev libxres-dev libxshmfence-dev libxt-dev libxtst-dev libxv-dev libxxf86vm-dev
  linux-libc-dev make manpages-dev mesa-common-dev nettle-dev python-all-dev python-dev python-smbus
  python2.7-dev python3-dev python3-smbus python3.7-dev ruby unixodbc-dev wget x11proto-bigreqs-dev
  x11proto-composite-dev x11proto-core-dev x11proto-damage-dev x11proto-dmx-dev x11proto-dri2-dev
  x11proto-dri3-dev x11proto-fixes-dev x11proto-fonts-dev x11proto-gl-dev x11proto-input-dev
  x11proto-kb-dev x11proto-present-dev x11proto-randr-dev x11proto-record-dev x11proto-render-dev
  x11proto-resource-dev x11proto-scrnsaver-dev x11proto-video-dev x11proto-xcmisc-dev x11proto-xext-dev
  x11proto-xf86bigfont-dev x11proto-xf86dga-dev x11proto-xf86dri-dev x11proto-xf86vidmode-dev
  x11proto-xinerama-dev xtrans-dev xutils-dev zlib1g-dev
)
sudo apt-get install -y ${BUILD_REQUIREMENTS[@]}

# Download and extract the source code (if necessary)
if [ ! -d "${SRC_DIR}" ]; then
  wget --continue https://download.qt.io/official_releases/qt/${MAJOR}.${MINOR}/${VERSION}/single/qt-everywhere-src-${VERSION}.tar.xz
  tar -xvf qt-everywhere-src-${VERSION}.tar.xz
  mv qt-everywhere-src-${VERSION} ${SRC_DIR}
fi

# Remove previous build
rm -rf ${BUILD_DIR}
mkdir ${BUILD_DIR}
cd ${BUILD_DIR}

# Configure, build and install
../configure -opensource -confirm-license -release -nomake examples -nomake tests -skip qtwebengine -prefix ${PREFIX}
make -j${JOBS}
sudo make install

# Create an archive of the installation
tar -cvzf ${ARCHIVE} ${PREFIX}

echo
echo Installed:
${PREFIX}/bin/qmake -v
echo Created: ${ARCHIVE}
echo Runtime: $(date -d@${SECONDS} -u +%H:%M:%S) [HH:MM:SS]
