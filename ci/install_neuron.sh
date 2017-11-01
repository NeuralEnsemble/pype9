#!/bin/bash
# Adapted from similar install script in pyNN (https://github.com/NeuralEnsemble/PyNN)

set -e  # stop execution in case of errors

if [ -z "$1" ]; then
	echo "Please provide Neuron version to install script"
	return
fi

NRN_VERSION=$1
NRN=nrn-$NRN_VERSION
export NEURON_SRC_DIR=$HOME/$NRN
export NEURON_BUILD_DIR=$HOME/build/$NRN

if [ "$2" == 'purge' ]; then
	# Remove cache because it is causing errors until the previous build runs successfully
	rm -rf $NEURON_SRC_DIR
	rm -rf $NEURON_BUILD_DIR
fi

if [ ! -f "$NEURON_SRC_DIR/configure" ]; then
    wget http://www.neuron.yale.edu/ftp/neuron/versions/v$NRN_VERSION/$NRN.tar.gz -O $HOME/$NRN.tar.gz;
    pushd $HOME;
    tar xzf nrn-$NRN_VERSION.tar.gz;
    popd;
else
    echo 'Using cached version of NEURON sources.';
fi

mkdir -p $NEURON_BUILD_DIR
pushd $NEURON_BUILD_DIR
export VENV=`python -c "import sys; print(sys.prefix)"`;

if [ ! -f "$NEURON_BUILD_DIR/config.log" ]; then
    $NEURON_SRC_DIR/configure --with-paranrn --with-nrnpython=$VENV/bin/python \
     --prefix=$VENV --disable-rx3d --without-iv;
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
