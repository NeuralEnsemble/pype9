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
from builtins import object
from future.utils import PY3
import platform
import os
import subprocess as sp
import time
from itertools import chain
from copy import deepcopy
import shutil
from os.path import join
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from future.utils import with_metaclass
from abc import ABCMeta, abstractmethod
import sympy
from nineml import units
from nineml.exceptions import NineMLNameError, NineMLSerializationError
from pype9.exceptions import (
    Pype9BuildError, Pype9CommandNotFoundError, Pype9RuntimeError)
from ..cells.with_synapses import read
import pype9.annotations
from pype9.annotations import PYPE9_NS, BUILD_PROPS
from os.path import expanduser
import re
from nineml.serialization import url_re
import sysconfig
from pype9 import __version__
from pype9.utils.paths import remove_ignore_missing
from pype9.utils.logging import logger

BASE_BUILD_DIR = os.path.join(
    expanduser("~"),
    '.pype9',
    'build',
    'v{}'.format(__version__),
    'python{}'.format(sysconfig.get_config_var('py_version')))


class BaseCodeGenerator(with_metaclass(ABCMeta, object)):
    """
    Parameters
    ----------
        base_dir : str | None
            The base directory for the generated code. If None a directory
            will be created in user's home directory.
    """

    BUILD_MODE_OPTIONS = ['lazy',  # Build iff source has been updated
                          'force',  # Build always
                          'require',  # Don't build, requires pre-built
                          'build_only',  # Only build
                          'generate_only',  # Only generate source files
                          'purge'  # Remove all configure files and rebuild
                          ]

    _PARAMS_DIR = 'params'
    _SRC_DIR = 'src'
    _INSTL_DIR = 'install'
    _CMPL_DIR = 'compile'  # Ignored for NEURON but used for NEST
    _BUILT_COMP_CLASS = 'built_component_class.xml'

    # Python functions and annotations to be made available in the templates
    _globals = dict(
        [('len', len), ('zip', zip), ('enumerate', enumerate),
         ('range', range), ('next', next), ('chain', chain), ('sorted',
         sorted), ('hash', hash), ('deepcopy', deepcopy), ('units', units),
         ('hasattr', hasattr), ('set', set), ('list', list), ('None', None),
         ('sympy', sympy)] +
        [(n, v) for n, v in list(pype9.annotations.__dict__.items())
         if n != '__builtins__'])

    # Derived classes should provide mapping from 9ml dimensions to default
    # units
    DEFAULT_UNITS = {}

    def __init__(self, base_dir=None, **kwargs):  # @UnusedVariable
        if base_dir is None:
            base_dir = BASE_BUILD_DIR
        self._base_dir = os.path.join(
            base_dir, self.SIMULATOR_NAME + self.SIMULATOR_VERSION)

    def __repr__(self):
        return "{}CodeGenerator(base_dir='{}')".format(
            self.SIMULATOR_NAME.capitalize(), self.base_dir)

    def __eq__(self, other):
        try:
            return (self.SIMULATOR_NAME == other.SIMULATOR_NAME and
                    self.base_dir == other.base_dir)
        except AttributeError:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def base_dir(self):
        return self._base_dir

    @abstractmethod
    def generate_source_files(self, dynamics, src_dir, name, **kwargs):
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
    def compile_source_files(self, compile_dir, name):
        pass

    def generate(self, component_class, build_mode='lazy', url=None, **kwargs):
        """
        Generates and builds the required simulator-specific files for a given
        NineML cell class

        Parameters
        ----------
        component_class : nineml.Dynamics
            9ML Dynamics object
        name : str
            Name of the generated cell class
        install_dir : str
            Path to the directory where the NMODL files
            will be generated and compiled
        build_mode : str
            Available build options:
                lazy - only build if files are modified
                force - always generate and build
                purge - remove all config files, generate and rebuild
                require - require built binaries are present
                build_only - build and then quit
                generate_only - generate src and then quit
                recompile - don't generate src but compile
        build_version : str
            A suffix appended to the cell build name to distinguish
            it from other code generated from the component class
        url : str
            The URL where the component class is stored (used to form the
            build path)
        kwargs : dict
            A dictionary of (potentially simulator- specific) template
            arguments
        """
        # Save original working directory to reinstate it afterwards (just to
        # be polite)
        name = component_class.name
        orig_dir = os.getcwd()
        if url is None:
            url = component_class.url
        # Calculate compile directory path within build directory
        src_dir = self.get_source_dir(name, url)
        compile_dir = self.get_compile_dir(name, url)
        install_dir = self.get_install_dir(name, url)
        # Path of the build component class
        built_comp_class_pth = os.path.join(src_dir, self._BUILT_COMP_CLASS)
        # Determine whether the installation needs rebuilding or whether there
        # is an existing library module to use.
        if build_mode == 'purge':
            remove_ignore_missing(src_dir)
            remove_ignore_missing(install_dir)
            remove_ignore_missing(compile_dir)
            generate_source = compile_source = True
        elif build_mode in ('force', 'build_only'):  # Force build
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
                try:
                    built_component_class = read(built_comp_class_pth)[name]
                    if built_component_class.equals(component_class,
                                                    annotations_ns=[PYPE9_NS]):
                        generate_source = False
                        logger.info("Found existing source in '{}' directory, "
                                    "code generation skipped (set 'build_mode'"
                                    " argument to 'force' or 'build_only' to "
                                    "enforce regeneration)".format(src_dir))
                    else:
                        generate_source = True
                        logger.info("Found existing source in '{}' directory, "
                                    "but the component classes differ so "
                                    "regenerating sources".format(src_dir))
                except (NineMLNameError, NineMLSerializationError):
                    generate_source = True
                    logger.info("Found existing source in '{}' directory, "
                                "but could not find '{}' component class so "
                                "regenerating sources".format(name, src_dir))
        # Check if required directories are present depending on build_mode
        elif build_mode == 'require':
            if not os.path.exists(install_dir):
                raise Pype9BuildError(
                    "Prebuilt installation directory '{}' is not "
                    "present, and is required for  'require' build option"
                    .format(install_dir))
        else:
            raise Pype9BuildError(
                "Unrecognised build option '{}', must be one of ('{}')"
                .format(build_mode, "', '".join(self.BUILD_MODE_OPTIONS)))
        # Generate source files from NineML code
        if generate_source:
            self.clean_src_dir(src_dir, name)
            self.generate_source_files(
                name=name,
                component_class=component_class,
                src_dir=src_dir,
                compile_dir=compile_dir,
                install_dir=install_dir,
                **kwargs)
            component_class.write(built_comp_class_pth,
                                  preserve_order=True, version=2.0)
        if compile_source:
            # Clean existing compile & install directories from previous builds
            if generate_source:
                self.clean_compile_dir(compile_dir,
                                       purge=(build_mode == 'purge'))
                self.configure_build_files(
                    name=name, src_dir=src_dir, compile_dir=compile_dir,
                    install_dir=install_dir, **kwargs)
                self.clean_install_dir(install_dir)
            self.compile_source_files(compile_dir, name)
        # Switch back to original dir
        os.chdir(orig_dir)
        # Cache any dimension maps that were calculated during the generation
        # process
        return install_dir

    def get_build_dir(self, name, url):
        return os.path.join(self.base_dir, self.url_build_path(url), name)

    def get_source_dir(self, name, url):
        return os.path.abspath(os.path.join(
            self.get_build_dir(name, url), self._SRC_DIR))

    def get_compile_dir(self, name, url):
        return os.path.abspath(os.path.join(
            self.get_build_dir(name, url), self._CMPL_DIR))

    def get_install_dir(self, name, url):
        return os.path.abspath(os.path.join(
            self.get_build_dir(name, url), self._INSTL_DIR))

    def clean_src_dir(self, src_dir, component_name):  # @UnusedVariable
        # Clean existing src directories from previous builds.
        shutil.rmtree(src_dir, ignore_errors=True)
        try:
            os.makedirs(src_dir)
        except OSError as e:
            raise Pype9BuildError(
                "Could not create source directory ({}), please check the "
                "required permissions or specify a different \"build dir"
                "base\" ('build_dir_base'):\n{}".format(src_dir, e))

    def clean_compile_dir(self, compile_dir, purge=False):  # @UnusedVariable
        # Clean existing compile & install directories from previous builds
        shutil.rmtree(compile_dir, ignore_errors=True)
        try:
            os.makedirs(compile_dir)
        except OSError as e:
            raise Pype9BuildError(
                "Could not create compile directory ({}), please check the "
                "required permissions or specify a different \"build dir"
                "base\" ('build_dir_base'):\n{}".format(compile_dir, e))

    def clean_install_dir(self, install_dir):
        # Clean existing compile & install directories from previous builds
        shutil.rmtree(install_dir, ignore_errors=True)
        try:
            os.makedirs(install_dir)
        except OSError as e:
            raise Pype9BuildError(
                "Could not create install directory ({}), please check the "
                "required permissions or specify a different \"build dir"
                "base\" ('build_dir_base'):\n{}".format(install_dir, e))

    def render_to_file(self, template, args, filename, directory, switches={},
                       post_hoc_subs={}):
        # Initialise the template loader to include the flag directories
        template_paths = [
            self.BASE_TMPL_PATH,
            os.path.join(self.BASE_TMPL_PATH, 'includes')]
        # Add include paths for various switches (e.g. solver type)
        for name, value in list(switches.items()):
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
        for old, new in list(post_hoc_subs.items()):
            contents = contents.replace(old, new)
        # Write the contents to file
        with open(os.path.join(directory, filename), 'w') as f:
            f.write(contents)

    def path_to_utility(self, utility_name, env_var='', **kwargs):  # @UnusedVariable @IgnorePep8
        """
        Returns the full path to an executable by searching the "PATH"
        environment variable

        Parameters
        ----------
        utility_name : str
            Name of executable to search the execution path
        env_var : str
            Name of a environment variable to lookup first before searching
            path
        default : str | None
            The default value to assign to the path if it cannot be found.

        Returns
        -------
        utility_path : str
            Full path to executable
        """
        if kwargs and list(kwargs) != ['default']:
            raise Pype9RuntimeError(
                "Should only provide 'default' as kwarg to path_to_utility "
                "provided ({})".format(kwargs))
        try:
            utility_path = os.environ[env_var]
        except KeyError:
            if platform.system() == 'Windows':
                utility_name += '.exe'
            # Get the system path
            system_path = os.environ['PATH'].split(os.pathsep)
            # Append NEST_INSTALL_DIR/NRNHOME if present
            system_path.extend(self.simulator_specific_paths())
            # Check the system path for the command
            utility_path = None
            for dr in system_path:
                path = join(dr, utility_name)
                if os.path.exists(path):
                    utility_path = path
                    break
            if not utility_path:
                try:
                    utility_path = kwargs['default']
                except KeyError:
                    raise Pype9CommandNotFoundError(
                        "Could not find executable '{}' on the system path "
                        "'{}'".format(utility_name, ':'.join(system_path)))
        else:
            if not os.path.exists(utility_path):
                raise Pype9CommandNotFoundError(
                    "Could not find executable '{}' at path '{}' provided by "
                    "'{}' environment variable"
                    .format(utility_name, env_var))
        return utility_path

    def simulator_specific_paths(self):
        """
        To be overridden by derived classes if required.
        """
        return []

    def transform_for_build(self, name, component_class, **kwargs):  # @UnusedVariable @IgnorePep8
        """
        Copies and transforms the component class to match the format of the
        simulator (overridden in derived class)

        Parameters
        ----------
        name : str
            The name of the transformed component class
        component_class : nineml.Dynamics
            The component class to be transformed
        """
        # ---------------------------------------------------------------------
        # Clone original component class and properties
        # ---------------------------------------------------------------------
        component_class = component_class.clone()
        component_class.name = name
        self._set_build_props(component_class, **kwargs)
        return component_class

    def _set_build_props(self, component_class, **build_props):
        """
        Sets the build properties in the component class annotations

        Parameters
        ----------
        component_class : Dynamics | MultiDynamics
            The build component class
        build_props : dict(str, str)
            Build properties to save into the annotations of the build
            component class
        """
        for k, v in list(build_props.items()) + [
                ('version', pype9.__version__)]:
            component_class.annotations.set((BUILD_PROPS, PYPE9_NS), k, v)

    def run_command(self, cmd, fail_msg=None, **kwargs):
        env = os.environ.copy()
        try:
            process = sp.Popen(cmd, stdout=sp.PIPE,
                               stderr=sp.PIPE, env=env, **kwargs)
            stdout, stderr = process.communicate()
            if PY3:
                stdout = str(stdout.decode('utf-8'))
                stderr = str(stderr.decode('utf-8'))
            logger.debug("'{}' stdout:\n{}".format(cmd, stdout))
            logger.debug("'{}' stderr:\n{}".format(cmd, stderr))
        except sp.CalledProcessError as e:
            if fail_msg is None:
                raise
            else:
                msg = fail_msg.format(e)
                raise Pype9BuildError(msg)
        return stdout, stderr

    @classmethod
    def get_mod_time(cls, url):
        if url is None:
            mod_time = time.ctime(0)  # Return the earliest date if no url
        else:
            mod_time = time.ctime(os.path.getmtime(url))
        return mod_time

    @classmethod
    def url_build_path(cls, url):
        if url is None:
            path = 'generated'
        else:
            if url_re.match(url) is not None:
                path = os.path.join(
                    'url',
                    re.match(r'(:?\w+://)?([\.\/\w]+).*', url).group(1))
            else:
                path = os.path.join('file', os.path.realpath(url)[1:])
        return path

    def load_libraries(self, name, url, **kwargs):
        """
        To be overridden by derived classes to allow the model to be loaded
        from compiled external libraries
        """
        pass
