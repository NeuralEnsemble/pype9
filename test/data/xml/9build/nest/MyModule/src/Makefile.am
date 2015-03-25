libdir= @libdir@/nest

lib_LTLIBRARIES=      TestModule.la libTestModule.la

TestModule_la_CXXFLAGS= @AM_CXXFLAGS@
TestModule_la_SOURCES=  TestModule.cpp TestModule.h \
                            Test.cpp Test.h
                            


TestModule_la_LDFLAGS=  -module
libTestModule_la_CXXFLAGS= $(TestModule_la_CXXFLAGS) -DLINKED_MODULE
libTestModule_la_SOURCES=  $(TestModule_la_SOURCES)

MAKEFLAGS= @MAKE_FLAGS@

AM_CPPFLAGS= @NEST_CPPFLAGS@ \             
             @INCLTDL@


.PHONY: install-slidoc

pkgdatadir=@datadir@/nest

nobase_pkgdata_DATA=\
	sli/TestModule-init.sli

install-slidoc:
	NESTRCFILENAME=/dev/null $(DESTDIR)$(NEST_PREFIX)/bin/sli --userargs="@HELPDIRS@" \
	$(NEST_PREFIX)/share/nest/sli/install-help.sli

install-data-hook: install-exec install-slidoc

EXTRA_DIST= sli