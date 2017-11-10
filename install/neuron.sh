#!/bin/bash

set -e  # stop execution in case of errors

if [ -z "$1" ]; then
    echo "Neuron install script:"
    echo "  Usage: VERSION [PYTHON_VERSION INSTALL_PREFIX BUILD_DIR]"
    echo ""
    echo "ERROR! Please provide Neuron version as first argument to install script"
    exit
fi

VERSION=$1
NEURON=nrn-$VERSION

if [ -z "$2" ]; then
    PYTHON_VERSION=$(python -c "import sysconfig; print(sysconfig.get_config_var('py_version').split('.')[0])");
else
    PYTHON_VERSION=$2
fi
echo "Using Python $PYTHON_VERSION in Neuron build"

PYTHON=python$PYTHON_VERSION
PYTHON_PATH=$(which $PYTHON)

if [ -z "$3" ]; then
    # Use virtualenv bin by default
    INSTALL_PREFIX=$($PYTHON -c "import sys; print(sys.prefix)");
    echo "prefix: $INSTALL_PREFIX"
    if [ $INSTALL_PREFIX == '/usr' ] || [ $INSTALL_PREFIX == '/usr/local' ]; then
        INSTALL_PREFIX=$HOME/neuron
    fi
else
    INSTALL_PREFIX=$3
fi
echo "Installing Neuron to '$INSTALL_PREFIX'"

if [ -z "$4" ]; then
    BASE_DIR=$HOME/.pype9/prereq-build/$NEURON
    rm -rf $BASE_DIR
else
    BASE_DIR=$4
fi
echo "Using '$BASE_DIR' as Neuron base build directory"
mkdir -p $BASE_DIR

SRC_DIR=$BASE_DIR/$NEURON
BUILD_DIR=$BASE_DIR/$NEURON-build

if [ "${VERSION%%-*}" == 'sha' ]; then
    # Download and untar
    echo ${VERSION##sha-}
    wget –-quiet http://github.com/nrnhines/nrn/archive/${VERSION##sha-}.zip -O $BASE_DIR/$NEURON.zip;
    pushd $BASE_DIR;
    unzip $NEURON.zip;
    rm $NEURON.zip;
    mv nrn* $NEURON;
    pushd $NEURON;
    ./build.sh;  # run libtoolize
    popd;
    popd;
else
    # Download and untar
    wget --quiet http://www.neuron.yale.edu/ftp/neuron/versions/v$VERSION/$NEURON.tar.gz -O $BASE_DIR/$NEURON.tar.gz;
    pushd $BASE_DIR;
    tar xzf $NEURON.tar.gz;
    popd;
fi

mkdir -p $BUILD_DIR
pushd $BUILD_DIR

# Configure, make and install
echo "Install Prefix: $INSTALL_PREFIX"
CONFIG_CMD="$SRC_DIR/configure --with-paranrn --with-nrnpython=$PYTHON_PATH --prefix=$INSTALL_PREFIX --disable-rx3d --without-iv";
echo $CONFIG_CMD
$CONFIG_CMD
make -j8;

# Add setup.cfg with empty prefix
SETUP_CFG=$BUILD_DIR/src/nrnpython/setup.cfg
echo "[install]" > $SETUP_CFG
echo "prefix=" >> $SETUP_CFG

# Now can install
make install

rm $SETUP_CFG

# Install Python
cd src/nrnpython
$PYTHON setup.py install
pip install nrnutils  # must be installed after NEURON

# Create links to required NEURON utilities
cd $INSTALL_PREFIX/bin;
ls -l;
ln -sf ../x86_64/bin/nrnivmodl;
ln -sf ../x86_64/bin/modlunit;
popd


# Test installation
$PYTHON -c "import neuron; neuron.h.Section();"

