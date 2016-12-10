FROM neuralensemble/base:py2
MAINTAINER tom.close@monash.edu

ENV NRN_VER=7.4
ENV NRN=nrn-$NRN_VER

WORKDIR /home/docker/packages
RUN wget http://www.neuron.yale.edu/ftp/neuron/versions/v$NRN_VER/$NRN.tar.gz
RUN tar xzf $NRN.tar.gz; rm $NRN.tar.gz

RUN mkdir $VENV/build
WORKDIR $VENV/build
RUN mkdir $NRN; \
    cd $NRN; \
    $HOME/packages/$NRN/configure --with-nrnpython=$VENV/bin/python --disable-rx3d --without-iv --prefix=$VENV; \
    make; make install; \
    cd src/nrnpython; $VENV/bin/python setup.py install; \
    cd $VENV/bin; ln -s ../x86_64/bin/nrnivmodl

RUN PATH=$PATH:$VENV/bin $VENV/bin/pip install lazyarray brian nrnutils PyNN

WORKDIR /home/docker/
RUN echo "source $VENV/bin/activate" >> .bashrc
