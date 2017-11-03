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
export PYTHON_INCLUDE_DIR=$(python -c "import sysconfig; print(sysconfig.get_config_var('INCLUDEPY'))");

if [ ! -d "$PYTHON_INCLUDE_DIR" ]; then
    echo "Did not find Python include dir at '$PYTHON_INCLUDE_DIR'"
    exit
fi

export PYTHON_LIBRARY=$(python -c "import os.path; import sysconfig; vars = sysconfig.get_config_vars(); print(os.path.join(vars['LIBDIR'], vars['LDLIBRARY']))")

if [ ! -f "$PYTHON_LIBRARY" ]; then
    echo "Did not find Python library at '$PYTHON_LIBRARY'"
    UBUNTU_PYTHON_LIBRARY=$(python -c "import os.path; import sysconfig; vars = sysconfig.get_config_vars(); print(os.path.join(vars['LIBDIR'], vars['MULTIARCH'], vars['LDLIBRARY']))")
    if [ -f $UBUNTU_PYTHON_LIBRARY ]; then
        export PYTHON_LIBRARY=$UBUNTU_PYTHON_LIBRARY
    else
        PYTHON_LIB_DIR=$(dirname $PYTHON_LIBRARY)
        if [ -d $PYTHON_LIB_DIR ]; then
            echo "Did not find '$PYTHON_LIBRARY' but found the following files in '$PYTHON_LIB_DIR'"
            ls $PYTHON_LIB_DIR
        else
            echo "Did not find containing directory for Python library '$PYTHON_LIBRARY'"
        fi
        exit    
    fi
fi

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
alias python=python2  # The NEST help doesn't build with Python3 sometimes
make -j8;
make install
unalias python

popd