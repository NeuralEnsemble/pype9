#!/bin/bash
# Adapted from similar install script in pyNN (https://github.com/NeuralEnsemble/PyNN)

set -e  # stop execution in case of errors

export NRN_VERSION="nrn-7.3"
if [ ! -f "$HOME/$NRN_VERSION/configure" ]; then
    wget http://www.neuron.yale.edu/ftp/neuron/versions/v7.3/$NRN_VERSION.tar.gz -O $HOME/$NRN_VERSION.tar.gz;
    pushd $HOME;
    tar xzf $NRN_VERSION.tar.gz;
    popd;
else
    echo 'Using cached version of NEURON sources.';
fi
mkdir -p $HOME/build/$NRN_VERSION
pushd $HOME/build/$NRN_VERSION
export VENV=`python -c "import sys; print sys.prefix"`;
if [ ! -f "$HOME/build/$NRN_VERSION/config.log" ]; then
    $HOME/$NRN_VERSION/configure --with-paranrn --with-nrnpython --prefix=$VENV --without-iv;
    make;
else
    echo 'Using cached NEURON build directory.';
fi
make install
cd src/nrnpython
python setup.py install

pip install nrnutils  # must be installed after NEURON

# Create links to required NEURON utilities
cd $VENV/bin;
ls -l;
ln -sf ../x86_64/bin/nrnivmodl;
ln -sf ../x86_64/bin/modlunit;

# compile PyNN NMODL mechanisms
cd $VENV/lib/python2.7/site-packages/pyNN/neuron/nmodl
nrnivmodl

popd
