#!/bin/bash
# Adapted from similar install script in pyNN (https://github.com/NeuralEnsemble/PyNN)

set -e  # stop execution in case of errors

if [ -z "$1" ]; then
    echo "Please provide Neuron version to install script"
    return
fi

NEURON_VERSION=$1
NEURON=nrn-$NEURON_VERSION

if [ -z "$2" ]; then
    export NEURON_INSTALL_PREFIX=$2
else
    # Use virtualenv bin by default
    export NEURON_INSTALL_PREFIX=$(python -c "import sys; print(sys.prefix)");
fi

if [ -z "$3" ]; then
    export NEURON_BUILD_DIR=$3
else
    export NEURON_BUILD_DIR=$HOME/pype9-build/neuron
fi
echo "Using '$NEURON_BUILD_DIR' as NEURON build directory"
mkdir -p $NEURON_BUILD_DIR

SRC_DIR=$NEURON_BUILD_DIR/$NEURON
BUILD_DIR=$NEURON_BUILD_DIR/build

export NEURON_BUILD_DIR=$HOME/build/$NEURON

wget http://www.neuron.yale.edu/ftp/neuron/versions/v$NEURON_VERSION/$NEURON.tar.gz -O $NEURON_BUILD_DIR/$NEURON.tar.gz;
pushd $NEURON_BUILD_DIR;
tar xzf $NEURON.tar.gz;
popd;

mkdir -p $NEURON_BUILD_DIR
pushd $NEURON_BUILD_DIR

PYTHON_PREFIX=`python -c "import sys; print(sys.prefix)"`;

$NEURON_SRC_DIR/configure --with-paranrn --with-nrnpython=$PYTHON_PREFIX/bin/python \
 --prefix=$NEURON_INSTALL_PREFIX --disable-rx3d --without-iv;
make;
make install

# Install Python
cd src/nrnpython
python setup.py install
pip install nrnutils  # must be installed after NEURON

# Create links to required NEURON utilities
cd $NEURON_INSTALL_PREFIX/bin;
ls -l;
ln -sf ../x86_64/bin/nrnivmodl;
ln -sf ../x86_64/bin/modlunit;
popd
