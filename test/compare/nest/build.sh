#!/usr/bin/env bash
aclocal \
&& automake --add-missing \
&& autoconf
rm -r build/*
mkdir build
cd build
CPPFLAGS=-DDEBUG CFLAGS='-g3 -O0' CXXFLAGS='-g3 -O0' ../configure --prefix=`pwd`/..
make install
