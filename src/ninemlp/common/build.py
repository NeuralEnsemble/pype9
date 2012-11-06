"""

    This module defines common methods used in simulator specific build modules

    @author Tom Close

"""

#######################################################################################
#
#    Copyright 2011 Okinawa Institute of Science and Technology (OIST), Okinawa, Japan
#
#######################################################################################
import platform
import os.path
import subprocess as sp

_RELATIVE_BUILD_DIR = 'build'
_SRC_DIR = 'src'
_INSTALL_DIR = 'install'
_COMPILE_DIR = 'compile' # Ignored for NEURON but used for NEST

def get_build_paths(ncml_path, celltype_name, simulator_name, build_parent_dir=None):
    """
    return the respective source, install and optional compile directory paths for a given cell type
    
    @param ncml_path [str]: The path to the NCML file (used in the default build directories)
    @param celltype_name [str]: The name of the cell type (used in the default build directories)
    @param simulator_name [str] The name of the simulator, i.e. neuron or nest (used in the default build directories)
    @param module_build_dir [str]: The path of the parent directory of the build directories (defaults to 'build' in the directory where the ncml path is located)
    
    @return [str]: (<default-install_directory>, <source-directory>, <compile-directory>)
    """
    if not build_parent_dir:
        build_parent_dir = os.path.join(os.path.dirname(ncml_path), _RELATIVE_BUILD_DIR, 
                                                                    simulator_name, celltype_name)
    src_dir = os.path.join(build_parent_dir, _SRC_DIR)
    default_install_dir = os.path.join(build_parent_dir, _INSTALL_DIR)
    compile_dir = os.path.join(build_parent_dir, _COMPILE_DIR)
    return (default_install_dir, src_dir, compile_dir)

def path_to_exec(exec_name):
    """
    Returns the full path to an executable by searching the $PATH environment variable
    
    @param exec_name[str]: Name of executable to search the execution path for
    @return [str]: Full path to executable
    """
    if platform.system() == 'Windows':
        exec_name += '.exe'
    # Check the system path for the 'nrnivmodl' command
    exec_path = None
    for dr in os.environ['PATH'].split(os.pathsep):
        path = os.path.join(dr, exec_name)
        if os.path.exists(path):
            exec_path = path
            break
    if not exec_path:
        raise Exception("Could not find nrnivmodl on the system path '%s'" % os.environ['PATH'])
    return exec_path
