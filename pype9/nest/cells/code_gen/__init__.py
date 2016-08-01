"""

  This module contains functions for building and loading nest modules

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
import os
from os import path
from copy import deepcopy
import subprocess as sp
import re
from pype9.base.cells.code_gen import BaseCodeGenerator
from pype9.utils import remove_ignore_missing
from pype9.exceptions import Pype9BuildError
import pype9
import shutil
from datetime import datetime
from copy import copy
from nineml.user import DynamicsProperties, Definition
from nineml import Document
from pype9.nest.units import UnitHandler
from pype9.exceptions import Pype9RuntimeError


class CodeGenerator(BaseCodeGenerator):

    SIMULATOR_NAME = 'nest'
    ODE_SOLVER_DEFAULT = 'gsl'
    SS_SOLVER_DEFAULT = None
    MAX_STEP_SIZE_DEFAULT = 0.01  # Used for CVODE/IDA, FIXME: not sure best value!!! @IgnorePep8
    ABS_TOLERANCE_DEFAULT = 1e-3
    REL_TOLERANCE_DEFAULT = 0.0
    GSL_JACOBIAN_APPROX_STEP_DEFAULT = 0.01
    V_THRESHOLD_DEFAULT = 0.0
    MAX_SIMULTANEOUS_TRANSITIONS = 1000
    BASE_TMPL_PATH = path.join(path.dirname(__file__), 'templates')

    _inline_random_implementations = {}

    def __init__(self, build_cores=1):
        super(CodeGenerator, self).__init__()
        self._build_cores = build_cores
        nest_config = self.path_to_exec('nest-config')
        compiler = sp.check_output('{} --compiler'.format(nest_config),
                                   shell=True)
        self._compiler = compiler[:-1]  # strip trailing \n

    def generate_source_files(self, component_class, default_properties,
                              initial_state, src_dir, initial_regime,
                              name=None, **kwargs):
        if name is None:
            name = component_class.name
        # Get the initial regime and check that it refers to a regime in the
        # component class
        tmpl_args = {
            'component_name': name,
            'component_class': component_class,
            'prototype': default_properties,
            'initial_state': initial_state,
            'initial_regime': initial_regime,
            'version': pype9.version, 'src_dir': src_dir,
            'timestamp': datetime.now().strftime('%a %d %b %y %I:%M:%S%p'),
            'unit_handler': UnitHandler(component_class),
            'default_regime': kwargs.get('default_regime',
                                         next(component_class.regime_names)),
            'jacobian_approx_step': kwargs.get(
                'jacobian_approx_step', self.GSL_JACOBIAN_APPROX_STEP_DEFAULT),
            'max_step_size': kwargs.get('max_step_size',
                                        self.MAX_STEP_SIZE_DEFAULT),
            'abs_tolerance': kwargs.get('max_step_size',
                                        self.ABS_TOLERANCE_DEFAULT),
            'rel_tolerance': kwargs.get('max_step_size',
                                        self.REL_TOLERANCE_DEFAULT),
            'max_simultaneous_transitions': kwargs.get(
                'max_simultaneous_transitions',
                self.MAX_SIMULTANEOUS_TRANSITIONS),
            'parameter_scales': [],
            'v_threshold': kwargs.get('v_threshold', self.V_THRESHOLD_DEFAULT)}
        ode_solver = kwargs.get('ode_solver', self.ODE_SOLVER_DEFAULT)
        ss_solver = kwargs.get('ss_solver', self.SS_SOLVER_DEFAULT)
        if ode_solver is None:
            raise Pype9BuildError("'ode_solver' cannot be None")
        switches = {'ode_solver': ode_solver, 'ss_solver': ss_solver}
        # Render C++ header file
        self.render_to_file('header.tmpl', tmpl_args,
                             name + '.h', src_dir, switches=switches)
        # Render C++ class file
        self.render_to_file('main.tmpl', tmpl_args, name + '.cpp',
                             src_dir, switches=switches,
                             post_hoc_subs=self._inline_random_implementations)
        # Render Loader header file
        self.render_to_file('module-header.tmpl', tmpl_args,
                             name + 'Module.h', src_dir)
        # Render Loader C++ class
        self.render_to_file('module-cpp.tmpl', tmpl_args,
                             name + 'Module.cpp', src_dir)
        # Render SLI initialiser
        self.render_to_file('module_sli_init.tmpl', tmpl_args,
                             name + 'Module-init.sli',
                             path.join(src_dir, 'sli'))

    def configure_build_files(self, name, src_dir, compile_dir, install_dir,
                              verbose=False, **kwargs):
        # Generate Makefile if it is not present
        if not path.exists(path.join(compile_dir, 'Makefile')):
            if not path.exists(compile_dir):
                os.mkdir(compile_dir)
            if verbose != 'silent':
                print ("Configuring build files in '{}' directory"
                       .format(compile_dir))
            orig_dir = os.getcwd()
            config_args = {'name': name, 'src_dir': src_dir,
                           'ode_solver': kwargs.get('ode_solver',
                                                    self.ODE_SOLVER_DEFAULT),
                           'version': pype9.version}
            self.render_to_file('configure-ac.tmpl', config_args,
                                 'configure.ac', src_dir)
            self.render_to_file('Makefile-am.tmpl', config_args,
                                 'Makefile.am', src_dir)
            self.render_to_file('bootstrap-sh.tmpl', config_args,
                                 'bootstrap.sh', src_dir)
            os.chdir(src_dir)
            try:
                bootstrap = sp.Popen(
                    ['sh', 'bootstrap.sh'], stdout=sp.PIPE, stderr=sp.PIPE)
                stdout, stderr = bootstrap.communicate()
            except sp.CalledProcessError as e:
                raise Pype9BuildError(
                    "Error executing bootstrapping of '{}' NEST module "
                    "failed (see src directory '{}'):\n\n{}"
                    .format(name or src_dir, src_dir, e))
            if not stdout.rstrip().endswith('Done.'):
                raise Pype9BuildError(
                    "Bootstrapping of '{}' NEST module failed (see src "
                    "directory '{}'):\n\n{}\n{}"
                    .format(name or src_dir, src_dir, stdout, stderr))
            if verbose is True:
                print stderr
                print stdout
            os.chdir(compile_dir)
            env = os.environ.copy()
            env['CXX'] = self._compiler
            try:
                configure = sp.Popen(
                    ['sh', src_dir + '/configure', '--prefix=' + install_dir],
                    env=env, stdout=sp.PIPE, stderr=sp.PIPE)
                stdout, stderr = configure.communicate()
            except sp.CalledProcessError as e:
                raise Pype9BuildError(
                    "Configuration of '{}' NEST module failed (see src "
                    "directory '{}'):\n\n {}".format(name, src_dir, e))
            if 'make install' not in stdout:
                raise Pype9BuildError(
                    "Configure of '{}' NEST module failed (see src "
                    "directory '{}'):\n\n{}\n{}"
                    .format(name or src_dir, src_dir, stdout, stderr))
            if verbose is True:
                print stderr
                print stdout
            os.chdir(orig_dir)

    def compile_source_files(self, compile_dir, component_name, verbose):
        # Run configure script, make and make install
        os.chdir(compile_dir)
        if verbose != 'silent':
            print ("Compiling NEST model class in '{}' directory."
                   .format(compile_dir))
        try:
            make = sp.Popen(['make', '-j{}'.format(self._build_cores)],
                            stdout=sp.PIPE, stderr=sp.PIPE)
            stdout, stderr = make.communicate()
        except sp.CalledProcessError as e:
            raise Pype9BuildError(
                "Compilation of '{}' NEST module failed (see compile "
                "directory '{}'):\n\n {}"
                .format(component_name, compile_dir, e))
        if re.match(r'error', stderr, re.IGNORECASE):
            raise Pype9BuildError(
                "Compilation of '{}' NEST module directory failed:\n\n{}\n{}"
                .format(compile_dir, stdout, stderr))
        if verbose is True:
            print stderr
            print stdout
        try:
            install = sp.Popen(['make', 'install'], stdout=sp.PIPE,
                               stderr=sp.PIPE)
            stdout, stderr = install.communicate()
        except sp.CalledProcessError as e:
            raise Pype9BuildError(
                "Installation of '{}' NEST module failed (see compile "
                "directory '{}'):\n\n {}"
                .format(component_name, compile_dir, e))
        # FIXME: At some point I should try to work out why building the SLI
        #        documentation fails so I can just check stderr here
        if ('Libraries have been installed in:' not in stdout and
              not stdout.rstrip().endswith('Done.')):
            raise Pype9BuildError(
                "Installation of '{}' NEST module directory failed:\n\n{}\n{}"
                .format(compile_dir, stdout, stderr))
        if verbose is True:
            print stderr
            print stdout
        if verbose != 'silent':
            print ("Compilation of '{}' NEST module completed successfully"
                   .format(component_name))

    def clean_src_dir(self, src_dir, name):
        # Clean existing src directories from previous builds.
        prefix = path.join(src_dir, name)
        if path.exists(src_dir):
            remove_ignore_missing(prefix + '.h')
            remove_ignore_missing(prefix + '.cpp')
            remove_ignore_missing(prefix + 'Module.h')
            remove_ignore_missing(prefix + 'Module.cpp')
            remove_ignore_missing(
                path.join(src_dir, 'sli', name + 'Module-init.sli'))
        sli_path = path.join(src_dir, 'sli')
        if not path.exists(sli_path):
            os.makedirs(sli_path)

    def clean_compile_dir(self, compile_dir, verbose=False, **kwargs):  # @UnusedVariable @IgnorePep8
        orig_dir = os.getcwd()
        try:
            if not path.exists(compile_dir):
                os.makedirs(compile_dir)
        except IOError, e:
            raise Pype9BuildError(
                "Could not make compile directory '{}': {}"
                .format(compile_dir, e))
        try:
            os.chdir(compile_dir)
            clean = sp.Popen(['make', 'clean'], stdout=sp.PIPE, stderr=sp.PIPE)
            stdout, stderr = clean.communicate()
            os.chdir(orig_dir)
        except sp.CalledProcessError or IOError:
            os.chdir(orig_dir)
            shutil.rmtree(compile_dir, ignore_errors=True)
            try:
                os.makedirs(compile_dir)
            except IOError as e:
                raise Pype9BuildError(
                    "Could not create build directory ({}), please check the "
                    "required permissions or specify a different \"parent "
                    "build directory\" ('parent_build_dir') -> {}".format(e))
        if stderr and self._no_makefile_re.match(stderr) is None:
            raise Pype9BuildError(
                "Clean of '{}' NEST module directory failed:\n\n{}\n{}"
                .format(compile_dir, stdout, stderr))
        if verbose is True:
            print stderr
            print stdout

    def simulator_specific_paths(self):
        path = []
        if 'NEST_INSTALL_DIR' in os.environ:
            path.append(path.join(os.environ['NEST_INSTALL_DIR'], 'bin'))
        return path

    _no_makefile_re = re.compile(r"make: \*\*\* No rule to make target .clean."
                                 r"\.  Stop\.")
