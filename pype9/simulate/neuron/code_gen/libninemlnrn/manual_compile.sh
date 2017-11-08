#!/usr/bin/env bash
# For manual compilation of libninemlnrn if the setup.py fails or neuron is reinstalled

if [ "$CC" == "" ]; then
	echo "Please set the environment variable CC to the C-compiler used by nrnivmodl."
	echo "This can be found by locating nrnmech_makefile and finding the value it sets for CC"
	echo "If you have installed GNU Scientific Library with a non-standard prefix then "
	echo "please also set the WITH_GSL environment variable to the GSL prefix"
	exit
fi

if [ "$WITH_GSL" != "" ]; then
	GSL_INCLUDE=-I$WITH_GSL/include
	GSL_LIB=-L$WITH_GSL/lib
fi

if [ "`uname`" == 'Darwin' ]; then
	INSTALL_NAME="-install_name  @rpath/libninemlnrn.so"
else
	INSTALL_NAME=''
fi

$CC -fPIC -c -o libinemlnrn.o libinemlnrn.cpp $GSL_INCLUDE
$CC -shared $GSL_LIB $INSTALL_NAME -lm -lgslcblas -lgsl -o libninemlnrn.so libinemlnrn.o -lc
