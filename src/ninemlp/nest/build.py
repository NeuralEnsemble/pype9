"""

  This module contains functions for building and loading nest modules

  @author Tom Close

"""

#######################################################################################
#    
#    Copyright 2012 Okinawa Institute of Science and Technology (OIST), Okinawa, Japan
#
#######################################################################################
import time
import os.path
import subprocess as sp
import shutil
from ninemlp import DEFAULT_BUILD_MODE
from ninemlp.common.build import path_to_exec, get_build_paths, load_component_parameters

_SIMULATOR_BUILD_NAME = 'nest'

def ensure_camel_case(name):
    if len(name) < 2:
        raise Exception("The name ('{}') needs to be at least 2 letters long to enable the "
                        " capitalized version to be different from upper case version".format(name))
    if name == name.lower() or name == name.upper():
        name = name.title()
    return name

def build_celltype_files(celltype_name, ncml_path, install_dir=None, build_parent_dir=None,
                                method='gsl', build_mode=DEFAULT_BUILD_MODE, silent_build=False):
    """
    Generates the cpp code corresponding to the NCML file, then configures, and compiles and installs
    the corresponding module into nest
    
    @param celltype_name [str]: Name of the celltype to be built
    @param ncml_path [str]: Path to the NCML file from which the NMODL files will be compiled and built
    @param install_dir [str]: Path to the directory where the NMODL files will be generated and compiled
    @param build_parent_dir [str]: Used to set the path for the default 'install_dir', and the 'src' and 'build' dirs path
    @param method [str]: The method option to be passed to the NeMo interpreter command
    """
    # Save original working directory to reinstate it afterwards (just to be polite)
    orig_dir = os.getcwd()
    # Determine the paths for the src, build and install directories
    (default_install_dir, params_dir, 
            src_dir, compile_dir) = get_build_paths(ncml_path, celltype_name,_SIMULATOR_BUILD_NAME, 
                                                    build_parent_dir=build_parent_dir)
    if not install_dir:
        install_dir = default_install_dir
    # Clean existing directories from previous builds. TODO: It is a bit wasteful to build the
    # module again everytime, it should be checked to see if the module needs rebuilding first.
    shutil.rmtree(src_dir, ignore_errors=True)
    shutil.rmtree(params_dir, ignore_errors=True)
    shutil.rmtree(compile_dir, ignore_errors=True)
    shutil.rmtree(install_dir, ignore_errors=True)
    # Create fresh directories
    os.makedirs(src_dir)
    os.makedirs(params_dir)
    os.makedirs(compile_dir)
    os.makedirs(install_dir)
    # Compile the NCML file into NEST cpp code using NeMo
    nemo_path = path_to_exec('nemo')
    try:
        sp.check_call("{nemo_path} {ncml_path} --pyparams={params} --nest={output} "
                      "--nest-method={method}".format(nemo_path=nemo_path, method=method,
                                                      ncml_path=ncml_path, output=src_dir, 
                                                      params=params_dir), shell=True)
    except sp.CalledProcessError as e:
        raise Exception('Error while compiling NCML description into NEST cpp code -> {}'.format(e))
    # Generate configure.ac and Makefile
    create_configure_ac(celltype_name, src_dir)
    create_makefile(celltype_name, src_dir)
    create_boilerplate_cpp(celltype_name, src_dir)
    create_sli_initialiser(celltype_name, src_dir)
    # Run the required shell commands to bootstrap the build configuration
    run_bootstrap(src_dir)
    # Run configure script, make and make install
    os.chdir(compile_dir)
    sp.check_call('{src_dir}/configure --prefix={install_dir}'
                  .format(src_dir=src_dir, install_dir=install_dir), shell=True)
    sp.check_call('make', shell=True)
    sp.check_call('make install', shell=True)
    # Switch back to original dir
    os.chdir(orig_dir)
    # Load component parameters for use in python interface
    component_parameters = load_component_parameters(celltype_name, params_dir)
    # Return installation directory
    return install_dir, component_parameters


