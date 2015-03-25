libdir= @libdir@/nest

lib_LTLIBRARIES=      IzhikevichBuiltInModule.la libIzhikevichBuiltInModule.la

IzhikevichBuiltInModule_la_CXXFLAGS= @AM_CXXFLAGS@
IzhikevichBuiltInModule_la_SOURCES=  IzhikevichBuiltInModule.cpp IzhikevichBuiltInModule.h \
                            IzhikevichBuiltIn.cpp IzhikevichBuiltIn.h
                            


IzhikevichBuiltInModule_la_LDFLAGS=  -module
libIzhikevichBuiltInModule_la_CXXFLAGS= $(IzhikevichBuiltInModule_la_CXXFLAGS) -DLINKED_MODULE
libIzhikevichBuiltInModule_la_SOURCES=  $(IzhikevichBuiltInModule_la_SOURCES)

MAKEFLAGS= @MAKE_FLAGS@

AM_CPPFLAGS= @NEST_CPPFLAGS@ \
             @INCLTDL@


.PHONY: install-slidoc

pkgdatadir=@datadir@/nest

nobase_pkgdata_DATA=\
	sli/IzhikevichBuiltInModule-init.sli

install-slidoc:
	NESTRCFILENAME=/dev/null $(DESTDIR)$(NEST_PREFIX)/bin/sli --userargs="@HELPDIRS@" \
	$(NEST_PREFIX)/share/nest/sli/install-help.sli

install-data-hook: install-exec install-slidoc

EXTRA_DIST= sli