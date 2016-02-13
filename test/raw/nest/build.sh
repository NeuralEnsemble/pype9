#!/usr/bin/env bash

aclocal \
&& automake --add-missing \
&& autoconf
rm -r build/*
cd build
../configure --prefix=`pwd`/../bin
make
