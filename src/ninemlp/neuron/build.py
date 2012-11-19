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
import time
import platform
import subprocess as sp
from ninemlp import DEFAULT_BUILD_MODE
from ninemlp.common.build import path_to_exec, get_build_paths, load_component_parameters

BUILD_ARCHS = [platform.machine(), 'i686', 'x86_64', 'powerpc', 'umac']
_SIMULATOR_BUILD_NAME = 'neuron'
_MODIFICATION_TIME_FILE = 'modification_time'

if 'NRNHOME' in os.environ:
    os.environ['PATH'] += os.pathsep + os.environ['NRNHOME']
else:
    # I apologise for this little hack (this is the path on my machine, 
    # to save me having to set the environment variable in eclipse)
    os.environ['PATH'] += os.pathsep + '/opt/NEURON-7.2/x86_64/bin'

def build_celltype_files(celltype_name, ncml_path, install_dir=None, build_parent_dir=None,
    method='derivimplicit', build_mode=DEFAULT_BUILD_MODE, silent_build=False, kinetics=[]):
    """
    Generates and builds the required NMODL files for a given NCML cell class
    
    @param celltype_name [str]: Name of the celltype to be built
    @param ncml_path [str]: Path to the NCML file from which the NMODL files will be compiled and built
    @param install_dir [str]: Path to the directory where the NMODL files will be generated and compiled
    @param build_parent_dir [str]: Used to set the default 'install_dir' path
    @param method [str]: The method option to be passed to the NeMo interpreter command
    @param kinetics [list(str)]: A list of ionic components to be generated using the kinetics option
    """
    default_install_dir, params_dir, src_dir, compile_dir = get_build_paths(ncml_path, celltype_name, #@UnusedVariable
                                        _SIMULATOR_BUILD_NAME, build_parent_dir=build_parent_dir)
    if not install_dir:
        install_dir = default_install_dir

    # ['lazy', 'force', 'build_only', 'require']
    if build_mode == 'force' or build_mode == 'build_only':
        shutil.rmtree(install_dir, ignore_errors=False)
        shutil.rmtree(params_dir, ignore_errors=False)
    elif build_mode == 'compile_only' or build_mode == 'require':
        if not os.path.exists(install_dir) or not os.path.exists(params_dir):
            raise Exception("Prebuilt installation directory '{install}' and/or python parameters "\
                            "directory '{params}' are not present, which are required for " \
                            "'require' and 'compile_only' build options".format(install=install_dir,
                                                                                params=params_dir))
    try:
        if not os.path.exists(install_dir):
            os.makedirs(install_dir)
        if not os.path.exists(params_dir):
            os.makedirs(params_dir)
    except IOError as e:
        raise Exception("Could not create a required neuron build directory, check the required " \
                        "permissions or specify a different parent build directory -> {}".format(e))
    # Get the stored modification time of the previous build if it exists
    install_modification_time_path = os.path.join(install_dir, _MODIFICATION_TIME_FILE)
    params_modification_time_path = os.path.join(params_dir, _MODIFICATION_TIME_FILE)
    if os.path.exists(install_modification_time_path):
        with open(install_modification_time_path) as f:
            prev_install_modification_time = f.readline()
    else:
        prev_install_modification_time = ''
    if os.path.exists(params_modification_time_path):
        with open(params_modification_time_path) as f:
            prev_params_modification_time = f.readline()
    else:
        prev_params_modification_time = ''
    # Get the modification time of the source NCML file for comparison with the build directory       
    ncml_modification_time = time.ctime(os.path.getmtime(ncml_path))
    rebuilt = False
    if ncml_modification_time != prev_install_modification_time or \
                                            ncml_modification_time != prev_params_modification_time:
        nemo_path = path_to_exec('nemo')
        try:
            sp.check_call("{nemo_path} {ncml_path} -p --pyparams={params} --nmodl={output} " \
                          "--nmodl-method={method} --nmodl-kinetic={kinetics}"\
                          .format(nemo_path=nemo_path, ncml_path=os.path.normpath(ncml_path),
                                  output=os.path.normpath(install_dir), params=params_dir,
                                  kinetics=','.join(kinetics), method=method), shell=True)
        except sp.CalledProcessError as e:
            raise Exception("Error while compiling NCML description into NMODL code -> {}".\
                            format(e))
        # Build mode is set to 'force' because the mod files have been regenerated
        with open(install_modification_time_path, 'w') as f:
            f.write(ncml_modification_time)
        with open(params_modification_time_path, 'w') as f:
            f.write(ncml_modification_time)
        rebuilt = True
    if rebuilt or build_mode == 'compile_only':
        compile_nmodl(install_dir, build_mode='force', silent=silent_build)            
    # Load the parameter name translations from the params dir 
    component_parameters = load_component_parameters(celltype_name, params_dir)
    return install_dir, component_parameters


def compile_nmodl (model_dir, build_mode=DEFAULT_BUILD_MODE, silent=False):
    """
    Builds all NMODL files in a directory
    @param model_dir: The path of the directory to build
    @param build_mode: Can be one of either, 'lazy', 'super_lazy', 'require', 'force', or \
'build_only'. 'lazy' doesn't \
run nrnivmodl if the library is found, 'require', requires that the library is found otherwise \
throws an exception (useful on clusters that require precompilation before parallelisation where \
the error message could otherwise be confusing), 'force' removes existing library if found and \
recompiles, and 'build_only' removes existing library if found, recompile and then exits
    @param verbose: Prints out verbose debugging messages
    """
    # Change working directory to model directory
    orig_dir = os.getcwd()
    try:
        os.chdir(model_dir)
    except OSError:
        raise Exception("Could not find NMODL directory '{}'".format(model_dir))
    # Clean up old build directories if present
    found_required_lib = False
    for arch in BUILD_ARCHS:
        path = os.path.join(model_dir, arch)
        if os.path.exists(path):
            if build_mode in ('lazy', 'require'):
                # If the library is found, set the 'found_required_lib' flag.
                found_required_lib = True
            elif build_mode in ('force', 'build_only'):
                # Instead of flagging 'found_required_lib', the library is removed to allow fresh 
                # compilation
                shutil.rmtree(path, ignore_errors=True)
    if not found_required_lib:
        if build_mode == 'require':
            raise Exception("The required NMODL binaries were not found in directory '{}' " \
                            "(change the build mode from 'require' any of 'lazy', 'build_only', " \
                            "or 'force' in order to compile them).".format(model_dir))
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
                build_error = sp.call(cmd_path, stdout=fnull, stderr=fnull)
        else:
            # Run nrnivmodl command on directory
            build_error = sp.call(cmd_path)
        if build_error:
            raise Exception("Could not compile NMODL files in directory '{}' - ".format(model_dir))
    elif not silent:
        print "Found existing mechanisms in '{}' directory, compile skipped (set 'build_mode' " \
              "argument to 'force' enforce recompilation them).".format(model_dir)
    os.chdir(orig_dir)

















