# Automake file for external dynamic modules for NEST
#
# Hans Ekkehard Plesser, April 2008
# Automake file for the Developer Module
#
# libTestModule is built as a normal, installable library.
# It will be installed to $prefix/lib by make install.
#
# Headers from this directory are not to be installed upon
# make install. They are therefore included in _SOURCES.


# 1. Exchange "my" in "TestModule" with the name of your model below
#    (ten locations).
# 2. Add all .cpp and .h files from your code as *_SOURCES. Header files
#    are given only so that they will be included in the tarball if you
#    run "make dist" on your module.
# 3. The TestModule* stuff creates a module that can be loaded at runtime.
#    It is called TestModule.so.
# 4. The libTestModule* stuff creates a library against which NEST can be
#    linked.

libdir= @libdir@/nest

lib_LTLIBRARIES=      TestModule.la libTestModule.la

TestModule_la_CXXFLAGS= @AM_CXXFLAGS@
TestModule_la_SOURCES=  TestModule.cpp      TestModule.h      \
                      Test.h Test.cpp
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
	NESTRCFILENAME=/dev/null $(DESTDIR)$(NEST_PREFIX)/bin/sli --userargs="@HELPDIRS@" $(NEST_PREFIX)/share/nest/sli/install-help.sli

install-data-hook: install-exec install-slidoc

EXTRA_DIST= sli
