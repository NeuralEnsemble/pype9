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
from itertools import chain
import shutil
from os.path import join
from collections import defaultdict
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from itertools import izip
from runpy import run_path
from abc import ABCMeta, abstractmethod
import nineml
from pype9.exceptions import Pype9BuildError


class BaseCodeGenerator(object):

    __metaclass__ = ABCMeta

    BUILD_MODE_OPTIONS = ['lazy', 'force', 'require', 'build_only',
                          'generate_only', 'compile_only']
    BUILD_DIR_DEFAULT = '9build'
    _PARAMS_DIR = 'params'
    _SRC_DIR = 'src'
    _INSTL_DIR = 'install'
    _CMPL_DIR = 'compile'  # Ignored for NEURON but used for NEST
    _9ML_MOD_TIME_FILE = 'source_modification_time'

    # Derived classes should provide mapping from 9ml dimensions to default
    # units
    DEFAULT_UNITS = {}

    # Abstract methods that are required in the derived classes

    def __init__(self):
        # Initialise the Jinja2 environment
        self.jinja_env = Environment(loader=FileSystemLoader(self._TMPL_PATH),
                                     trim_blocks=True, lstrip_blocks=True,
                                     undefined=StrictUndefined)
        # Add some globals used by the template code
        self.jinja_env.globals.update(len=len, izip=izip, enumerate=enumerate,
                                      xrange=xrange, next=next, chain=chain,
                                      hash=hash)

    @abstractmethod
    def generate_source_files(self, component, initial_state, src_dir,
                              **kwargs):
        """
        Generates the source files for the relevant simulator
        """
        pass

    @abstractmethod
    def configure_build_files(self, model_name, src_dir, compile_dir,
                               install_dir):
        """
        Configures the build files before compiling
        """
        pass

    @abstractmethod
    def compile_source_files(self, compile_dir, component_name, verbose):
        pass

    def generate(self, component, initial_state=None, install_dir=None,
                 build_dir=None, build_mode='lazy', verbose=True,
                 **kwargs):
        """
        Generates and builds the required simulator-specific files for a given
        NineML cell class

        `component` [nineml.user_layer.Component]: 9ML component
        `install_dir` [str]: Path to the directory where the NMODL files
                             will be generated and compiled
        `build_dir` [str]: Used to set the default 'install_dir' path
        `build_mode` [str]: Available build options:
                            lazy - only build if files are modified
                            force - always build from scratch
                            require - require built binaries are present
                            build_only - build and then quit
                            generate_only - generate src and then quit
                            compile_only - don't generate src but compile
        `verbose` [bool]: Whether the build output is shown or not
        `kwargs` [dict]: A dictionary of (potentially simulator-
                                specific) template arguments
        """
        # Save original working directory to reinstate it afterwards (just to
        # be polite)
        orig_dir = os.getcwd()
        # Get component from file if passed as a string
        if isinstance(component, str):
            # Interpret the given component as a URL of a NineML component
            component_src_path = component
            # Read NineML description
            context = nineml.read(component_src_path)
            components = list(context.components)
            if len(components) == 0:
                raise Pype9BuildError(
                    "No components loaded from nineml path '{}'"
                    .format(component_src_path))
            elif len(components) > 1:
                raise Pype9BuildError(
                    "Multiple components ('{}') loaded from nineml path '{}'"
                    .format("', '".join(c.name for c in context.components),
                            component_src_path))
            component = components[0]
        else:
            component_src_path = None
        # Get initial_state from file if passed as a string
        if isinstance(component, str):
            # Interpret the given component as a URL of a NineML component
            state_src_path = component
            # Read NineML description
            # initial_states = parse_9ml(state_src_path)
            initial_states = [0.0]  # TODO: Write nineml lib for state layer
            if not initial_states:
                raise Pype9BuildError(
                    "No initial_states loaded from nineml path '{}'"
                    .format(state_src_path))
            elif len(initial_states) > 1:
                raise Pype9BuildError(
                    "Multiple initial states ('{}') loaded from nineml path "
                    "'{}'".format("', '".join(s.name for s in initial_states),
                                  state_src_path))
            else:
                initial_state = initial_states[0]
        else:
            state_src_path = None
        # Set build dir if not provided
        if not build_dir:
            if not component_src_path:
                raise Pype9BuildError(
                    "Build directory must be explicitly provided ('build_dir')"
                    " when using 9ml component already in memory")
            build_dir = os.path.abspath(os.path.join(
                os.path.dirname(component_src_path),
                self.BUILD_DIR_DEFAULT,
                self.SIMULATOR_NAME,
                component.name))
        # Calculate src directory path within build directory
        src_dir = os.path.abspath(os.path.join(build_dir, self._SRC_DIR))
        # Calculate compile directory path within build directory
        compile_dir = self.get_compile_dir(build_dir)
        # Calculate install directory path within build directory if not
        # provided
        install_dir = self.get_install_dir(build_dir, install_dir)
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
        if build_mode in ('force', 'build_only'):  # Force build
            generate_source = compile_source = True
        elif build_mode == 'require':  # Just check that prebuild is present
            generate_source = compile_source = False
        elif build_mode == 'compile_only':  # Don't regenerate, just compile
            if not os.path.exists(src_dir):
                raise Pype9BuildError(
                    "Source directory '{src}' is not present, which is "
                    "required for 'compile_only' build " "option"
                    .format(src=src_dir))
            generate_source = False
            compile_source = True
        elif build_mode == 'generate_only':  # Only generate
            generate_source = True
            compile_source = False
        elif build_mode == 'lazy':  # Generate if source has been modified
            generate_source = compile_source = True
            if os.path.exists(nineml_mod_time_path):
                with open(nineml_mod_time_path) as f:
                    prev_mod_time = f.readline()
                    # If the time of modification matches the time of the
                    # previous build we don't need to rebuild
                    if nineml_mod_time == prev_mod_time:
                        generate_source = compile_source = False
                        if verbose:
                            print ("Found existing build in '{}' directory, "
                                   "code generation skipped (set 'build_mode' "
                                   "argument to 'force' or 'build_only' to "
                                   "enforce regeneration".format(build_dir))
        # Check if required directories are present depending on build_mode
        elif build_mode == 'require':
            if not os.path.exists(install_dir):
                raise Pype9BuildError(
                    "Prebuilt installation directory '{install}' is not "
                    "present, and is required for  'require' build option"
                    .format(install=install_dir))
        else:
            raise Pype9BuildError(
                "Unrecognised build option '{}', must be one of ('{}')"
                .format(build_mode, "', '".join(self.BUILD_MODE_OPTIONS)))
        # Generate source files from NineML code
        if generate_source:
            self.clean_src_dir(src_dir, component.name)
            self.generate_source_files(
                component=component, initial_state=initial_state,
                src_dir=src_dir, compile_dir=compile_dir,
                install_dir=install_dir, verbose=verbose, **kwargs)
            # Write the timestamp of the 9ML file used to generate the source
            # files
            with open(nineml_mod_time_path, 'w') as f:
                f.write(nineml_mod_time)
        if compile_source:
            # Clean existing compile & install directories from previous builds
            self.clean_compile_dir(compile_dir)
            self.configure_build_files(
                component=component.name, src_dir=src_dir,
                compile_dir=compile_dir, install_dir=install_dir)
            self.clean_install_dir(install_dir)
            # Compile source files
            self.compile_source_files(compile_dir, component.name,
                                      verbose=verbose)
        # Switch back to original dir
        os.chdir(orig_dir)
        return install_dir

    def unit_conversion(self, units):
        try:
            default_units = self.DEFAULT_UNITS[units.dimension]
            factor = 10 ** (units.power - default_units.power)
            offset = (default_units.offset - units.offset) * factor
        except KeyError:
            # FIXME: In this case we should try to work out a combination of
            #        equivalent default units (could be a little tricky) or
            #        convert to SI units if unit is not covered by simulator.
            factor = 1.0
            offset = 0.0
        return (factor, offset)

    def get_install_dir(self, build_dir, install_dir):
        """
        The install dir is determined within a method so that derrived classes
        (namely neuron.CodeGenerator) can override the provided install
        directory if provided if it needs to be in a special place.
        """
        if not install_dir:
            install_dir = os.path.abspath(os.path.join(build_dir,
                                                       self._INSTL_DIR))
        return install_dir

    def get_compile_dir(self, build_dir):
        return os.path.abspath(os.path.join(build_dir, self._CMPL_DIR))

    def clean_src_dir(self, src_dir, component_name):  # @UnusedVariable
        # Clean existing src directories from previous builds.
        shutil.rmtree(src_dir, ignore_errors=True)
        try:
            os.makedirs(src_dir)
        except IOError as e:
            raise Pype9BuildError(
                "Could not create build directory ({}), please check the "
                "required permissions or specify a different \"parent build "
                "directory\" ('parent_build_dir') -> {}".format(e))

    def clean_compile_dir(self, compile_dir):
        # Clean existing compile & install directories from previous builds
        shutil.rmtree(compile_dir, ignore_errors=True)
        try:
            os.makedirs(compile_dir)
        except IOError as e:
            raise Pype9BuildError(
                "Could not create build directory ({}), please check the "
                "required permissions or specify a different \"parent build "
                "directory\" ('parent_build_dir') -> {}".format(e))

    def clean_install_dir(self, install_dir):
        # Clean existing compile & install directories from previous builds
        shutil.rmtree(install_dir, ignore_errors=True)
        try:
            os.makedirs(install_dir)
        except IOError as e:
            raise Pype9BuildError(
                "Could not create build directory ({}), please check the "
                "required permissions or specify a different \"parent build "
                "directory\" ('parent_build_dir') -> {}".format(e))

    def render_to_file(self, template, args, filename, directory):
        contents = self.jinja_env.get_template(template).render(**args)
        with open(os.path.join(directory, filename), 'w') as f:
            f.write(contents)

    def path_to_exec(self, exec_name):
        """
        Returns the full path to an executable by searching the "PATH"
        environment variable

        `exec_name` [str] -- Name of executable to search the execution path
        return [str] -- Full path to executable
        """
        if platform.system() == 'Windows':
            exec_name += '.exe'
        # Get the system path
        system_path = os.environ['PATH'].split(os.pathsep)
        # Append NEST_INSTALL_DIR/NRNHOME if present
        system_path.extend(self.simulator_specific_paths())
        # Check the system path for the command
        exec_path = None
        for dr in system_path:
            path = join(dr, exec_name)
            if os.path.exists(path):
                exec_path = path
                break
        if not exec_path:
            raise Pype9BuildError(
                "Could not find executable '{}' on the system path '{}'"
                .format(exec_name, ':'.join(system_path)))
        return exec_path

    def simulator_specific_paths(self):
        """
        To be overridden by derived classes if required.
        """
        return []

    def _load_component_translations(self, biophysics_name, params_dir):
        """
        Loads component parameter translations from names to standard reference
        name (eg. 'e_rev', 'MaximalConductance') dictionary. For each file in
        the params directory with a '.py' extension starting with the
        celltype_name assume that it is a parameters file.

        `biophysics_name` [str] -- The name of the cell biophysics to load
                                      the parameter names for
        `params_dir` [str] -- The path to the directory that contains the
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