def create_configure_ac(celltype_name, src_dir):
    configure_ac = """
AC_PREREQ(2.52)3

AC_INIT({celltype_name}, 1.0, nest_user@nest-initiative.org)

# These variables are exported to include/config.h
{celltype_name_upper}_MAJOR=1
{celltype_name_upper}_MINOR=0
{celltype_name_upper}_PATCHLEVEL=0

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

AM_INIT_AUTOMAKE(nest, ${celltype_name_upper}_VERSION)

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

# sundials-config
SUNDIALS_CONFIG=`which sundials-config`
AC_ARG_WITH(sundials,[  --with-sundials=script    sundials-config script including path],
[
  if test "$withval" != yes; then
    SUNDIALS_CONFIG=$withval
#  else
#    AC_MSG_ERROR([--with-sundials-config expects the sundials-config script as argument. See README for details.])
  fi
])

# does nest-config work
AC_MSG_CHECKING([for nest-config ])
AC_CHECK_FILE($NEST_CONFIG, HAVE_NEST=yes, 
              AC_MSG_ERROR([No usable nest-config was found. You may want to use --with-nest-config.]))
AC_MSG_RESULT(found)

# Does sundials-config work
AC_MSG_CHECKING([for sundials-config ])
AC_CHECK_FILE($SUNDIALS_CONFIG, HAVE_SUNDIALS=yes, 
              AC_MSG_ERROR([No usable sundials-config was found. You may want to use --with-sundials-config.]))
AC_MSG_RESULT(found)

# the following will crash if nest-config does not run
# careful, lines below must not break
AC_MSG_CHECKING([for NEST directory information ])
NEST_PREFIX=`$NEST_CONFIG --prefix`
NEST_CPPFLAGS=`$NEST_CONFIG --cflags`
NEST_COMPILER=`$NEST_CONFIG --compiler`
if test $prefix = NONE; then prefix=`$NEST_CONFIG --prefix`; fi
AC_MSG_RESULT($NEST_CPPFLAGS)

AC_MSG_CHECKING([for SUNDIALS preprocessor flags ])
SUNDIALS_CPPFLAGS="`$SUNDIALS_CONFIG -m cvode -t s -l c -s cppflags`"
AC_MSG_RESULT($SUNDIALS_CPPFLAGS)

AC_MSG_CHECKING([for SUNDIALS linker options ])
SUNDIALS_LDFLAGS="`$SUNDIALS_CONFIG -m cvode -t s -l c -s libs` -lblas -llapack"
AC_MSG_RESULT($SUNDIALS_LDFLAGS)

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

{celltype_name_upper}_SAVE_CXXFLAGS=$CXXFLAGS

# Must first check if we are on AIX
AC_AIX

# Check for C++ compiler, looking for the same compiler
# used with NEST
AC_PROG_CXX([ $NEST_COMPILER ])

# the following is makeshift, should have the macro set proper
# {celltype_name_upper}_SET_CXXFLAGS
AM_CXXFLAGS=${celltype_name_upper}_SAVE_CXXFLAGS
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
AC_SUBST(SUNDIALS_CONFIG)
AC_SUBST(SUNDIALS_CPPFLAGS)
AC_SUBST(SUNDIALS_LDFLAGS)

AM_CONFIG_HEADER({celltype_name}_config.h:{celltype_name}_config.h.in)
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
echo "{celltype_name} Configuration Summary"
echo "-------------------------------------------------------"
echo
echo "C++ compiler        : $CXX"
echo "C++ compiler flags  : $AM_CXXFLAGS"
echo "NEST compiler flags : $NEST_CPPFLAGS"
echo "SUNDIALS compiler flags : $SUNDIALS_CPPFLAGS"
echo "SUNDIALS linker flags : $SUNDIALS_LDFLAGS"

# these variables will still contain '${{prefix}}'
# we want to have the versions where this is resolved, too:
eval eval eval  PKGDOCDIR_AS_CONFIGURED=$PKGDOCDIR
eval eval eval  PKGDATADIR_AS_CONFIGURED=$PKGDATADIR

echo
echo "-------------------------------------------------------"
echo
echo "You can build and install {celltype_name} now, using"
echo "  make"
echo "  make install"
echo
echo "{celltype_name} will be installed to:"
echo -n "  "; eval eval echo "$libdir"
echo""".format(celltype_name=celltype_name, celltype_name_upper=celltype_name.upper())
    # Write configure.ac with module names to file
    with open(os.path.join(src_dir, 'configure.ac'), 'w') as f:
        f.write(configure_ac)

