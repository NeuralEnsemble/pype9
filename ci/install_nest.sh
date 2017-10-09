#!/bin/bash
# Adapted from similar install script in pyNN (https://github.com/NeuralEnsemble/PyNN)

	
export NEST_VERSION="2.12.0"
export NEST="nest-$NEST_VERSION"

# Remove cache because it is causing errors until the previous build runs successfully
rm -rf $HOME/$NEST
rm -rf $HOME/build/$NEST

set -e  # stop execution in case of errors

pip install cython
if [ ! -f "$HOME/$NEST/CMakeLists.txt" ]; then
    wget https://github.com/nest/nest-simulator/releases/download/v$NEST_VERSION/$NEST.tar.gz -O $HOME/$NEST.tar.gz;
    pushd $HOME;
    tar xzf $NEST.tar.gz;
    popd;
else
    echo 'Using cached version of NEST sources.';
fi
mkdir -p $HOME/build/$NEST
pushd $HOME/build/$NEST

# Get Python installation information
export VENV=$(python -c "import sys; print(sys.prefix)");
export PYLIB_DIR=$(python -c 'from distutils import sysconfig; print(sysconfig.get_config_var("LIBDIR"))');
export PYINC_DIR=$(python -c 'from distutils import sysconfig; print(sysconfig.get_config_var("INCLUDEDIR"))');
export PYLIB_NAME=$(python -c 'from distutils import sysconfig; print(".".join(sysconfig.get_config_var("LIBRARY").split(".")[:2]))').so;
export PYVER=$(python -c 'import sys; print("{}.{}".format(*sys.version_info[:2]))');
export PYLIBRARY=$PYLIB_DIR/$PYLIB_NAME

# To reset cache after updates
# rm $HOME/build/$NEST/config.log

if [ ! -d "$HOME/build/$NEST/CMakeFiles" ]; then
    echo "VENV: $VENV"
    echo "Python Library: $PYLIBRARY"
    echo "Python include dir: $PYINC_DIR"
    cmake -Dwith-mpi=ON -DPYTHON_LIBRARY=$PYLIBRARY -DPYTHON_INCLUDE_DIR=$PYINC_DIR/python$PYVER -DCMAKE_INSTALL_PREFIX=$VENV $HOME/$NEST;
    make;
else
    echo 'Using cached NEST build directory.';
    echo "$HOME/$NEST";
    ls $HOME/$NEST;
    echo "$HOME/build/$NEST";
    ls $HOME/build/$NEST;
fi
make install
popd
