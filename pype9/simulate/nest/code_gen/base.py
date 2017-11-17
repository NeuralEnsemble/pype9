"""

  This module contains functions for building and loading nest modules

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
from future.utils import PY3
import os
import sys
from os import path
import subprocess as sp
import re
import shutil
from datetime import datetime
import errno
import nest
from pype9.simulate.nest.units import UnitHandler
from pype9.simulate.common.code_gen import BaseCodeGenerator
from pype9.utils.paths import remove_ignore_missing, add_lib_path
from pype9.exceptions import Pype9BuildError
import pype9
from pype9.utils.logging import logger

cmake_success_re = re.compile(r'-- Build files have been written to: (.*)')


class CodeGenerator(BaseCodeGenerator):

    SIMULATOR_NAME = 'nest'
    SIMULATOR_VERSION = nest.version().split()[1]
    ODE_SOLVER_DEFAULT = 'gsl'
    REGIME_VARNAME = '__regime__'
    SS_SOLVER_DEFAULT = None
    MAX_STEP_SIZE_DEFAULT = 0.01  # Used for CVODE/IDA, FIXME: not sure best value!!! @IgnorePep8
    ABS_TOLERANCE_DEFAULT = 1e-3
    REL_TOLERANCE_DEFAULT = 0.0
    GSL_JACOBIAN_APPROX_STEP_DEFAULT = 0.01
    V_THRESHOLD_DEFAULT = 0.0
    MAX_SIMULTANEOUS_TRANSITIONS = 1000
    BASE_TMPL_PATH = path.abspath(path.join(path.dirname(__file__),
                                            'templates'))
    UnitHandler = UnitHandler

    _inline_random_implementations = {}

    def __init__(self, build_cores=1, **kwargs):
        super(CodeGenerator, self).__init__(**kwargs)
        self._build_cores = build_cores
        self.nest_config = os.path.join(
            self.get_nest_install_prefix(), 'bin', 'nest-config')
        compiler, _ = self.run_command(
            [self.nest_config, '--compiler'],
            fail_msg=("Could not run nest-config at '{}': {{}}"
                      .format(self.nest_config)))
        self._compiler = compiler.strip()  # strip trailing \n

    def generate_source_files(self, component_class, src_dir, name=None,
                              debug_print=None, **kwargs):
        if name is None:
            name = component_class.name
        # Get the initial regime and check that it refers to a regime in the
        # component class
        tmpl_args = {
            'component_name': name,
            'component_class': component_class,
            'version': pype9.__version__, 'src_dir': src_dir,
            'timestamp': datetime.now().strftime('%a %d %b %y %I:%M:%S%p'),
            'unit_handler': UnitHandler(component_class),
            'sorted_regimes': sorted(
                component_class.regimes,
                key=lambda r: component_class.index_of(r)),
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
            'v_threshold': kwargs.get('v_threshold', self.V_THRESHOLD_DEFAULT),
            'regime_varname': self.REGIME_VARNAME,
            'debug_print': [] if debug_print is None else debug_print}
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
        # Render SLI initializer
        self.render_to_file('module_sli_init.tmpl', tmpl_args,
                             name + 'Module-init.sli',
                             path.join(src_dir, 'sli'))

    def configure_build_files(self, name, src_dir, compile_dir, install_dir,
                              **kwargs):  # @UnusedVariable
        # Generate Makefile if it is not present
        if not path.exists(path.join(compile_dir, 'Makefile')):
            if not path.exists(compile_dir):
                os.mkdir(compile_dir)
            logger.info("Configuring build files in '{}' directory"
                        .format(compile_dir))
            orig_dir = os.getcwd()
            config_args = {'name': name, 'src_dir': src_dir,
                           # NB: ODE solver currently ignored
                           # 'ode_solver': kwargs.get('ode_solver',
                           #                          self.ODE_SOLVER_DEFAULT),
                           'version': pype9.__version__,
                           'executable': sys.executable}
            self.render_to_file('CMakeLists.txt.tmpl', config_args,
                                 'CMakeLists.txt', src_dir)
            os.chdir(compile_dir)
            stdout, stderr = self.run_command(
                ['cmake',
                 '-Dwith-nest={}'.format(self.nest_config),
                 '-DCMAKE_INSTALL_PREFIX={}'.format(install_dir), src_dir],
                fail_msg=(
                    "Cmake of '{}' NEST module failed (see src "
                    "directory '{}'):\n\n {{}}".format(name, src_dir)))
            if stderr:
                raise Pype9BuildError(
                    "Configure of '{}' NEST module failed (see src "
                    "directory '{}'):\n\n{}\n{}"
                    .format(name or src_dir, src_dir, stdout, stderr))
                logger.debug("cmake '{}':\nstdout:\n{}stderr:\n{}\n"
                             .format(compile_dir, stdout, stderr))
            os.chdir(orig_dir)

    def compile_source_files(self, compile_dir, component_name):
        # Run configure script, make and make install
        os.chdir(compile_dir)
        logger.info("Compiling NEST model class in '{}' directory."
                    .format(compile_dir))
        stdout, stderr = self.run_command(
            ['make',
             '-j{}'.format(self._build_cores)],
            fail_msg=("Compilation of '{}' NEST module failed (see compile "
                      "directory '{}'):\n\n {{}}".format(component_name,
                                                         compile_dir)))
        if re.search(r'error:', stderr):  # Ignores warnings
            raise Pype9BuildError(
                "Compilation of '{}' NEST module directory failed:\n\n{}\n{}"
                .format(compile_dir, stdout, stderr))
        logger.debug("make '{}':\nstdout:\n{}stderr:\n{}\n"
                     .format(compile_dir, stdout, stderr))
        stdout, stderr = self.run_command(['make',
                                           'install'], fail_msg=(
            "Installation of '{}' NEST module failed (see compile "
            "directory '{}'):\n\n {{}}"
            .format(component_name, compile_dir)))
        if stderr:
            raise Pype9BuildError(
                "Installation of '{}' NEST module directory failed:\n\n{}\n{}"
                .format(compile_dir, stdout, stderr))
        logger.debug("make install'{}':\nstdout:\n{}stderr:\n{}\n"
                     .format(compile_dir, stdout, stderr))
        logger.info("Compilation of '{}' NEST module completed "
                    "successfully".format(component_name))

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

    def clean_compile_dir(self, compile_dir, purge=False, **kwargs):  # @UnusedVariable @IgnorePep8
        if purge:
            try:
                shutil.rmtree(compile_dir)
            except OSError as e:
                if e.errno != errno.ENOENT:  # Ignore if missing
                    raise
        if not path.exists(compile_dir):
            try:
                os.makedirs(compile_dir)
            except OSError as e:
                raise Pype9BuildError(
                    "Could not make compile directory '{}': {}"
                    .format(compile_dir, e))
        else:
            orig_dir = os.getcwd()
            os.chdir(compile_dir)
            try:
                stdout, stderr = self.run_command(['make', 'clean'])
                os.chdir(orig_dir)
            except (sp.CalledProcessError, OSError):
                os.chdir(orig_dir)
                shutil.rmtree(compile_dir, ignore_errors=True)
                try:
                    os.makedirs(compile_dir)
                except OSError as e:
                    raise Pype9BuildError(
                        "Could not create build directory ({}), please check "
                        "the required permissions or specify a different "
                        "build directory:\n{}".format(e))
            if stderr and 'No rule to make target' not in stderr:
                raise Pype9BuildError(
                    "Clean of '{}' NEST module directory failed:\n\n{}\n{}"
                    .format(compile_dir, stdout, stderr))
            logger.debug("make clean '{}':\nstdout:\n{}stderr:\n{}\n"
                         .format(compile_dir, stdout, stderr))

    def simulator_specific_paths(self):
        path = []
        if 'NEST_INSTALL_DIR' in os.environ:
            path.append(path.join(os.environ['NEST_INSTALL_DIR'], 'bin'))
        return path

    def load_libraries(self, name, url, **kwargs):  # @UnusedVariable
        install_dir = self.get_install_dir(name, url)
        lib_dir = os.path.join(install_dir, 'lib')
        add_lib_path(lib_dir)
        # Add module install directory to NEST path
        nest.sli_run(
            '({}) addpath'.format(os.path.join(install_dir, 'share', 'sli')))
        # Install nest module
        nest.Install(name + 'Module')

    @classmethod
    def get_nest_install_prefix(cls):
        # Make doubly sure that the loaded nest install appears first on the
        # PYTHONPATH (not sure if this is necessary, but can't hurt)
        pynest_install_dir = os.path.join(os.path.dirname(nest.__file__),
                                          '..')
        env = os.environ.copy()
        env['PYTHONPATH'] = os.pathsep.join((pynest_install_dir,
                                             env.get('PYTHONPATH', '')))
        try:
            process = sp.Popen(
                [sys.executable, '-c', "import nest; nest.sysinfo()"],
                stdout=sp.PIPE, stderr=sp.PIPE, env=env)
            stdout, _ = process.communicate()
        except sp.CalledProcessError as e:
            raise Pype9BuildError(
                "Error trying to run 'import nest; nest.sysinfo()' in "
                "subprocess:\n{}".format(e))
        if PY3:
            stdout = str(stdout.decode('utf-8'))
        match = re.search(r'\(([^\)]+)/share/nest/sli\)', stdout)
        if match is None:
            raise Pype9BuildError(
                "Could not find nest install prefix by searching for "
                "'share/nest/sli' in output from nest.sysinfo:\n{}"
                .format(stdout))
        return match.group(1)


if __name__ == '__main__':
    print(CodeGenerator.get_nest_config_path())
