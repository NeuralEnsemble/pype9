bin_PROGRAMS = raw-compare

raw_compare_CXXFLAGS = -I/usr/local/Cellar/gsl/1.16/include @AM_CXXFLAGS@
raw_compare_SOURCES =  main.cpp IzhikevichBranch.h IzhikevichBranch.cpp \
                   	   IzhikevichMaster.cpp IzhikevichMaster.h \
                   	   lockptr.h lockptrdatum.h lockptrdatrum_impl.h \
                   	   name.h name.cc token.h token.cc slitype.h slitype.cc \
                   	   slifunction.h datum.h datum.cc dict.h dict.cc
raw_compare_LDADD =  -lgsl -lgslcblas
raw_compare_LDFLAGS = -L/usr/local/Cellar/gsl/1.16/lib

MAKEFLAGS= @MAKE_FLAGS@

AM_CPPFLAGS= @INCLTDL@
