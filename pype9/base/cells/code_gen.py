"""
    This module defines common methods used in simulator specific build modules

    @author Tom Close
"""

##########################################################################
#
#  Copyright 2011 Okinawa Institute of Science and Technology (OIST), Okinawa
#
##########################################################################
from __future__ import absolute_import
import platform
import os
import time
from itertools import chain
from copy import deepcopy
import shutil
from os.path import join
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from itertools import izip
from abc import ABCMeta, abstractmethod
import sympy
from nineml import units
from pype9.exceptions import Pype9BuildError, Pype9RuntimeError
import logging
import pype9.annotations
from pype9.annotations import PYPE9_NS, BUILD_PROPS
from pype9.base.document import read
import tempfile


logger = logging.getLogger('PyPe9')


class BaseCodeGenerator(object):

    __metaclass__ = ABCMeta

    BUILD_MODE_OPTIONS = ['lazy', 'force', 'require', 'build_only',
                          'generate_only']
    BUILD_DIR_DEFAULT = '9build'
    _PARAMS_DIR = 'params'
    _SRC_DIR = 'src'
    _INSTL_DIR = 'install'
    _CMPL_DIR = 'compile'  # Ignored for NEURON but used for NEST
    _BUILT_COMP_CLASS = 'built_component_class.xml'

    # Python functions and annotations to be made available in the templates
    _globals = dict(
        [('len', len), ('izip', izip), ('enumerate', enumerate),
         ('xrange', xrange), ('next', next), ('chain', chain), ('sorted',
         sorted), ('hash', hash), ('deepcopy', deepcopy), ('units', units),
         ('hasattr', hasattr), ('set', set), ('list', list), ('None', None),
         ('sympy', sympy)] +
        [(n, v) for n, v in pype9.annotations.__dict__.iteritems()
         if n != '__builtins__'])

    # Derived classes should provide mapping from 9ml dimensions to default
    # units
    DEFAULT_UNITS = {}

    @abstractmethod
    def generate_source_files(self, dynamics, initial_state, src_dir, name,
                              **kwargs):
        """
        Generates the source files for the relevant simulator
        """
        pass

    def configure_build_files(self, name, src_dir, compile_dir, install_dir,
                              **kwargs):
        """
        Configures the build files before compiling
        """
        pass

    @abstractmethod
    def compile_source_files(self, compile_dir, name, verbose):
        pass

    def generate(self, component_class, name=None, default_properties=None,
                 initial_state=None, install_dir=None, build_dir=None,
                 build_mode='lazy', verbose=True, initial_regime=None,
                 **kwargs):
        """
        Generates and builds the required simulator-specific files for a given
        NineML cell class

        `component` [nineml.user.Component]: 9ML component
        `install_dir` [str]: Path to the directory where the NMODL files
                             will be generated and compiled
        `build_dir` [str]: Used to set the default 'install_dir' path
        `build_mode` [str]: Available build options:
                            lazy - only build if files are modified
                            force - always build from scratch
                            require - require built binaries are present
                            build_only - build and then quit
                            generate_only - generate src and then quit
                            recompile - don't generate src but compile
        `verbose` [bool]: Whether the build output is shown or not
        `kwargs` [dict]: A dictionary of (potentially simulator-
                                specific) template arguments
        """
        # Set build properties
        for k, v in kwargs.iteritems():
            component_class.annotations.set(PYPE9_NS, BUILD_PROPS, k, v)
        # Save original working directory to reinstate it afterwards (just to
        # be polite)
        orig_dir = os.getcwd()
        if name is None:
            name = component_class.name
        # Set build dir if not provided
        if build_dir is None:
            if component_class.url is None:
                build_dir = tempfile.mkdtemp()
                logger.info("Building '{}' component in temporary directory "
                            "'{}'".format(name, build_dir))
            else:
                build_dir = self.get_build_dir(component_class.url, name)
                logger.info("Building '{}' component in '{}' directory"
                            .format(name, build_dir))
        # Calculate src directory path within build directory
        src_dir = os.path.abspath(os.path.join(build_dir, self._SRC_DIR))
        # Calculate compile directory path within build directory
        compile_dir = self.get_compile_dir(build_dir)
        # Calculate install directory path within build directory if not
        # provided
        install_dir = self.get_install_dir(build_dir, install_dir)
        # Path of the build component class
        built_comp_class_pth = os.path.join(src_dir, self._BUILT_COMP_CLASS)
        # Determine whether the installation needs rebuilding or whether there
        # is an existing library module to use.
        if build_mode in ('force', 'build_only'):  # Force build
            generate_source = compile_source = True
        elif build_mode == 'require':  # Just check that prebuild is present
            generate_source = compile_source = False
        elif build_mode == 'generate_only':  # Only generate
            generate_source = True
            compile_source = False
        elif build_mode == 'lazy':  # Generate if source has been modified
            compile_source = True
            if not os.path.exists(built_comp_class_pth):
                generate_source = True
            else:
                built_component_class = read(
                    built_comp_class_pth, annotations_ns=[PYPE9_NS])[name]
                if built_component_class.equals(component_class,
                                                annotations_ns=[PYPE9_NS]):
                    generate_source = False
                    logger.info("Found existing build in '{}' directory, "
                                "code generation skipped (set 'build_mode' "
                                "argument to 'force' or 'build_only' to "
                                "enforce regeneration)".format(build_dir))
                else:
                    generate_source = True
                    logger.info("Found existing build in '{}' directory, "
                                "but the component classes differ so "
                                "regenerating sources".format(build_dir))
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
        # FIXME: The 'initial_regime' argument will no longer necessary
        #        when it is incorporated into the initial_state object.
        #        If initial_regime is not specified pick the regime with
        #        the most time derivatives to avoid refractory regimes.
        #        Sorry if this seems hacky, it will be fixed soon.
        if initial_regime is not None:
            self._check_initial_regime(component_class, initial_regime)
        else:
            max_num_tds = 0
            for regime in component_class.regimes:
                if initial_regime is None or (regime.num_time_derivatives >
                                              max_num_tds):
                    initial_regime = regime.name
        # Generate source files from NineML code
        if generate_source:
            self.clean_src_dir(src_dir, name)
            self.generate_source_files(
                name=name,
                component_class=component_class,
                default_properties=default_properties,
                initial_state=initial_state,
                src_dir=src_dir, compile_dir=compile_dir,
                install_dir=install_dir, verbose=verbose,
                initial_regime=initial_regime, **kwargs)
            component_class.write(built_comp_class_pth)
        if compile_source:
            # Clean existing compile & install directories from previous builds
            if generate_source:
                self.clean_compile_dir(compile_dir)
                self.configure_build_files(
                    name=name, src_dir=src_dir, compile_dir=compile_dir,
                    install_dir=install_dir, **kwargs)
                self.clean_install_dir(install_dir)
            self.compile_source_files(compile_dir, name, verbose=verbose)
        # Switch back to original dir
        os.chdir(orig_dir)
        return install_dir

    def get_build_dir(self, url, name, group=''):
        return os.path.abspath(os.path.join(
            os.path.dirname(url), self.BUILD_DIR_DEFAULT,
            self.SIMULATOR_NAME, group, name))

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

    def render_to_file(self, template, args, filename, directory, switches={},
                       post_hoc_subs={}):
        # Initialise the template loader to include the flag directories
        template_paths = [
            self.BASE_TMPL_PATH,
            os.path.join(self.BASE_TMPL_PATH, 'includes')]
        # Add include paths for various switches (e.g. solver type)
        for name, value in switches.iteritems():
            if value is not None:
                template_paths.append(os.path.join(self.BASE_TMPL_PATH,
                                                   'includes', name, value))
        # Add default path for template includes
        template_paths.append(
            os.path.join(self.BASE_TMPL_PATH, 'includes', 'default'))
        # Initialise the Jinja2 environment
        jinja_env = Environment(loader=FileSystemLoader(template_paths),
                                trim_blocks=True, lstrip_blocks=True,
                                undefined=StrictUndefined)
        # Add some globals used by the template code
        jinja_env.globals.update(**self._globals)
        # Actually render the contents
        contents = jinja_env.get_template(template).render(**args)
        for old, new in post_hoc_subs.iteritems():
            contents = contents.replace(old, new)
        # Write the contents to file
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

    def transform_for_build(self, name, component_class, default_properties,
                            initial_state, **kwargs):  # @UnusedVariable
        """
        Copies and transforms the component class and associated properties and
        states to match the format of the simulator (overridden in derived
        class)

        Parameters
        ----------
        name : str
            The name of the transformed component class
        component_class : nineml.Dynamics
            The component class to be transformed
        default_properties : nineml.DynamicsProperties
            The properties to be transformed to match
        initial_states : dict[str, nineml.Quantity]
            The initial_states to be transformed to match
        """
        # ---------------------------------------------------------------------
        # Clone original component class and properties
        # ---------------------------------------------------------------------
        component_class = component_class.clone()
        component_class.name = name
        default_properties = (default_properties.clone()
                              if default_properties is not None else None)
        if initial_state is not None:
            initial_state = dict(
                (n, v.clone()) for n, v in initial_state.iteritems())
        else:
            initial_state = None
        return component_class, default_properties, initial_state

    @classmethod
    def get_mod_time(cls, url):
        if url is None:
            mod_time = time.ctime(0)  # Return the earliest date if no url
        else:
            mod_time = time.ctime(os.path.getmtime(url))
        return mod_time

    @classmethod
    def _check_initial_regime(cls, component_class, initial_regime):
        if (initial_regime and
                initial_regime not in component_class.regime_names):
            raise Pype9RuntimeError(
                "Initial regime '{}' does not refer to a regime in the given "
                "component class '{}'"
                .format(initial_regime,
                        "', '".join(component_class.regime_names)))
