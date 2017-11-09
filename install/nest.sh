#!/bin/bash

set -e  # stop execution in case of errors

if [ -z "$1" ]; then
    echo "NEST install script:"
    echo "  Usage: VERSION [INSTALL_PREFIX BUILD_DIR]"
    echo ""
    echo "ERROR! Please provide NEST version as first argument to install script"
    exit
fi

NEST_VERSION=$1
NEST="nest-$NEST_VERSION"

if [ -z "$2" ]; then
    PYTHON_VERSION=$(python -c "import sysconfig; print(sysconfig.get_config_var('py_version').split('.')[0])");
else
    PYTHON_VERSION=$2
fi
echo "Using Python $PYTHON_VERSION"

PYTHON=python$PYTHON_VERSION

if [ -z "$3" ]; then
    # Use virtualenv bin by default
    export NEST_INSTALL_PREFIX=$($PYTHON -c "import sys; print(sys.prefix)");
    if [ $NEST_INSTALL_PREFIX == '/usr' ] || [ $NEST_INSTALL_PREFIX == '/usr/local' ]; then
        export NEST_INSTALL_PREFIX=$HOME/nest
    fi
else
    export NEST_INSTALL_PREFIX=$3
fi
echo "Installing NEST to '$NEST_INSTALL_PREFIX'"

if [ -z "$4" ]; then
    export NEST_BUILD_DIR=$HOME/pype9-build/nest
    rm -rf $NEST_BUILD_DIR
else
    export NEST_BUILD_DIR=$4
fi
echo "Using '$NEST_BUILD_DIR' as NEST build directory"
mkdir -p $NEST_BUILD_DIR

export SRC_DIR=$NEST_BUILD_DIR/$NEST
export BUILD_DIR=$NEST_BUILD_DIR/$NEST-build

# Download source from GitHub
if [ "${NEST_VERSION%%-*}" == 'sha' ]; then
    # Download and untar
    echo ${NEST_VERSION##sha-}
    wget http://github.com/nrnhines/nrn/archive/${NEST_VERSION##sha-}.zip -O $NEST_BUILD_DIR/$NEST.zip;
    pushd $NEST_BUILD_DIR;
    unzip $NEST.zip;
    rm $NEST.zip;
    mv nrn* $NEST;
    popd;
else
    wget https://github.com/nest/nest-simulator/releases/download/v$NEST_VERSION/$NEST.tar.gz -O $NEST_BUILD_DIR/$NEST.tar.gz;
    pushd $NEST_BUILD_DIR;
    tar xzf $NEST.tar.gz;
    popd;
fi

# Install cython
pip install cython

mkdir -p $BUILD_DIR
pushd $BUILD_DIR

# Get Python installation paths
export PYTHON_INCLUDE_DIRS=$($PYTHON -c "import sysconfig; print(sysconfig.get_config_var('INCLUDEPY'))");
if [ ! -d "$PYTHON_INCLUDE_DIRS" ]; then
    echo "Python include dir '$PYTHON_INCLUDE_DIRS'"
    ls $(dirname $PYTHON_INCLUDE_DIRS)
    exit
fi
export PYTHON_LIBRARY=$($PYTHON -c "import os, sysconfig, platform; vars = sysconfig.get_config_vars(); print(os.path.join(vars['LIBDIR'] + vars.get('multiarchsubdir', ''), (vars['LIBRARY'][:-1] + 'dylib' if platform.system() == 'Darwin' else vars['INSTSONAME'])))");
if [ ! -f "$PYTHON_LIBRARY" ]; then
    echo "Python lib dir '$PYTHON_LIBRARY':"
    ls $(dirname $PYTHON_LIBRARY)
    exit
fi

echo "Install Prefix: $NEST_INSTALL_PREFIX"
echo "Python Library: $PYTHON_LIBRARY"
echo "Python include dir: $PYTHON_INCLUDE_DIR"


CMAKE_CMD="cmake -Dwith-mpi=ON -Dwith-python=$PYTHON_VERSION -DPYTHON_LIBRARY=$PYTHON_LIBRARY \
 -DPYTHON_INCLUDE_DIRS=$PYTHON_INCLUDE_DIRS \
 -DCMAKE_INSTALL_PREFIX=$NEST_INSTALL_PREFIX $SRC_DIR"
echo "NEST CMake:"
echo $CMAKE_CMD
$CMAKE_CMD
make -j8;
make install
popd

# Create symlink from multiarch sub-directory to site-packages if required
ARCH_SUBDIR=$($PYTHON -c "import sysconfig; print(sysconfig.get_config_vars().get('multiarchsubdir', ''))");
if [ ! -z "$ARCH_SUBDIR" ]; then
    PYVER=$($PYTHON -c "import sysconfig; print(sysconfig.get_config_var('py_version_short'))");
    pushd $NEST_INSTALL_PREFIX/lib/python$PYVER/site-packages
    ln -sf $NEST_INSTALL_PREFIX/lib/$ARCH_SUBDIR/python$PYVER/site-packages/nest
    popd;
fi
