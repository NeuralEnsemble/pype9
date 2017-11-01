#!/bin/bash
# Adapted from similar install script in pyNN (https://github.com/NeuralEnsemble/PyNN)

if [ -z "$1" ]; then
	echo "Please provide NEST version to install script"
	return
fi

NEST_VERSION=$1
NEST="nest-$NEST_VERSION"
export NEST_SRC_DIR=$HOME/$NEST
export NEST_BUILD_DIR=$HOME/build/$NEST

if [ "$2" == 'purge' ]; then
	# Remove cache because it is causing errors until the previous build runs successfully
	rm -rf $NEST_SRC_DIR
	rm -rf $NEST_BUILD_DIR
fi

set -e  # stop execution in case of errors

if [ ! -f "$NEST_SRC_DIR/CMakeLists.txt" ]; then
    wget https://github.com/nest/nest-simulator/releases/download/v$NEST_VERSION/$NEST.tar.gz \
     -O $HOME/$NEST.tar.gz;
    pushd $HOME;
    tar xzf $NEST.tar.gz;
    popd;
else
    echo 'Using cached version of NEST sources.';
fi

mkdir -p $NEST_BUILD_DIR
pushd $NEST_BUILD_DIR

# Get Python installation information
VENV=$(python -c "import sys; print(sys.prefix)");
PYLIB_DIR=$(python -c 'from distutils import sysconfig; print(sysconfig.get_config_var("LIBDIR"))');
PYINC_DIR=$(python -c 'from distutils import sysconfig; print(sysconfig.get_config_var("INCLUDEDIR"))');
PYLIB_NAME=$(python -c 'from distutils import sysconfig; print(".".join(sysconfig.get_config_var("LIBRARY").split(".")[:2]))').so;
PYVER=$(python -c 'import sys; print("{}.{}".format(*sys.version_info[:2]))');
PYLIBRARY=$PYLIB_DIR/$PYLIB_NAME

# Install cython
pip install cython

if [ ! -d "$NEST_BUILD_DIR/CMakeFiles" ]; then
    echo "VENV: $VENV"
    echo "Python Library: $PYLIBRARY"
    echo "Python include dir: $PYINC_DIR"
    cmake -Dwith-mpi=ON -DPYTHON_LIBRARY=$PYLIBRARY \
     -DPYTHON_INCLUDE_DIR=$PYINC_DIR/python$PYVER \
     -DCMAKE_INSTALL_PREFIX=$VENV $NEST_SRC_DIR;
    make;
else
    echo 'Using cached NEST build and install directories.';
    echo "$NEST_SRC_DIR";
    ls $NEST_SRC_DIR;
    echo "$NEST_BUILD_DIR";
    ls $NEST_BUILD_DIR;
fi
make install
popd