def create_makefile(celltype_name, src_dir):
# Generate makefile
    makefile = """
libdir= @libdir@/nest

lib_LTLIBRARIES=      {celltype_name}Loader.la lib{celltype_name}Loader.la

{celltype_name}Loader_la_CXXFLAGS= @AM_CXXFLAGS@
{celltype_name}Loader_la_SOURCES=  {celltype_name}.cpp      {celltype_name}.h \\
                             {celltype_name}Loader.cpp {celltype_name}Loader.h


{celltype_name}Loader_la_LDFLAGS=  -module

lib{celltype_name}Loader_la_CXXFLAGS= $({celltype_name}Loader_la_CXXFLAGS) -DLINKED_MODULE
lib{celltype_name}Loader_la_SOURCES=  $({celltype_name}Loader_la_SOURCES)

MAKEFLAGS= @MAKE_FLAGS@

AM_CPPFLAGS= @NEST_CPPFLAGS@ \\
             @SUNDIALS_CPPFLAGS@ \\
             @INCLTDL@

AM_LDFLAGS = @SUNDIALS_LDFLAGS@

.PHONY: install-slidoc

nobase_pkgdata_DATA=\\
    {celltype_name}Loader.sli

install-slidoc:
    NESTRCFILENAME=/dev/null $(DESTDIR)$(NEST_PREFIX)/bin/sli --userargs="@HELPDIRS@" \
    $(NEST_PREFIX)/share/nest/sli/install-help.sli

install-data-hook: install-exec install-slidoc

EXTRA_DIST= sli
""".format(celltype_name=celltype_name)
    # Write configure.ac with module names to file
    with open(os.path.join(src_dir, 'Makefile.am'), 'w') as f:
        f.write(makefile)

def run_bootstrap(src_dir):
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
    # Run bootstrap command to create configure script
    os.chdir(src_dir)
    sp.check_call(bootstrap_cmd, shell=True)

