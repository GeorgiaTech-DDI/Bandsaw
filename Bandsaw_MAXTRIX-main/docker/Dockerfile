FROM python:3.11-bookworm

# Install picamera dependencies
RUN apt-get update && apt-get install -y libcap-dev

# Build and install libcamera
RUN  apt install -y libboost-dev libgnutls28-dev openssl \
    libtiff-dev pybind11-dev qtbase5-dev libqt5core5a \
    libqt5widgets5 meson cmake \
    libglib2.0-dev libgstreamer-plugins-base1.0-dev
RUN pip install -U Jinja2 PyYAML ply

WORKDIR /dependencies
RUN git clone https://github.com/raspberrypi/libcamera.git
WORKDIR /dependencies/libcamera
RUN meson setup build --buildtype=release -Dgstreamer=enabled -Dpycamera=enabled
RUN ninja -C build install
