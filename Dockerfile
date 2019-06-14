FROM buildpack-deps:bionic as builderslim216
MAINTAINER "Steffen Graber" <s.graber@fz-juelich.de>

ENV TERM=xterm \
    TZ=Europe/Berlin \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    cython3 \
    libgsl0-dev \
    libltdl-dev \
    libncurses5-dev \
    libreadline6-dev \
    python3.6-dev \
    python3-numpy \
    python3-scipy \
    python3-matplotlib \
    python3-ipython \
    python3-nose \
    wget

RUN wget https://github.com/nest/nest-simulator/archive/v2.16.0.tar.gz && \
  mkdir nest-build && \
  tar zxf v2.16.0.tar.gz && \
  cd  nest-build && \
  cmake -DCMAKE_INSTALL_PREFIX:PATH=/opt/nest/ \
        -Dwith-python=3 \
        ../nest-simulator-2.16.0 && \
  make && \
  make install
  make installcheck

