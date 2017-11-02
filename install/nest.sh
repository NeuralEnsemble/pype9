#!/bin/bash

set -e  # stop execution in case of errors

if [ -z "$1" ]; then
    echo "Please provide NEST version as first argument to install script"
    exit
fi

NEST_VERSION=$1
NEST="nest-$NEST_VERSION"

if [ -z "$2" ]; then
    # Use virtualenv bin by default
    export NEST_INSTALL_PREFIX=$(python -c "import sys; print(sys.prefix)");
    if [ $NEST_INSTALL_PREFIX == '/usr' ] || [ $NEST_INSTALL_PREFIX == '/usr/local' ]; then
        export NEST_INSTALL_PREFIX=$HOME/nest
    fi
else
    export NEST_INSTALL_PREFIX=$2
fi
echo "Installing NEST to '$NEST_INSTALL_PREFIX'"

if [ -z "$3" ]; then
    export NEST_BUILD_DIR=$HOME/pype9-build/nest
else
    export NEST_BUILD_DIR=$3
fi
echo "Using '$NEST_BUILD_DIR' as NEST build directory"
mkdir -p $NEST_BUILD_DIR

export SRC_DIR=$NEST_BUILD_DIR/$NEST
export BUILD_DIR=$NEST_BUILD_DIR/build

# Download source from GitHub
wget https://github.com/nest/nest-simulator/releases/download/v$NEST_VERSION/$NEST.tar.gz -O $NEST_BUILD_DIR/$NEST.tar.gz;
pushd $NEST_BUILD_DIR;
tar xzf $NEST.tar.gz;
popd;

# Get Python installation information
export PYTHON_INCLUDE_DIR=$(python -c 'import sysconfig; print(sysconfig.get_config_var("INCLUDEPY"))');
export PYTHON_LIBRARY=$(python -c 'import os.path; import sysconfig; print(os.path.join(sysconfig.get_config_var("LIBPL"), sysconfig.get_config_var("LDLIBRARY")))')

# Install cython
pip install cython

mkdir -p $BUILD_DIR
pushd $BUILD_DIR

echo "Install Prefix: $NEST_INSTALL_PREFIX"
echo "Python Library: $PYTHON_LIBRARY"
echo "Python include dir: $PYTHON_INCLUDE_DIR"

cmake -Dwith-mpi=ON -DPYTHON_LIBRARY=$PYTHON_LIBRARY \
 -DPYTHON_INCLUDE_DIR=$PYTHON_INCLUDE_DIR \
 -DCMAKE_INSTALL_PREFIX=$NEST_INSTALL_PREFIX $SRC_DIR;
make -j8;
make install

popd
