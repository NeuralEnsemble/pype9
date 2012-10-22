"""

  This module contains functions for building and loading NMODL mechanisms

  @author Tom Close

"""

#######################################################################################
#
#    Copyright 2012 Okinawa Institute of Science and Technology (OIST), Okinawa, Japan
#
#######################################################################################

import os.path
import shutil
import platform
import subprocess as sp
from ninemlp import DEFAULT_BUILD_MODE
from ninemlp.common.build import path_to_exec

BUILD_ARCHS = [platform.machine(), 'i686', 'x86_64', 'powerpc', 'umac']

if 'NRNHOME' in os.environ:
    os.environ['PATH'] += os.pathsep + os.environ['NRNHOME']
else:
    # I apologise for this hack (this is the path on my machine, to save me having to set the environment variable in eclipse)
    os.environ['PATH'] += os.pathsep + '/opt/NEURON-7.2/x86_64/bin' 

def build_cellclass(cellclass_name, ncml_location, module_build_dir, build_mode=DEFAULT_BUILD_MODE):
    
    nemo_path = path_to_exec('nemo')
    try:
        sp.check_call('{nemo_path} {ncml_path} --nmodl {output}'.format(nemo_path=nemo_path,
                                            ncml_path=ncml_location, output=src_dir), shell=True)
    except sp.CalledProcessError as e:
        raise Exception('Error while compiling NCML description into NEST cpp code -> {}'.format(e))
    
    

def compile_nmodl (model_dir, build_mode=DEFAULT_BUILD_MODE, silent=False):
    """
    Builds all NMODL files in a directory
    @param model_dir: The path of the directory to build
    @param build_mode: Can be one of either, 'lazy', 'super_lazy', 'require', 'force', or \
'compile_only'. 'lazy' runs nrnivmodl again to compile any touched mod files, 'super_lazy' doesn't \
run nrnivmodl if the library is found, 'require', requires that the library is found otherwise \
throws an exception (useful on clusters that require precompilation before parallelisation where \
the error message could otherwise be confusing), 'force' removes existing library if found and \
recompiles, and 'compile_only' removes existing library if found, recompile and then exits
    @param verbose: Prints out verbose debugging messages
    """
    # Change working directory to model directory
    orig_dir = os.getcwd()
    try:
        os.chdir(model_dir)
    except OSError:
        raise Exception("Could not find NMODL directory '%s'" % model_dir)
    # Clean up old build directories if present
    found_required_lib = False
    for arch in BUILD_ARCHS:
        path = os.path.join(model_dir, arch)
        if os.path.exists(path):
            if build_mode in ('super_lazy', 'require'):
                found_required_lib = True
            elif build_mode in ('force', 'compile_only'):
                shutil.rmtree(path, ignore_errors=True)
    if not found_required_lib:
        if build_mode == 'require':
            raise Exception("The required NMODL binaries were not found in directory '%s' (change the build mode from 'require' any of 'lazy', 'compile_only', or 'force' in order to compile them)." % model_dir)
        # Get platform specific command name
        if platform.system() == 'Windows':
            cmd_name = 'nrnivmodl.exe'
        else:
            cmd_name = 'nrnivmodl'
        # Check the system path for the 'nrnivmodl' command
        cmd_path = None
        for dr in os.environ['PATH'].split(os.pathsep):
            path = os.path.join(dr, cmd_name)
            if os.path.exists(path):
                cmd_path = path
                break
        if not cmd_path:
            raise Exception("Could not find nrnivmodl on the system path '%s'" % os.environ['PATH'])
        print "Building mechanisms in '%s' directory." % model_dir
        if silent:
            with open(os.devnull, "w") as fnull:
                build_error = sp.call(cmd_path, stdout = fnull, stderr = fnull)
        else:
            # Run nrnivmodl command on directory
            build_error = sp.call(cmd_path)
        if build_error:
            raise Exception("Could not compile NMODL files in directory '%s' - " % model_dir)
    elif not silent:
        print "Found existing mechanisms in '%s' directory, compile skipped (set 'build_mode' argument to 'force' enforce recompilation them)." % model_dir
    os.chdir(orig_dir)
    

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
