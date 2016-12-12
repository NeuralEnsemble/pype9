#!/bin/bash
# Adapted from similar install script in pyNN (https://github.com/NeuralEnsemble/PyNN)

	
export NEST_VERSION="2.10.0"
export NEST="nest-$NEST_VERSION"

# Remove cache if it is causing errors
#rm -rf $HOME/$NEST
#rm -rf $HOME/build/$NEST

set -e  # stop execution in case of errors

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
export VENV=`python -c "import sys; print sys.prefix"`;
if [ ! -f "$HOME/build/$NEST/config.log" ]; then
    echo "VENV: $VENV"
    $HOME/$NEST/configure --with-mpi --prefix=$VENV;
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
