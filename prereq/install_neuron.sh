#!/bin/bash
# Adapted from similar install script in pyNN (https://github.com/NeuralEnsemble/PyNN)

set -e  # stop execution in case of errors

export NRN_VERSION="7.4"
export NRN=nrn-$NRN_VERSION
if [ ! -f "$HOME/$NRN/configure" ]; then
    wget http://www.neuron.yale.edu/ftp/neuron/versions/v$NRN_VERSION/$NRN.tar.gz -O $HOME/$NRN.tar.gz;
    pushd $HOME;
    tar xzf nrn-$NRN_VERSION.tar.gz;
    popd;
else
    echo 'Using cached version of NEURON sources.';
fi
mkdir -p $HOME/build/$NRN
pushd $HOME/build/$NRN
export VENV=`python -c "import sys; print sys.prefix"`;
rm $HOME/build/$NRN/config.log
if [ ! -f "$HOME/build/$NRN/config.log" ]; then
    $HOME/$NRN/configure --with-paranrn --with-nrnpython --prefix=$VENV --disable-rx3d --without-iv;
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
popd
