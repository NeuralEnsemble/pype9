#!/bin/bash

set -e  # stop execution in case of errors

if [ -z "$1" ]; then
    echo "NEST install script:"
    echo "  Usage: VERSION [PYTHON_VERSION INSTALL_PREFIX BUILD_DIR]"
    echo ""
    echo "ERROR! Please provide NEST version as first argument to install script"
    exit
fi

VERSION=$1
NEST="nest-$VERSION"

if [ -z "$2" ]; then
    PYTHON_VERSION=$(python -c "import sysconfig; print(sysconfig.get_config_var('py_version').split('.')[0])");
else
    PYTHON_VERSION=$2
fi
echo "Using Python $PYTHON_VERSION"

PYTHON=python$PYTHON_VERSION

if [ -z "$3" ]; then
    # Use virtualenv bin by default
    INSTALL_PREFIX=$($PYTHON -c "import sys; print(sys.prefix)");
    if [ $INSTALL_PREFIX == '/usr' ] || [ $INSTALL_PREFIX == '/usr/local' ]; then
        INSTALL_PREFIX=$HOME/nest
    fi
else
    INSTALL_PREFIX=$3
fi
echo "Installing NEST to '$INSTALL_PREFIX'"

if [ -z "$4" ]; then
    BASE_DIR=$HOME/.pype9/prereq-build/$NEST/$PYTHON
    rm -rf $BASE_DIR
else
    BASE_DIR=$4
fi
echo "Using '$BASE_DIR' as NEST base build directory"
mkdir -p $BASE_DIR

export SRC_DIR=$BASE_DIR/$NEST
export BUILD_DIR=$BASE_DIR/$NEST-build

# Download source from GitHub
if [ "${VERSION%%-*}" == 'tag' ]; then
    # Download and untar
    echo ${VERSION##tag-}
    wget -nv http://github.com/nrnhines/nrn/archive/${VERSION##tag-}.zip -O $BASE_DIR/$NEST.zip;
    pushd $BASE_DIR;
    unzip -qq $NEST.zip;
    rm $NEST.zip;
    mv nrn* $NEST;
    popd;
else
    wget -nv https://github.com/nest/nest-simulator/releases/download/v$VERSION/$NEST.tar.gz -O $BASE_DIR/$NEST.tar.gz;
    pushd $BASE_DIR;
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

echo "Install Prefix: $INSTALL_PREFIX"
echo "Python Library: $PYTHON_LIBRARY"
echo "Python include dir: $PYTHON_INCLUDE_DIR"

PYTHON_ARGS="-Dwith-python=$PYTHON_VERSION -DPYTHON_LIBRARY=$PYTHON_LIBRARY \
    -DPYTHON_INCLUDE_DIRS=$PYTHON_INCLUDE_DIRS"

CMAKE_CMD="cmake -Dwith-mpi=ON -DCMAKE_INSTALL_PREFIX=$INSTALL_PREFIX $PYTHON_ARGS $SRC_DIR"
echo "NEST CMake:"
echo $CMAKE_CMD
$CMAKE_CMD
make -j8 -s;
make -s install
popd

# Create symlink from multiarch sub-directory to site-packages if required
ARCH_SUBDIR=$($PYTHON -c "import sysconfig; print(sysconfig.get_config_vars().get('multiarchsubdir', ''))");
if [ ! -z "$ARCH_SUBDIR" ]; then
    SHORT_PYVER=$($PYTHON -c "import sysconfig; print(sysconfig.get_config_var('py_version_short'))");
    pushd $INSTALL_PREFIX/lib/python$SHORT_PYVER/site-packages
    ln -sf $INSTALL_PREFIX/lib/$ARCH_SUBDIR/python$SHORT_PYVER/site-packages/nest
    popd;
fi

# Test installation
$PYTHON -c "import nest; nest.GetKernelStatus();"
