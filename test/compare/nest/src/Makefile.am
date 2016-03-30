AM_CXXFLAGS = -I/usr/local/Cellar/gsl/1.16/include -Wall
LDADD = -L/usr/local/Cellar/gsl/1.16/lib -lgsl -lgslcblas -lm

bin_PROGRAMS = compare

compare_SOURCES =  main.cpp branch.h branch.cpp master.cpp master.h \
                   mock_nest.h mock_nest.cpp mock_sli.h mock_sli.cpp \
                   tarraryobj.h tarrayobj.cpp tokenarray.h tokenarray.cpp \
                   name.h name.cpp nest_time.h nest_time.cpp nest.h \
                   numerics.h numerics.cpp arraydatum.h nest_names.h nest_names.cpp

