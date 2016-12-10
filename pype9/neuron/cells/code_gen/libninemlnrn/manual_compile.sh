#!/usr/bin/env bash
# For manual compilation of libninemlnrn if the setup.py fails or neuron is updated

if [ "$CC" == "" ]; then
	echo "Please set the environment variable CC to the C-compiler used by nrnivmodl"
fi

if [ "$WITH_GSL" != "" ]; then
	GSL_INCLUDE=-I$WITH_GSL/include
	GSL_LIB=-L$WITH_GSL/lib
fi

$CC -fPIC -c -o nineml.o nineml.cpp $GSL_INCLUDE
$CC -shared $GSL_LIB -lm -lgslcblas -lgsl -o libninemlnrn.so nineml.o -lc
