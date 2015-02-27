"""

  This module contains functions for building and loading NMODL mechanisms

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
import os.path
import shutil
import time
from itertools import chain
from collections import defaultdict
import platform
import tempfile
from copy import deepcopy
import uuid
import subprocess as sp
import quantities as pq
from ..base import BaseCodeGenerator
import nineml.abstraction_layer.units as un
from nineml.abstraction_layer.dynamics import (
    OnEvent, TimeDerivative, StateVariable)
from nineml.abstraction_layer.expressions import Alias
from nineml.abstraction_layer.ports import (
    AnalogReceivePort, AnalogSendPort)
from pype9.exceptions import Pype9BuildError, Pype9RuntimeError
import pype9
from datetime import datetime
from nineml.utils import expect_single


class CodeGenerator(BaseCodeGenerator):

    SIMULATOR_NAME = 'neuron'
    ODE_SOLVER_DEFAULT = 'derivimplicit'
    _TMPL_PATH = os.path.join(os.path.dirname(__file__), 'jinja_templates')

    _neuron_units = {un.mV: 'millivolt',
                     un.S: 'siemens',
                     un.mA: 'milliamp'}

    _inbuilt_ions = ['na', 'k', 'ca']

    def __init__(self):
        super(CodeGenerator, self).__init__()
        # Find the path to nrnivmodl
        self.nrnivmodl_path = self.path_to_exec('nrnivmodl')
        # Work out the name of the installation directory for the compiled
        # NMODL files on the current platform
        self.specials_dir = self._get_specials_dir()

    def generate_source_files(self, component, initial_state, src_dir,  # @UnusedVariable @IgnorePep8
                              **kwargs):
        """
            *KWArgs*
                `membrane_voltage` -- Specifies the state that represents
                                      membrane voltage.
                `v_threshold`      -- The threshold for the neuron to emit a
                                      spike.
                `external_ports`   -- Analog ports to strip from expressions
                                      as they represent synapses or injected
                                      currents, which can be inserted manually
                                      by NEURON objects.
                `is_subcomponent`  -- Whether to use the 'SUFFIX' tag or not.
                `ode_solver`       -- specifies the ODE solver to use
        """
        # TODO: will check to see if it is a multi-component here and generate
        #       multiple mod files unless specifically requested to be flat
        if ('membrane_voltage' not in kwargs or
                'membrane_capacitance' not in kwargs):
            raise Pype9BuildError(
                "'membrane_voltage' and 'membrane_capacitance' variables must "
                "be specified for standalone NEURON mod file generation: {}"
                .format(kwargs))
        self.generate_mod_file(
            component, initial_state, src_dir,
            membrane_voltage=kwargs['membrane_voltage'],
            membrane_capacitance=kwargs['membrane_capacitance'],
            is_subcomponent=kwargs.get('is_subcomponent', False),
            external_ports=kwargs.get('external_ports', []),
            ode_solver=kwargs.get('ode_solver', self.ODE_SOLVER_DEFAULT))

    def generate_mod_file(self, component, initial_state, src_dir,
                          membrane_voltage, membrane_capacitance,
                          is_subcomponent, external_ports, ode_solver):
        componentclass = self.convert_to_current_centric(
            component.component_class, membrane_voltage, membrane_capacitance)
        tmpl_args = {
            'component': component,
            'componentclass': componentclass,
            'version': pype9.version, 'src_dir': src_dir,
            'timestamp': datetime.now().strftime('%a %d %b %y %I:%M:%S%p'),
            'unit_conversion': self.unit_conversion,
            'ode_solver': ode_solver,
            'external_ports': external_ports,
            'is_subcomponent': is_subcomponent,
            # FIXME: weight_vars needs to be removed or implmented properly
            'weight_variables': []}
        # Render mod file
        self.render_to_file('main.tmpl', tmpl_args, component.name + '.mod',
                            src_dir)

    @classmethod
    def convert_to_current_centric(cls, componentclass, membrane_voltage,
                                   membrane_capacitance):
        """
        Copy the component class to alter it to match NEURON's current
        centric focus
        `membrane_voltage` -- the name of the state variable that represents
                              the membrane voltage
        `membrane_voltage` -- the name of the capcitance that represents
                              the membrane capacitance
        """
        # Clone component class
        cc = deepcopy(componentclass)
        # Rename references to specified membrane voltage to hard coded NEURON
        # value
        cc.rename_symbol(membrane_voltage, 'v')
        try:
            v = cc.state_variable('v')
            cm = cc.parameter(membrane_capacitance)
        except KeyError:
            raise Pype9RuntimeError(
                "Could not find specified voltage or capacitance ('{}', '{}')"
                .format(v.name, cm.name))
        if v.dimension != un.voltage:
            raise Pype9RuntimeError(
                "Specified membrane voltage does not have 'voltage' dimension"
                " ({})".format(v.dimension.name))
        if cm.dimension != un.specificCapacitance:
            raise Pype9RuntimeError(
                "Specified membrane capacitance does not have "
                "'specificCapacitance' dimension ({})"
                .format(v.dimension.name))
        # Replace voltage state-variable with analog receive port
        cc.remove(v)
        cc.add(AnalogReceivePort(v.name, dimension=un.voltage))
        # Remove associated analog send port if present
        try:
            cc.remove(cc.analog_send_port('v'))
        except KeyError:
            pass
        # Add current to component
        i_name = 'i' if 'i' not in cc.state_variable_names else 'i_'
        # Get the voltage time derivatives from each regime (must be constant
        # as there is no OutputAnalog)
        dvdt = next(cc.regimes).time_derivative(v.name)
        for regime in cc.regimes:
            if regime.time_derivative(v.name) != dvdt:
                raise Pype9RuntimeError(
                    "Cannot convert to current centric as the voltage time for"
                    " derivative equation changes between regimes")
            regime.remove(regime.time_derivative(v.name))
        # Add alias expression for current
        i = Alias(i_name, rhs=dvdt.rhs * cm)
        cc.add(i)
        # Add analog send port for current
        i_port = AnalogSendPort(i_name, dimension=un.currentDensity)
        i_port.annotations = {'biophysics': {'ion_species':
                                             'non_specific'}}
        cc.add(i_port)
        # Validate the transformed model
        cc.validate()
        return cc

    def configure_build_files(self, component, src_dir, compile_dir,
                               install_dir):
        pass

    def compile_source_files(self, compile_dir, component_name, verbose):
        """
        Builds all NMODL files in a directory
        `src_dir`     -- The path of the directory to build
        `build_mode`  -- Can be one of either, 'lazy', 'super_lazy',
                           'require', 'force', or 'build_only'. 'lazy' doesn't
                           run nrnivmodl if the library is found, 'require',
                           requires that the library is found otherwise throws
                           an exception (useful on clusters that require
                           precompilation before parallelisation where the
                           error message could otherwise be confusing), 'force'
                           removes existing library if found and recompiles,
                           and 'build_only' removes existing library if found,
                           recompile and then exit
        `verbose`     -- Prints out verbose debugging messages
        """
        # Change working directory to model directory
        os.chdir(compile_dir)
        if verbose:
            print ("Building NEURON mechanisms in '{}' directory."
                   .format(compile_dir))
        # Run nrnivmodl command in src directory
        try:
            if not verbose:
                with open(os.devnull, "w") as fnull:
                    sp.check_call(self.nrnivmodl_path, stdout=fnull,
                                  stderr=fnull)
            else:
                sp.check_call(self.nrnivmodl_path)
        except sp.CalledProcessError as e:
            raise Pype9BuildError(
                "Compilation of NMODL files for '{}' model failed. See src "
                "directory '{}':\n\n{}".format(component_name, compile_dir, e))

    def get_install_dir(self, build_dir, install_dir):
        if install_dir:
            raise Pype9BuildError(
                "Cannot specify custom installation directory ('{}') for "
                "NEURON simulator as it needs to be located as a specifically "
                "named directory of the src directory (e.g. x86_64 for 64b "
                "unix/linux)".format(install_dir))
        # return the platform-specific location of the nrnivmodl output files
        return os.path.abspath(os.path.join(build_dir, self._SRC_DIR,
                                            self.specials_dir))

    def get_compile_dir(self, build_dir):
        """
        The compile dir is the same as the src dir for NEURON compile
        """
        return os.path.abspath(os.path.join(build_dir, self._SRC_DIR))

    def clean_compile_dir(self, compile_dir):
        pass  # NEURON doesn't use a separate compile dir

    def _get_specials_dir(self):
        # Create a temporary directory to run nrnivmodl in
        tmp_dir_path = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
        try:
            os.mkdir(tmp_dir_path)
        except IOError:
            raise Pype9BuildError("Error creating temporary directory '{}'"
                                  .format(tmp_dir_path))
        orig_dir = os.getcwd()
        os.chdir(tmp_dir_path)
        # Run nrnivmodl to see what build directory is created
        try:
            with open(os.devnull, "w") as fnull:
                sp.check_call(self.nrnivmodl_path, stdout=fnull, stderr=fnull)
        except sp.CalledProcessError as e:
            raise Pype9BuildError("Error test running nrnivmodl".format(e))
        # Get the name of the specials directory
        try:
            specials_dir = os.listdir(tmp_dir_path)[0]
        except IndexError:
            raise Pype9BuildError(
                "Error test running nrnivmodl no build directory created"
                .format(e))
        # Return back to the original directory
        os.chdir(orig_dir)
        return specials_dir

    def simulator_specific_paths(self):
        path = []
        try:
            for d in os.listdir(os.environ['NRNHOME']):
                bin_path = os.path.join(d, 'bin')
                if os.path.exists(bin_path):
                    path.append(bin_path)
        except KeyError:
            pass
        return path
