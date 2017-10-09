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
export VENV=`python -c "import sys; print sys.prefix"`;

# To reset cache after updates
# rm $HOME/build/$NEST/config.log

if [ ! -d "$HOME/build/$NEST/CMakeFiles" ]; then
    echo "VENV: $VENV"
    cmake -Dwith-python=ON -Dwith-mpi=ON -DCMAKE_INSTALL_PREFIX=$VENV $HOME/$NEST;
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
