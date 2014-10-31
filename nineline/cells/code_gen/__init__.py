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
from abc import ABCMeta, abstractmethod
from nineml.abstraction_layer.dynamics.readers import XMLReader as NineMLReader


class BaseCodeGenerator(object):

    __metaclass__ = ABCMeta

    BUILD_MODE_OPTIONS = ['lazy', 'force', 'build_only', 'require',
                          'compile_only']
    _DEFAULT_BUILD_DIR = '.9build'
    _PARAMS_DIR = 'params'
    _SRC_DIR = 'src'
    _INSTL_DIR = 'install'
    _CMPL_DIR = 'compile'  # Ignored for NEURON but used for NEST
    _9ML_MOD_TIME_FILE = 'source_modification_time'

    # Abstract methods that are required in the derived classes

    @abstractmethod
    def _extract_template_args(self, component, initial_state, ode_method):
        """
        Extracts the required information from the 9ML model into a dictionary
        containing the relevant arguments for the Jinja2 templates.
        """
        pass

    @abstractmethod
    def _render_source_files(self, template_args, src_dir, install_dir):
        pass

    @abstractmethod
    def compile_source_files(self, src_dir, compile_dir, install_dir,
                             component_name, verbose):
        pass

    def __init__(self):
        # Initialise the Jinja2 environment
        self.jinja_env = Environment(loader=FileSystemLoader(self._TMPL_PATH),
                                     trim_blocks=True,
                                     undefined=StrictUndefined)
        # Add some globals used by the template code
        self.jinja_env.globals.update(izip=izip, enumerate=enumerate)

    def generate(self, component, initial_state, install_dir=None,
                 build_dir=None, ode_method=None,
                 build_mode='lazy', verbose=True):
        """
        Generates and builds the required NMODL files for a given NCML cell
        class

        @param celltype_name [str]: Name of the celltype to be built
        @param nineml_path [str]: Path to the NCML file from which the NMODL
                                  files will be compiled and built
        @param install_dir [str]: Path to the directory where the NMODL files
                                  will be generated and compiled
        @param build_dir [str]: Used to set the default 'install_dir'
                                       path
        @param ode_method [str]: The ode_method option to be passed to the NeMo
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
        # Save original working directory to reinstate it afterwards (just to
        # be polite)
        orig_dir = os.getcwd()
        # Get component from file if passed as a string
        if isinstance(component, str):
            #Interpret the given component as a URL of a NineML component
            component_src_path = component
            # Read NineML description
            components = NineMLReader.read_components(component_src_path)
            if not components:
                raise Exception("No components loaded from nineml path '{}'"
                                .format(component_src_path))
            elif len(components) > 1:
                raise Exception("Multiple components ('{}') loaded from nineml"
                                " path '{}'"
                                .format("', '".join(c.name
                                                    for c in components),
                                        component_src_path))
            else:
                component = component[0]
        else:
            component_src_path = None
        # Get initial_state from file if passed as a string
        if isinstance(component, str):
            #Interpret the given component as a URL of a NineML component
            state_src_path = component
            # Read NineML description
            initial_states = NineMLReader.read_components(state_src_path)
            if not initial_states:
                raise Exception("No initial_states loaded from nineml path "
                                "'{}'".format(state_src_path))
            elif len(initial_states) > 1:
                raise Exception("Multiple initial states ('{}') loaded from "
                                " nineml path '{}'"
                                .format("', '".join(s.name
                                                    for s in initial_states),
                                        state_src_path))
            else:
                initial_state = initial_states[0]
        else:
            state_src_path = None
        # Set build dir if not provided
        if not build_dir:
            if not component_src_path:
                raise Exception("Build directory must be explicitly provided "
                                "('build_dir') when using 9ml component "
                                "already in memory")
            build_dir = os.path.abspath(os.path.join(
                                           os.path.dirname(component_src_path),
                                           self._DEFAULT_BUILD_DIR,
                                           self.SIMULATOR_NAME,
                                           component.name))
        # Calculate src directory path within build directory
        src_dir = os.path.abspath(os.path.join(build_dir, self._SRC_DIR))
        # Calculate compile directory path within build directory
        compile_dir = self._get_compile_dir(build_dir)
        # Calculate install directory path within build directory if not
        # provided
        install_dir = self._get_install_dir(build_dir, install_dir)
        # Get the timestamp of the source file
        if component_src_path:
            nineml_mod_time = time.ctime(os.path.getmtime(component_src_path))
        else:
            nineml_mod_time = None
        # Path of the file which contains or will contain the source
        # modification timestamp in the installation directory
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
                    if nineml_mod_time == prev_mod_time:
                        generate_source = compile_source = False
                        if not verbose:
                            print ("Found existing build in '{}' directory, "
                                   "code generation skipped (set 'build_mode' "
                                   "argument to 'force' or 'build_only' to "
                                   "enforce regeneration".format(build_dir))
        # Check if required directories are present depending on build_mode
        if build_mode == 'require':
            if not os.path.exists(install_dir):
                raise Exception("Prebuilt installation directory '{install}'"
                                "is not present, and is required for "
                                "'require' build option"
                                .format(install=install_dir))
        elif build_mode == 'complile_only':
            if not os.path.exists(src_dir):
                raise Exception("Source directory '{src}' is not present, "
                                "which is required for 'compile_only' build "
                                "option".format(src=src_dir))
        # Generate source files from NineML code
        if generate_source:
            self._clean_src_dir(src_dir)
            self.generate_source_files(component, initial_state, src_dir,
                                       install_dir, ode_method, verbose)
            # Write the timestamp of the 9ML file used to generate the source
            # files
            with open(nineml_mod_time_path, 'w') as f:
                f.write(nineml_mod_time)
        if compile_source:
            # Clean existing compile & install directories from previous builds
            self._clean_compile_and_install_dirs(compile_dir, install_dir)
            # Compile source files
            self.compile_source_files(src_dir, install_dir, compile_dir,
                                      verbose=verbose)
        # Switch back to original dir
        os.chdir(orig_dir)
        return install_dir

    def generate_source_files(self, component, initial_state, src_dir,
                              install_dir, ode_method=None, verbose=True):
        """
        Generates the source files for the relevant simulator
        """
        # Set default solver if not provided with default for simulator target.
        if not ode_method:
            ode_method = self._DEFAULT_SOLVER
        # Extract relevant information from 9ml
        # component/class/initial_state
        template_args = self._extract_template_args(component, initial_state,
                                                    ode_method)
        # Render source files
        self._render_source_files(template_args, src_dir, install_dir, verbose)

    def _get_install_dir(self, build_dir, install_dir):
        """
        The install dir is determined within a method so that derrived classes
        (namely neuron.CodeGenerator) can override the provided install
        directory if provided if it needs to be in a special place.
        """
        if not install_dir:
            install_dir = os.path.abspath(os.path.join(build_dir,
                                                       self._INSTL_DIR))
        return install_dir

    def _get_compile_dir(self, build_dir):
        return os.path.abspath(os.path.join(build_dir, self._CMPL_DIR))

    def _render_to_file(self, template, args, filename, directory):
        contents = self.jinja_env.get_template(template).render(**args)
        with open(os.path.join(directory, filename), 'w') as f:
            f.write(contents)

    def _clean_src_dir(self, src_dir, component_name):  # @UnusedVariable
        # Clean existing src directories from previous builds.
        shutil.rmtree(src_dir, ignore_errors=True)
        try:
            os.makedirs(src_dir)
        except IOError as e:
            raise Exception("Could not create build directory ({}), please"
                            " check the required permissions or specify a "
                            "different \"parent build directory\" "
                            "('parent_build_dir') -> {}".format(e))

    def _clean_compile_and_install_dirs(self, compile_dir, install_dir):
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

    @classmethod
    def _path_to_exec(cls, exec_name):
        """
        Returns the full path to an executable by searching the "PATH"
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