def create_boilerplate_cpp(celltype_name, src_dir):
    
    header_code="""
/*
 *  {celltype_name}Loader.h
 *
 *  This file is part of NEST.
 *
 *  Copyright (C) 2008 by
 *  The NEST Initiative
 *
 *  See the file AUTHORS for details.
 *
 *  Permission is granted to compile and modify
 *  this file for non-commercial use.
 *  See the file LICENSE for details.
 *
 */

#ifndef {celltype_name_upper}MODULE_H
#define {celltype_name_upper}MODULE_H

#include "dynmodule.h"
#include "slifunction.h"

namespace nest
{{
  class Network;
}}

// Put your stuff into your own namespace.
namespace ncml {{
  
/**
 * Class defining your model.
 * @note For each model, you must define one such class, with a unique name.
 */
class {celltype_name}Loader : public DynModule
{{
public:

  // Interface functions ------------------------------------------
  
  /**
   * @note The constructor registers the module with the dynamic loader. 
   *       Initialization proper is performed by the init() method.
   */
  {celltype_name}Loader();
  
  /**
   * @note The destructor does not do much in modules. Proper "downrigging"
   *       is the responsibility of the unregister() method.
   */
  ~{celltype_name}Loader();

  /**
   * Initialize module by registering models with the network.
   * @param SLIInterpreter* SLI interpreter
   * @param nest::Network*  Network with which to register models
   * @note  Parameter Network is needed for historical compatibility
   *        only.
   */
  void init(SLIInterpreter*, nest::Network*);

  /**
   * Return the name of your model.
   */
  const std::string name(void) const;
  
  /**
   * Return the name of a sli file to execute when {celltype_name}Loader is loaded.
   * This mechanism can be used to define SLI commands associated with your
   * module, in particular, set up type tries for functions you have defined.
   */
  const std::string commandstring(void) const;
     
public:
  
  // Classes implementing your functions -----------------------------
  
  /**
   * Implement a function for a step-pattern-based connection.
   * @note What this function does is described in the SLI documentation
   *       in the cpp file.
   * @note The mangled name indicates this function expects the following
   *       arguments on the stack (bottom first): vector of int, int, 
   *       vector of int, int. 
   * @note You must define a member object in your module class
   *       of the function class. execute() is later invoked on this
   *       member.
   */
  class StepPatternConnect_Vi_i_Vi_i_lFunction: public SLIFunction
     {{
     public:
       void execute(SLIInterpreter *) const;
     }};

     StepPatternConnect_Vi_i_Vi_i_lFunction stepPatternConnect_Vi_i_Vi_i_lFunction;
  }};
}} // namespace ncml

#endif
""".format(celltype_name=celltype_name, celltype_name_upper=celltype_name.upper())
    # Write configure.ac with module names to file
    with open(os.path.join(src_dir, celltype_name + 'Loader.h'), 'w') as f:
        f.write(header_code)
    # Create the C++ file
    cpp_code="""
 /*   
 *  {celltype_name}Loader.cpp
 *  This file is part of NEST.
 *
 *  Copyright (C) 2008 by
 *  The NEST Initiative
 *
 *  See the file AUTHORS for details.
 *
 *  Permission is granted to compile and modify
 *  this file for non-commercial use.
 *  See the file LICENSE for details.
 *
 */

// include necessary NEST headers
//#include "config.h"
#include "network.h"
#include "model.h"
#include "dynamicloader.h"
#include "genericmodel.h"
#include "generic_connector.h"
#include "booldatum.h"
#include "integerdatum.h"
#include "tokenarray.h"
#include "exceptions.h"
#include "sliexceptions.h"
#include "nestmodule.h"

// include headers with your own stuff
#include "{celltype_name}Loader.h"
#include "{celltype_name}.h"

// -- Interface to dynamic module loader ---------------------------------------

/*
 * The dynamic module loader must be able to find your module. 
 * You make the module known to the loader by defining an instance of your 
 * module class in global scope. This instance must have the name
 *
 * <modulename>_LTX_mod
 *
 * The dynamicloader can then load modulename and search for symbol "mod" in it.
 */
 
ncml::{celltype_name}Loader {celltype_name}Loader_LTX_mod;

// -- DynModule functions ------------------------------------------------------

ncml::{celltype_name}Loader::{celltype_name}Loader()
  {{ 
#ifdef LINKED_MODULE
     // register this module at the dynamic loader
     // this is needed to allow for linking in this module at compile time
     // all registered modules will be initialized by the main app's dynamic loader
     nest::DynamicLoaderModule::registerLinkedModule(this);
#endif     
   }}

ncml::{celltype_name}Loader::~{celltype_name}Loader()
   {{
   }}

   const std::string ncml::{celltype_name}Loader::name(void) const
   {{
     return std::string("{celltype_name}"); // Return name of the module
   }}

   const std::string ncml::{celltype_name}Loader::commandstring(void) const
   {{
     /* 1. Tell interpreter that we provide the C++ part of {celltype_name}Loader with the
           current revision number. 
        2. Instruct the interpreter to check that {celltype_name}Loader-init.sli exists, 
           provides at least version 1.0 of the SLI interface to {celltype_name}Loader, and
           to load it.
      */
     return std::string(
       "/{celltype_name}Loader /C++ ($Revision: 8512 $) provide-component "
       "/{celltype_name}Loader /SLI (7165) require-component"
       );
   }}

   /* BeginDocumentation
      Name: StepPatternConnect - Connect sources and targets with a stepping pattern
      
      Synopsis:
      [sources] source_step [targets] target_step synmod StepPatternConnect -> n_connections
      
      Parameters:
      [sources]     - Array containing GIDs of potential source neurons
      source_step   - Make connection from every source_step'th neuron
      [targets]     - Array containing GIDs of potential target neurons
      target_step   - Make connection to every target_step'th neuron
      synmod        - The synapse model to use (literal, must be key in synapsedict)
      n_connections - Number of connections made
      
      Description:
      This function subsamples the source and target arrays given with steps
      source_step and target_step, beginning with the first element in each array,
      and connects the selected nodes.
      
      Example:
      /first_src 0 /network_size get def
      /last_src /iaf_neuron 20 Create def  % nodes  1 .. 20
      /src [first_src last_src] Range def
      /last_tgt /iaf_neuron 10 Create def  % nodes 21 .. 30
      /tgt [last_src 1 add last_tgt] Range def
      
      src 6 tgt 4 /drop_odd_spike StepPatternConnect 
  
      This connects nodes [1, 7, 13, 19] as sources to nodes [21, 25,
      29] as targets using synapses of type drop_odd_spike, and
      returning 12 as the number of connections.  The following
      command will print the connections (you must paste the SLI
      command as one long line):

      src {{ /s Set << /source s /synapse_type /static_synapse >> FindConnections {{ GetStatus /target get }} Map dup length 0 gt {{ cout s <- ( -> ) <- exch <-- endl }} if ; }} forall
      1 -> [21 25 29]
      7 -> [21 25 29]
      13 -> [21 25 29]
      19 -> [21 25 29]
      
      Remark:
      This function is only provided as an example for how to write your own 
      interface function. 
      
      Author:
      Hans Ekkehard Plesser
      
      SeeAlso:
      Connect, ConvergentConnect, DivergentConnect
   */
   void ncml::{celltype_name}Loader::StepPatternConnect_Vi_i_Vi_i_lFunction::execute(SLIInterpreter *i) const
   {{
     // Check if we have (at least) five arguments on the stack.
     i->assert_stack_load(5);

     // Retrieve source, source step, target, target step from the stack
     const TokenArray sources = getValue<TokenArray> (i->OStack.pick(4)); // bottom
     const long src_step      = getValue<long>       (i->OStack.pick(3));
     const TokenArray targets = getValue<TokenArray> (i->OStack.pick(2));
     const long tgt_step      = getValue<long>       (i->OStack.pick(1));  
     const Name synmodel_name = getValue<std::string>(i->OStack.pick(0)); // top
     
     // Obtain synapse model index
     const Token synmodel 
       = nest::NestModule::get_network().get_synapsedict().lookup(synmodel_name);
     if ( synmodel.empty() )
       throw nest::UnknownSynapseType(synmodel_name.toString());
     const nest::index synmodel_id = static_cast<nest::index>(synmodel);

     // Build a list of targets with the given step
     TokenArray selected_targets;
     for ( size_t t = 0 ; t < targets.size() ; t += tgt_step )
       selected_targets.push_back(targets[t]);
     
     // Now connect all appropriate sources to this list of targets
     size_t Nconn = 0;  // counts connections
     for ( size_t s = 0 ; s < sources.size() ; s += src_step )
     {{
       // We must first obtain the GID of the source as integer
       const nest::long_t sgid = getValue<nest::long_t>(sources[s]);

       // nest::network::divergent_connect() requires weight and delay arrays. We want to use
       // default values from the synapse model, so we pass empty arrays.
       nest::NestModule::get_network().divergent_connect(sgid, selected_targets, 
                             TokenArray(), TokenArray(),
                             synmodel_id);
       Nconn += selected_targets.size();
     }}

     // We get here only if none of the operations above throws and exception.
     // Now we can safely remove the arguments from the stack and push Nconn
     // as our result. 
     i->OStack.pop(5);
     i->OStack.push(Nconn);
     
     // Finally, we pop the call to this functions from the execution stack.
     i->EStack.pop();
   }}

  //-------------------------------------------------------------------------------------

  void ncml::{celltype_name}Loader::init(SLIInterpreter *i, nest::Network*)
  {{
    /* Register a neuron or device model.
       Give node type as template argument and the name as second argument.
       The first argument is always a reference to the network.
       Return value is a handle for later unregistration.
    */
       nest::register_model<nest::{celltype_name}>(nest::NestModule::get_network(), 
                        "{celltype_name}");

    /* Register a synapse type.
       Give synapse type as template argument and the name as second argument.
       The first argument is always a reference to the network.
    */
/*
    This is ommitted because this was just a dummy spike connection
    nest::register_prototype_connection<DropOddSpikeConnection>(nest::NestModule::get_network(), 
                                                       "drop_odd_synapse");
*/
    /* Register a SLI function.
       The first argument is the function name for SLI, the second a pointer to
       the function object. If you do not want to overload the function in SLI,
       you do not need to give the mangled name. If you give a mangled name, you
       should define a type trie in the {celltype_name}Loader-init.sli file.
    */
    i->createcommand("StepPatternConnect_Vi_i_Vi_i_l", 
                     &stepPatternConnect_Vi_i_Vi_i_lFunction);

  }}  // {celltype_name}Loader::init()
    
""".format(celltype_name=celltype_name)
    # Write configure.ac with module names to file
    with open(os.path.join(src_dir, celltype_name + 'Loader.cpp'), 'w') as f:
        f.write(cpp_code)

def create_sli_initialiser(celltype_name, src_dir):
    
    sli_code="""
/* 
 * Initialization file for {celltype_name}.
 * Run automatically when {celltype_name} is loaded.
 */

M_DEBUG ({celltype_name}Loader.sli) (Initializing SLI support for {celltype_name}.) message

/{celltype_name}Loader /SLI ($Revision: 7918 $) provide-component
/{celltype_name}Loader /C++ (7165) require-component

/StepPatternConnect [ /arraytype /integertype /arraytype /integertype /literaltype ]
{{ 
  StepPatternConnect_Vi_i_Vi_i_l
}} def
""".format(celltype_name=celltype_name)
    # Write configure.ac with module names to file
    with open(os.path.join(src_dir, celltype_name + 'Loader.sli'), 'w') as f:
        f.write(sli_code)

if __name__ == '__main__':
    build_celltype_files('mymodule', '/home/tclose/kbrain/xml/cerebellum/ncml/Granule_DeSouza10.xml')





