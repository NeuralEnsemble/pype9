lib_LTLIBRARIES= libninemlnrn.la

libninemlnrn_la_CFLAGS = @AM_CFLAGS@ -I/usr/local/Cellar/gsl/1.16/include
libninemlnrn_la_LFLAGS = @LIBS@ -version-info 0:1:0
LDADD = -L/usr/local/Cellar/gsl/1.16/lib -lgsl -lgslcblas -lm

libninemlnrn_la_SOURCES =  nineml.cpp
