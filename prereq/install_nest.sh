#!/bin/bash
# Adapted from similar install script in pyNN (https://github.com/NeuralEnsemble/PyNN)

set -e  # stop execution in case of errors

export NEST_VERSION="2.10.0"
export NEST="nest-$NEST_VERSION"
pip install cython
if [ ! -f "$HOME/$NEST/configure" ]; then
    wget https://github.com/nest/nest-simulator/releases/download/v$NEST_VERSION/$NEST.tar.gz -O $HOME/$NEST.tar.gz;
    pushd $HOME;
    tar xzf $NEST.tar.gz;
    popd;
else
    echo 'Using cached version of NEST sources.';
fi
mkdir -p $HOME/build/$NEST
pushd $HOME/build/$NEST
if [ ! -f "$HOME/build/$NEST/config.log" ]; then
    export VENV=`python -c "import sys; print sys.prefix"`;
    echo "VENV: $VENV"
    $HOME/$NEST/configure --with-mpi --prefix=$VENV;
    make;
else
    echo 'Using cached NEST build directory.';
    echo "$HOME/$NEST";
    ls $HOME/$NEST;
    echo "$HOME/build/$NEST";
    ls $HOME/build/$NEST;
	ln -s $VENV/python2.7.12 $VENV/python2.7.10  # NEST is looking for 2.7.10 for some reason
fi
make install
popd
