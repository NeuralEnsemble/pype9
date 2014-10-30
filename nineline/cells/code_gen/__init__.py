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
import time
import shutil
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
    _9ML_MOD_TIME_FILE = 'source_modification_time'

    def __init__(self):
        # Initialise the Jinja2 environment
        self.jinja_env = Environment(loader=FileSystemLoader(self._TMPL_PATH),
                                     trim_blocks=True,
                                     undefined=StrictUndefined)
        # Add some globals used by the template code
        self.jinja_env.globals.update(izip=izip, enumerate=enumerate)

    def generate(self, celltype_name, nineml_path, install_dir=None,
                 build_parent_dir=None, method=None,
                 build_mode='lazy', silent_build=False):
        """
        Generates and builds the required NMODL files for a given NCML cell
        class

        @param celltype_name [str]: Name of the celltype to be built
        @param nineml_path [str]: Path to the NCML file from which the NMODL
                                  files will be compiled and built
        @param install_dir [str]: Path to the directory where the NMODL files
                                  will be generated and compiled
        @param build_parent_dir [str]: Used to set the default 'install_dir'
                                       path
        @param method [str]: The method option to be passed to the NeMo
                             interpreter command
        @param build_mode [str]: Available build options:
                                  lazy - only build if files are modified
                                  force - always build from scratch
                                  build_only - build and then quit
                                  require - require built binaries are present
                                  compile_only - don't generate src but compile
        @param kinetics [list(str)]: A list of ionic components to be generated
                                     using the kinetics option
        """
        # Set default solver if not provided with default for simulator target.
        if not method:
            method = self._DEFAULT_SOLVER
        # Save original working directory to reinstate it afterwards (just to
        # be polite)
        orig_dir = os.getcwd()
        # Determine the paths for the src, build and install directories
        (default_install_dir, params_dir,
         src_dir, compile_dir) = self._get_build_paths(nineml_path,
                                                       celltype_name,
                                                       self.SIMULATOR_NAME,
                                                       build_parent_dir)
        if not install_dir:
            install_dir = default_install_dir
        # Get the timestamp of the source file
        nineml_mod_time = time.ctime(os.path.getmtime(nineml_path))
        # Path of the file which contains the source modification timestamp
        nineml_mod_time_path = os.path.join(src_dir, self._9ML_MOD_TIME_FILE)
        # Determine whether the installation needs rebuilding or whether there
        # is an existing library module to use.
        if build_mode == 'require':
            generate_source = compile_source = False
        elif build_mode == 'compile_only':
            generate_source = False
            compile_source = True
        elif build_mode in ('force', 'build_only'):
            generate_source = compile_source = True
        elif build_mode == 'lazy':
            if os.path.exists(nineml_mod_time_path):
                with open(nineml_mod_time_path) as f:
                    prev_mod_time = f.readline()
                    # If the time of modification matches the time of the
                    # previous build we don't need to rebuild
                    matching_time = (nineml_mod_time == prev_mod_time)
                    generate_source = compile_source = not matching_time
        # Check if required directories are present depending on build_mode
        if build_mode == 'require':
            if (not os.path.exists(install_dir) or
                not os.path.exists(params_dir)):
                raise Exception("Prebuilt installation directory '{install}'"
                                "and/or python parameters directory '{params}'"
                                "are not present, which are required for "
                                "'require' build option"
                                .format(install=install_dir,
                                        params=params_dir))
        elif build_mode == 'complile_only':
            if not os.path.exists(src_dir):
                raise Exception("Source directory '{src}' is not present, "
                                "which is required for 'compile_only' build "
                                "option".format(src=src_dir))
        # Generate source files from NineML code
        if generate_source:
            # Clean existing src directories from previous builds.
            shutil.rmtree(src_dir, ignore_errors=True)
            try:
                os.makedirs(src_dir)
            except IOError as e:
                raise Exception("Could not create build directory ({}), please"
                                " check the required permissions or specify a "
                                "different \"parent build directory\" "
                                "('parent_build_dir') -> {}".format(e))
            # Generate source files
            self.generate_source_files(nineml_path, src_dir, ode_method=method)
            # Write the timestamp of the 9ML file used to generate the source
            # files
            with open(nineml_mod_time_path, 'w') as f:
                f.write(nineml_mod_time)
        if compile_source:
            # Clean existing compile & install directories from previous builds
            shutil.rmtree(compile_dir, ignore_errors=True)
            shutil.rmtree(install_dir, ignore_errors=True)
            try:
                os.makedirs(compile_dir)
                os.makedirs(install_dir)
            except IOError as e:
                raise Exception("Could not create build directory ({}), please"
                                " check the required permissions or specify a "
                                "different \"parent build directory\" "
                                "('parent_build_dir') -> {}".format(e))
            # Compile source files
            self.compile_source_files(src_dir, install_dir, compile_dir,
                                      silent=silent_build)
        # Switch back to original dir
        os.chdir(orig_dir)
        return install_dir

    def _render_to_file(self, template, args, filename, directory):
        contents = self.jinja_env.get_template(template).render(**args)
        with open(os.path.join(directory, filename), 'w') as f:
            f.write(contents)

    def _get_build_paths(self, nineml_path, celltype_name,
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
                                            self.SIMULATOR_NAME,
                                            celltype_name))
        src_dir = str(abspath(join(build_parent_dir, self._SRC_DIR)))
        default_install_dir = str(abspath(join(build_parent_dir,
                                               self._INSTALL_DIR)))
        compile_dir = str(abspath(join(build_parent_dir, self._COMPILE_DIR)))
        params_dir = str(abspath(join(build_parent_dir, self._PARAMS_DIR)))
        return (default_install_dir, params_dir, src_dir, compile_dir)

    @classmethod
    def _path_to_exec(cls, exec_name):
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
