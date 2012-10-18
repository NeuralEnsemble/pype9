"""

  This module contains functions for building and loading nest modules

  @author Tom Close

"""

#######################################################################################
#
#    Copyright 2012 Okinawa Institute of Science and Technology (OIST), Okinawa, Japan
#
#######################################################################################
import sys
import os.path
import subprocess as sp
import shutil

_SRC_DIR = 'src'
_BUILD_DIR = 'build'
_INSTALL_DIR = 'install'


def build_cellclass(cellclass_name, ncml_location, module_build_dir):
    """
    Generates the cpp code corresponding to the NCML file, then configures, and compiles and installs
    the corresponding module into nest
    
    @param name[str]: Name of the module to compile and load
    @param ncml_location[str]: The location of the NCML file to compile
    """
    # Determine the paths for the src, build and install directories
    src_dir = os.path.normpath(os.path.join(module_build_dir, _SRC_DIR))
    build_dir = os.path.normpath(os.path.join(module_build_dir, _BUILD_DIR))
    install_dir = os.path.normpath(os.path.join(module_build_dir, _INSTALL_DIR))
    # Clean existing directories from previous builds
    shutil.rmtree(src_dir, ignore_errors=True)
    shutil.rmtree(build_dir, ignore_errors=True)
    shutil.rmtree(install_dir, ignore_errors=True)
    # Create fresh directories
    os.makedirs(src_dir)
    os.makedirs(build_dir)
    os.makedirs(install_dir)
    # Compile the NCML file into NEST cpp code
    if sys.platform == 'win32':
        nemo_path = sp.check_output('where nemo', shell=True)
    else:
        nemo_path = sp.check_output('which nemo', shell=True)
    try:
        sp.check_call('{nemo_path} {ncml_path} --nest {output}'.format(nemo_path=nemo_path,
                                            ncml_path=ncml_location, output=src_dir), shell=True)
    except sp.CalledProcessError as e:
        raise Exception('Error while compiling NCML description into NEST cpp code -> {}'.format(e))
