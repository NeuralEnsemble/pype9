bin_PROGRAMS = raw-compare

raw_compare_CXXFLAGS = @AM_CXXFLAGS@
raw_compare_SOURCES =  main.cpp IzhikevichBranch.h IzhikevichBranch.cpp \
                   	   IzhikevichMaster.cpp IzhikevichMaster.h
raw_compare_LDADD =  ../nest-build/nestkernel/libnest.la ../nest-build/libnestutil/libnestutil.la ../nest-build/sli/libsli.la ../nest-build/librandom/librandom.la -lgsl -lgslcblas
raw_compare_LDFLAGS = -L/usr/local/Cellar/gsl/1.16/lib

MAKEFLAGS= @MAKE_FLAGS@

AM_CPPFLAGS= @NEST_CPPFLAGS@ \
             @INCLTDL@
