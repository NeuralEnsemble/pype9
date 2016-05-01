AM_CXXFLAGS = -I/Users/tclose/git/debug/gsl/1.16/include -Wall -std=c++11 -g3 -O0
LDADD = -L/Users/tclose/git/debug/gsl/1.16/lib -lgsl -lgslcblas -lm

bin_PROGRAMS = compare

compare_SOURCES =  mock_nest.cpp mock_sli.h mock_sli.cpp dict.h dictutils.h\
									 archiving_node.h ring_buffer.h connection.h universal_data_logger.h \
									 exceptions.h recordables_map.h random.h network.h \
                   tarraryobj.h tarrayobj.cpp tokenarray.h tokenarray.cpp \
                   name.h name.cpp nest_time.h nest_time.cpp nest.h \
                   numerics.h numerics.cpp arraydatum.h nest_names.h \
                   nest_names.cpp lockptr.h setup.h main.cpp \
                   models/PyNNLeakyIntegrateAndFire.cpp models/PyNNLeakyIntegrateAndFire.h \
                   models/IafAlpha.cpp models/IafAlpha.h \
                   models/IzhikevichMaster.h models/IzhikevichMaster.cpp \
                   models/IzhikevichBranch.h models/IzhikevichBranch.cpp
