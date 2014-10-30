"""
    This module defines common methods used in simulator specific build modules

    @author Tom Close
"""

##########################################################################
#
#  Copyright 2011 Okinawa Institute of Science and Technology (OIST), Okinawa, Japan
#
##########################################################################
from __future__ import absolute_import
import platform
import os
from os.path import abspath, dirname, join
from collections import defaultdict
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from itertools import izip
from runpy import run_path
from abc import ABCMeta


class BaseCodeGenerator(object):

    __metaclass__ = ABCMeta

    BUILD_MODE_OPTIONS = ['lazy', 'force', 'build_only', 'require',
                          'compile_only']
    _RELATIVE_BUILD_DIR = '.9build'
    _PARAMS_DIR = 'params'
    _SRC_DIR = 'src'
    _INSTALL_DIR = 'install'
    _COMPILE_DIR = 'compile'  # Ignored for NEURON but used for NEST
    _TIME_OF_EDIT_FILE = 'modification_time'

    def __init__(self):
        # Instantiate Jinja2 environment
        jinja_env = Environment(loader=FileSystemLoader(self.templates_path),
                                trim_blocks=True,
                                undefined=StrictUndefined)
        # Add some globals used by the template code
        jinja_env.globals.update(izip=izip, enumerate=enumerate)

    def _get_build_paths(self, nineml_path, celltype_name, simulator_name,
                        build_parent_dir=None):
        """
        return the respective source, install and optional compile directory
        paths for a given cell type

        @param nineml_path [str]: The path to the NCML file (used in the
                                  default build directories)
        @param celltype_name [str]: The name of the cell type (used in the
                                    default build directories)
        @param simulator_name [str] The name of the simulator, i.e. neuron or
                                    nest (used in the default build
                                    directories)
        @param module_build_dir [str]: The path of the parent directory of the
                                       build directories (defaults to 'build'
                                       in the directory where the ncml path is
                                       located)

        @return [str]: (<default-install_directory>, <source-directory>,
                        <compile-directory>)
        """
        if not build_parent_dir:
            build_parent_dir = abspath(join(dirname(nineml_path),
                                            self._RELATIVE_BUILD_DIR,
                                            simulator_name, celltype_name))
        src_dir = str(abspath(join(build_parent_dir, self._SRC_DIR)))
        default_install_dir = str(abspath(join(build_parent_dir,
                                               self._INSTALL_DIR)))
        compile_dir = str(abspath(join(build_parent_dir, self._COMPILE_DIR)))
        params_dir = str(abspath(join(build_parent_dir, self._PARAMS_DIR)))
        return (default_install_dir, params_dir, src_dir, compile_dir)

    def _path_to_exec(self, exec_name):
        """
        Returns the full path to an executable by searching the $PATH
        environment variable

        @param exec_name[str]: Name of executable to search the execution path
        for @return [str]: Full path to executable
        """
        if platform.system() == 'Windows':
            exec_name += '.exe'
        # Check the system path for the 'nrnivmodl' command
        exec_path = None
        for dr in os.environ['PATH'].split(os.pathsep):
            path = join(dr, exec_name)
            if os.path.exists(path):
                exec_path = path
                break
        if not exec_path:
            raise Exception("Could not find executable '{}' on the system path"
                            "'{}'".format(exec_name, os.environ['PATH']))
        return exec_path

    def _load_component_translations(self, biophysics_name, params_dir):
        """
        Loads component parameter translations from names to standard reference
        name (eg. 'e_rev', 'MaximalConductance') dictionary. For each file in
        the params directory with a '.py' extension starting with the
        celltype_name assume that it is a parameters file.

        @param biophysics_name [str]: The name of the cell biophysics to load
                                      the parameter names for
        @param params_dir [str]: The path to the directory that contains the
                                 parameters
        """
        component_translations = defaultdict(dict)
        # Loop through all the files in the params directory
        for f_name in os.listdir(params_dir):
            if f_name.startswith(biophysics_name) and f_name.endswith('.py'):
                # Load the properties from the parameters file
                loaded_props = run_path(
                    join(params_dir, f_name))['properties']
                # Store in a dictionary of dictionaries indexed by component
                # and variable names
                for (comp_name,
                     var_name), mapped_var in loaded_props.iteritems():
                    component_translations[comp_name][var_name] = mapped_var
        return component_translations