#    shutil.copy('/home/tclose/git/kbrain/external/nest/nest-2.0.0-rc4/examples/MyModule/mymodule.h', src_dir)
#    shutil.copy('/home/tclose/git/kbrain/external/nest/nest-2.0.0-rc4/examples/MyModule/mymodule.cpp', src_dir)
#    shutil.copy('/home/tclose/git/kbrain/external/nest/nest-2.0.0-rc4/examples/MyModule/pif_psc_alpha.cpp', src_dir)
#    shutil.copy('/home/tclose/git/kbrain/external/nest/nest-2.0.0-rc4/examples/MyModule/pif_psc_alpha.h', src_dir)
#    shutil.copy('/home/tclose/git/kbrain/external/nest/nest-2.0.0-rc4/examples/MyModule/drop_odd_spike_connection.h', src_dir)
#    shutil.copytree('/home/tclose/git/kbrain/external/nest/nest-2.0.0-rc4/examples/MyModule/sli', src_dir + '/sli')
    # Generate configure.ac file
    configure_ac = """
AC_PREREQ(2.52)

AC_INIT({module_lower}, 1.0, nest_user@nest-initiative.org)

# These variables are exported to include/config.h
{module_upper}_MAJOR=1
{module_upper}_MINOR=0
{module_upper}_PATCHLEVEL=0

# Exporting source and build directories requires full path names.
# Thus we have to expand.
# Here, we are in top build dir, since source dir must exist, we can just
# move there and call pwd
if test "x$srcdir" = x ; then
  PKGSRCDIR=`pwd`
else
  PKGSRCDIR=`cd $srcdir && pwd`
fi
PKGBUILDDIR=`pwd`

# If this is not called, install-sh will be put into .. by bootstrap.sh
# moritz, 06-26-06
AC_CONFIG_AUX_DIR(.)

AM_INIT_AUTOMAKE(nest, ${module_upper}_VERSION)

# obtain host system type; HEP 2004-12-20
AC_CANONICAL_HOST

# ------------------------------------------------------------------------
# Handle options
#
# NOTE: No programs/compilations must be run in this section;
#       otherwise CFLAGS and CXXFLAGS may take on funny default
#       values.
#       HEP 2004-12-20
# ------------------------------------------------------------------------

# nest-config
NEST_CONFIG=`which nest-config`
AC_ARG_WITH(nest,[  --with-nest=script    nest-config script including path],
[
  if test "$withval" != yes; then
    NEST_CONFIG=$withval
  else
    AC_MSG_ERROR([--with-nest-config expects the nest-config script as argument. See README for details.])
  fi
])

# -------------------------------------------
# END Handle options
# -------------------------------------------


# does nest-config work
AC_MSG_CHECKING([for nest-config ])
AC_CHECK_FILE($NEST_CONFIG, HAVE_NEST=yes, 
              AC_MSG_ERROR([No usable nest-config was found. You may want to use --with-nest-config.]))
AC_MSG_RESULT(found)

# the following will crash if nest-config does not run
# careful, lines below must not break
AC_MSG_CHECKING([for NEST directory information ])
NEST_PREFIX=`$NEST_CONFIG --prefix`
NEST_CPPFLAGS=`$NEST_CONFIG --cflags`
NEST_COMPILER=`$NEST_CONFIG --compiler`
if test $prefix = NONE; then prefix=`$NEST_CONFIG --prefix`; fi
AC_MSG_RESULT($NEST_CPPFLAGS)

# Set the platform-dependent compiler flags based on the canonical
# host string.  These flags are placed in AM_{{C,CXX}}FLAGS.  If
# {{C,CXX}}FLAGS are given as environment variables, then they are
# appended to the set of automatically chosen flags.  After
# {{C,CXX}}FLAGS have been read out, they must be cleared, since
# system-dependent defaults will otherwise be placed into the
# Makefiles.  HEP 2004-12-20.

# Before we can determine the proper compiler flags, we must know
# which compiler we are using.  Since the pertaining AC macros run the
# compiler and set CFLAGS, CXXFLAGS to system-dependent values, we
# need to save command line/enviroment settings of these variables
# first. AC_AIX must run before the compiler is run, so we must run it
# here.
# HEP 2004-12-21

{module_upper}_SAVE_CXXFLAGS=$CXXFLAGS

# Must first check if we are on AIX
AC_AIX

# Check for C++ compiler, looking for the same compiler
# used with NEST
AC_PROG_CXX([ $NEST_COMPILER ])

# the following is makeshift, should have the macro set proper
# {module_upper}_SET_CXXFLAGS
AM_CXXFLAGS=${module_upper}_SAVE_CXXFLAGS
CXXFLAGS=

## Configure C environment

AC_PROG_LD
AC_PROG_INSTALL

AC_LIBLTDL_CONVENIENCE       ## put libltdl into a convenience library
AC_PROG_LIBTOOL           ## use libtool
AC_CONFIG_SUBDIRS(libltdl) ## also configure subdir containing libltdl

#-- Set the language to C++
AC_LANG_CPLUSPLUS

#-- Look for programs needed in the Makefile
AC_PROG_CXXCPP
AM_PROG_LIBTOOL
AC_PATH_PROGS([MAKE],[gmake make],[make])

# ---------------------------------------------------------------
# Configure directories to be built
# ---------------------------------------------------------------

PKGDATADIR=$datadir/$PACKAGE
PKGDOCDIR=$datadir/doc/$PACKAGE

# set up directories from which to build help
# second line replaces space with colon as separator
HELPDIRS="$PKGSRCDIR $PKGSRCDIR/sli"
HELPDIRS=`echo $HELPDIRS | tr " " ":"`

#-- Replace these variables in *.in
AC_SUBST(HAVE_NEST)
AC_SUBST(NEST_CONFIG)
AC_SUBST(NEST_CPPFLAGS)
AC_SUBST(NEST_COMPILER)
AC_SUBST(NEST_PREFIX)
AC_SUBST(HELPDIRS)
AC_SUBST(PKGSRCDIR)
AC_SUBST(PKGBUILDDIR)
AC_SUBST(PKGDATADIR)
AC_SUBST(PKGDOCDIR)
AC_SUBST(KERNEL)
AC_SUBST(HOST)
AC_SUBST(SED)
AC_SUBST(LD)
AC_SUBST(host_os)
AC_SUBST(host_cpu)
AC_SUBST(host_vendor)
AC_SUBST(AS)
AC_SUBST(CXX)
AC_SUBST(AR)
AC_SUBST(ARFLAGS)
AC_SUBST(CXX_AR)
AC_SUBST(AM_CXXFLAGS)
AC_SUBST(AM_CFLAGS)
AC_SUBST(MAKE)
AC_SUBST(MAKE_FLAGS)
AC_SUBST(INCLTDL)
AC_SUBST(LIBLTDL)

AM_CONFIG_HEADER({module_lower}_config.h:{module_lower}_config.h.in)
AC_CONFIG_FILES(Makefile)

# -----------------------------------------------
# Create output
# -----------------------------------------------
AC_OUTPUT


# -----------------------------------------------
# Report, after output at end of configure run
# Must come after AC_OUTPUT, so that it is 
# displayed after libltdl has been configured
# -----------------------------------------------

echo
echo "-------------------------------------------------------"
echo "{module_capitalized} Configuration Summary"
echo "-------------------------------------------------------"
echo
echo "C++ compiler        : $CXX"
echo "C++ compiler flags  : $AM_CXXFLAGS"
echo "NEST compiler flags : $NEST_CPPFLAGS"

# these variables will still contain '${{prefix}}'
# we want to have the versions where this is resolved, too:
eval eval eval  PKGDOCDIR_AS_CONFIGURED=$PKGDOCDIR
eval eval eval  PKGDATADIR_AS_CONFIGURED=$PKGDATADIR

echo
echo "-------------------------------------------------------"
echo
echo "You can build and install {module_capitalized} now, using"
echo "  make"
echo "  make install"
echo
echo "{module_capitalized} will be installed to:"
echo -n "  "; eval eval echo "$libdir"
echo""".format(module_lower=cellclass_name.lower(), module_upper=cellclass_name.upper(),
                                                    module_capitalized=cellclass_name.capitalize())
    # Write configure.ac with module names to file
    with open(os.path.join(src_dir, 'configure.ac'), 'w') as f:
        f.write(configure_ac)
    # Generate makefile
    makefile = """
libdir= @libdir@/nest

lib_LTLIBRARIES=      {cellclass_name}.la lib{cellclass_name}.la

{cellclass_name}_la_CXXFLAGS= @AM_CXXFLAGS@
{cellclass_name}_la_SOURCES=  {cellclass_name}.cpp      {cellclass_name}.h \\
                          pif_psc_alpha.cpp pif_psc_alpha.h \\
                          drop_odd_spike_connection.h
{cellclass_name}_la_LDFLAGS=  -module

lib{cellclass_name}_la_CXXFLAGS= $({cellclass_name}_la_CXXFLAGS) -DLINKED_MODULE
lib{cellclass_name}_la_SOURCES=  $({cellclass_name}_la_SOURCES)

MAKEFLAGS= @MAKE_FLAGS@

AM_CPPFLAGS= @NEST_CPPFLAGS@ \\
             @INCLTDL@      

.PHONY: install-slidoc

nobase_pkgdata_DATA=\\
    sli/{cellclass_name}.sli

install-slidoc:
    NESTRCFILENAME=/dev/null $(DESTDIR)$(NEST_PREFIX)/bin/sli --userargs="@HELPDIRS@" $(NEST_PREFIX)/share/nest/sli/install-help.sli

install-data-hook: install-exec install-slidoc

EXTRA_DIST= sli
""".format(cellclass_name=cellclass_name)
    # Write configure.ac with module names to file
    with open(os.path.join(src_dir, 'Makefile.am'), 'w') as f:
        f.write(makefile)
    # The list of shell commands to run to bootstrap the build
    bootstrap_cmd = """
#!/bin/sh

echo "Bootstrapping {src_dir}"

if test -d autom4te.cache ; then
# we must remove this cache, because it
# may screw up things if configure is run for
# different platforms. 
  echo "  -> Removing old automake cache ..."
  rm -rf autom4te.cache
fi

echo "  -> Running aclocal ..."
aclocal

echo "  -> Running libtoolize ..."
if [ `uname -s` = Darwin ] ; then
# libtoolize is glibtoolize on OSX
  LIBTOOLIZE=glibtoolize
else  
  LIBTOOLIZE=libtoolize
fi

libtool_major=`$LIBTOOLIZE --version | head -n1 | cut -d\) -f2 | cut -d\. -f1`
$LIBTOOLIZE --force --copy --ltdl

echo "  -> Re-running aclocal ..."
if test $libtool_major -le 2; then
  aclocal --force
else
  aclocal --force -I $(pwd)/libltdl/m4
fi

echo "  -> Running autoconf ..."
autoconf

# autoheader must run before automake 
echo "  -> Running autoheader ..."
autoheader

echo "  -> Running automake ..."
automake --foreign --add-missing --force-missing --copy

echo "Done."
""".format(src_dir=src_dir)
    # Save original working directory to reinstate it afterwards (just to be polite)
    orig_dir = os.getcwd() 
    # Run bootstrap command to create configure script
    os.chdir(src_dir)
    sp.check_call(bootstrap_cmd, shell=True)
    # Run configure script, passing the prefix of the installation directory
    os.chdir(build_dir)
    sp.check_call('{config_path} --prefix={install_dir}'.format(
                                           config_path=os.path.join(src_dir, 'configure'),
                                           install_dir=install_dir), shell=True)
    # Run make and install
    sp.check_call('make', shell=True)
    sp.check_call('make install', shell=True)
    # Switch back to original dir
    os.chdir(orig_dir)
    # Return installation directory
    return install_dir

if __name__ == '__main__':
    build_cellclass('mymodule', '/home/tclose/kbrain/xml/cerebellum/ncml/MyModule.xml')





