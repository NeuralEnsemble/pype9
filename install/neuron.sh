#!/bin/bash

set -e  # stop execution in case of errors

if [ -z "$1" ]; then
    echo "Neuron install script:"
    echo "  Usage: VERSION [INSTALL_PREFIX BUILD_DIR]"
    echo ""
    echo "ERROR! Please provide Neuron version as first argument to install script"
    exit
fi

NEURON_VERSION=$1
NEURON=nrn-$NEURON_VERSION

if [ -z "$2" ]; then
    PYTHON_VERSION=$(python -c "import sysconfig; print(sysconfig.get_config_var('py_version').split('.')[0])");
else
    PYTHON_VERSION=$2
fi
echo "Using Python $PYTHON_VERSION"

PYTHON=python$PYTHON_VERSION
PYTHON_PATH=$(which $PYTHON)

if [ -z "$3" ]; then
    # Use virtualenv bin by default
    export NEURON_INSTALL_PREFIX=$($PYTHON -c "import sys; print(sys.prefix)");
    echo "prefix: $NEURON_INSTALL_PREFIX"
    if [ $NEURON_INSTALL_PREFIX == '/usr' ] || [ $NEURON_INSTALL_PREFIX == '/usr/local' ]; then
        export NEURON_INSTALL_PREFIX=$HOME/neuron
    fi
else
    export NEURON_INSTALL_PREFIX=$3
fi
echo "Installing Neuron to '$NEURON_INSTALL_PREFIX'"

if [ -z "$4" ]; then
    export NEURON_BUILD_DIR=$HOME/pype9-build/neuron
    rm -rf $NEURON_BUILD_DIR
else
    export NEURON_BUILD_DIR=$4
fi
echo "Using '$NEURON_BUILD_DIR' as NEURON build directory"
mkdir -p $NEURON_BUILD_DIR

SRC_DIR=$NEURON_BUILD_DIR/$NEURON
BUILD_DIR=$NEURON_BUILD_DIR/$NEURON-build

if [ "${NEURON_VERSION%%-*}" == 'sha' ]; then
    # Download and untar
    echo ${NEURON_VERSION##sha-}
    wget http://github.com/nrnhines/nrn/archive/${NEURON_VERSION##sha-}.zip -O $NEURON_BUILD_DIR/$NEURON.zip;
    pushd $NEURON_BUILD_DIR;
    unzip $NEURON.zip;
    rm $NEURON.zip;
    mv nrn* $NEURON;
    pushd $NEURON;
    ./build.sh;  # run libtoolize
    popd;
    popd;
else
    # Download and untar
    wget http://www.neuron.yale.edu/ftp/neuron/versions/v$NEURON_VERSION/$NEURON.tar.gz -O $NEURON_BUILD_DIR/$NEURON.tar.gz;
    pushd $NEURON_BUILD_DIR;
    tar xzf $NEURON.tar.gz;
    popd;
fi

mkdir -p $NEURON_BUILD_DIR
pushd $NEURON_BUILD_DIR

# Configure, make and install
echo "Install Prefix: $NEURON_INSTALL_PREFIX"
CONFIG_CMD="$SRC_DIR/configure --with-paranrn --with-nrnpython=$PYTHON_PATH --prefix=$NEURON_INSTALL_PREFIX --disable-rx3d --without-iv)";
echo $CONFIG_CMD
$CONFIG_CMD
make -j8;
make install

# Install Python
cd src/nrnpython
$PYTHON setup.py install
pip install nrnutils  # must be installed after NEURON

# Create links to required NEURON utilities
cd $NEURON_INSTALL_PREFIX/bin;
ls -l;
ln -sf ../x86_64/bin/nrnivmodl;
ln -sf ../x86_64/bin/modlunit;
popd
