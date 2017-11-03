FROM ubuntu:trusty
MAINTAINER tom.close@monash.edu

RUN apt-get -qq update
RUN apt-get install -y git build-essential autoconf automake libtool libreadline6-dev \
                       libncurses5-dev libgsl0-dev python-dev python3-dev python-numpy \
                       python-scipy python3-numpy python3-scipy openmpi-bin \
                       libopenmpi-dev inkscape libhdf5-serial-dev  openssh-server \
                       python-pip python3-pip openssh-client curl vim openssl \
                       libreadline6-dev curl zlib1g zlib1g-dev libssl-dev \
                       libyaml-dev libopenmpi-dev inkscape libhdf5-serial-dev \
                       cmake pkg-config

RUN wget http://www.cmake.org/files/v3.9/cmake-3.9.4.tar.gz
RUN tar xf cmake-3.9.4.tar.gz
WORKDIR cmake-3.9.4
RUN ./configure
RUN make
RUN make install

RUN pip install --upgrade pip
RUN pip install cython virtualenv ipython

RUN useradd -ms /bin/bash docker
RUN echo docker:docker | chpasswd
RUN adduser docker sudo
USER docker
ENV HOME=/home/docker
ENV SHELL=/bin/bash

WORKDIR $HOME
RUN git config --global user.email "tom.g.close@gmail.com"
RUN git config --global user.name "Tom Close"

RUN echo "Cloning Pype9 7"
RUN git clone -b python3 https://github.com/tclose/pype9.git

RUN virtualenv --python=python2 $HOME/py2
RUN virtualenv --python=python3 $HOME/py3
