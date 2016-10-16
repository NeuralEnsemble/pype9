#!/bin/bash
# Adapted from similar install script in pyNN (https://github.com/NeuralEnsemble/PyNN)

set -e  # stop execution in case of errors

export INSTALL_DIR=$HOME/pype9-prereq
export BUILD_DIR=$INSTALL_DIR/build
export NEST_VERSION="2.10.0"
export NEST="nest-$NEST_VERSION"

mkdir -p $BUILD_DIR/$NEST
if [ ! -f "$BUILD_DIR/$NEST_VERSION/configure" ]; then
    wget https://github.com/nest/nest-simulator/releases/download/v$NEST_VERSION/$NEST.tar.gz -O $HOME/$INSTALL_DIR/$NEST.tar.gz;
    pushd $HOME/$INSTALL_DIR;
    tar xzf $NEST.tar.gz;
    popd;
else
    echo 'Using cached version of NEST sources.';
fi

pushd $HOME/$INSTALL_DIR/build/$NEST
if [ ! -f "$HOME/$INSTALL_DIR/build/$NEST/config.log" ]; then
    export VENV=`python -c "import sys; print sys.prefix"`;
    $HOME/$NEST/configure --with-mpi --prefix=$VENV;
    make;
else
    echo 'Using cached NEST build directory.';
    echo "$HOME/$NEST";
    ls $HOME/$NEST;
    echo "$HOME/$INSTALL_DIR/build/$NEST";
    ls $HOME/$INSTALL_DIR/build/$NEST;
fi
make install
popd
