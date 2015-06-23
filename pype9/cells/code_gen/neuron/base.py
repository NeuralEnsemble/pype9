"""

  This module contains functions for building and loading NMODL mechanisms

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
import os.path
import tempfile
from copy import copy
import uuid
from itertools import chain, groupby
import subprocess as sp
from collections import defaultdict
import sympy
from ..base import BaseCodeGenerator
import nineml.units as un
from nineml.abstraction.expressions import Alias
from nineml.abstraction.ports import AnalogSendPort
from pype9.exceptions import Pype9BuildError
import pype9
from datetime import datetime
from nineml import Document
from nineml.user import DynamicsProperties, Definition, Property
from nineml.abstraction import (StateAssignment, Parameter, StateVariable,
                                Constant)
from sympy.printing import ccode

try:
    from nineml.extensions.kinetics import Kinetics  # @UnusedImport
except ImportError:
    KineticsClass = type(None)
from pype9.annotations import (
    PYPE9_NS, ION_SPECIES, MEMBRANE_VOLTAGE, MEMBRANE_CAPACITANCE,
    TRANSFORM_SRC, TRANSFORM_DEST, NONSPECIFIC_CURRENT,
    EXTERNAL_CURRENTS, NO_TIME_DERIVS, INTERNAL_CONCENTRATION,
    EXTERNAL_CONCENTRATION)
import logging

TRANSFORM_NS = 'NeuronBuildTransform'

logger = logging.getLogger("PyPe9")


class CodeGenerator(BaseCodeGenerator):

    SIMULATOR_NAME = 'neuron'
    ODE_SOLVER_DEFAULT = 'derivimplicit'
    BASE_TMPL_PATH = os.path.join(os.path.dirname(__file__), 'templates')

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

    def generate_source_files(self, prototype, initial_state, src_dir,
                              **kwargs):
        """
            *KWArgs*
                `membrane_voltage` -- Specifies the state that represents
                                      membrane voltage.
                `membrane_capacitance` -- Specifies the state that represents
                                      membrane capacitance.
                `default_capacitance` -- Specifies the quantity assigned to
                                      the membrane capacitance by default
                `v_threshold`      -- The threshold for the neuron to emit a
                                      spike.
                `external_ports`   -- Analog ports to strip from expressions
                                      as they represent synapses or injected
                                      currents, which can be inserted manually
                                      by NEURON objects.
                `is_subcomponent`  -- Whether to use the 'SUFFIX' tag or not.
                `ode_solver`       -- specifies the ODE solver to use
        """
        assert isinstance(prototype, DynamicsProperties), \
            ("Provided prototype class '{}' is not a Dynamics object"
             .format(prototype))
#         if isinstance(prototype, Kinetics):
#             self.generate_kinetics(name, prototype, initial_state, src_dir,
#                                    **kwargs)
#         el
        # Check whether it is a point process or a ion channel
        cc = prototype.component_class
        if isinstance(cc[cc.annotations[PYPE9_NS]['MembraneVoltage']],
                      StateVariable):
            self.generate_point_process(
                prototype, initial_state, src_dir, **kwargs)
        else:
            self.generate_ion_channel(prototype, initial_state, src_dir,
                                      **kwargs)

    def generate_ion_channel(self, prototype, initial_state, src_dir,
                             **kwargs):
        # Render mod file
        self.generate_mod_file('main.tmpl', prototype, initial_state, src_dir,
                               kwargs)

    def generate_kinetics(self, prototype, initial_state, src_dir, **kwargs):
        # Render mod file
        self.generate_mod_file('kinetics.tmpl', prototype, initial_state,
                               src_dir, kwargs)

    def generate_point_process(self, prototype, initial_state, src_dir,
                               **kwargs):
        add_tmpl_args = {'is_subcomponent': False}
        template_args = copy(kwargs)
        template_args.update(add_tmpl_args)
        # Render mod file
        self.generate_mod_file('main.tmpl', prototype, initial_state,
                               src_dir, template_args)

    def generate_mod_file(self, template, prototype, initial_state, src_dir,
                          template_args):
        tmpl_args = {
            'code_gen': self,
            'component_name': prototype.name,
            'componentclass': prototype.component_class,
            'prototype': prototype,
            'initial_state': initial_state,
            'version': pype9.version, 'src_dir': src_dir,
            'timestamp': datetime.now().strftime('%a %d %b %y %I:%M:%S%p'),
            'unit_conversion': self.unit_conversion,
            'ode_solver': self.ODE_SOLVER_DEFAULT,
            'external_ports': [],
            'is_subcomponent': True,
            # FIXME: weight_vars needs to be removed or implmented properly
            'weight_variables': []}
        tmpl_args.update(template_args)
        # Render mod file
        self.render_to_file(template, tmpl_args, prototype.name + '.mod',
                            src_dir)

    def transform_for_build(self, prototype, **kwargs):
        """
        Copy the component class to alter it to match NEURON's current
        centric focus
        `prototype`        -- the component to be transformed
        `membrane_voltage` -- the name of the state variable that represents
                              the membrane voltage
        `membrane_capacitance` -- the name of the capcitance that represents
                              the membrane capacitance
        """
        # ---------------------------------------------------------------------
        # Clone original component class and properties
        # ---------------------------------------------------------------------
        orig = prototype.component_class
        trfrm = copy(orig)
        props = [copy(p) for p in prototype.properties]
        # ---------------------------------------------------------------------
        # Get the membrane voltage and convert it to 'v'
        # ---------------------------------------------------------------------
        try:
            name = kwargs['membrane_voltage']
            try:
                orig_v = orig[name]
            except KeyError:
                raise Pype9BuildError(
                    "Could not find specified membrane voltage '{}'"
                    .format(name))
        except KeyError:  # Guess voltage from its dimension if not supplied
            candidate_vs = [cv for cv in orig.state_variables
                            if cv.dimension == un.voltage]
            if len(candidate_vs) == 0:
                candidate_vs = [cv for cv in orig.analog_receive_ports
                                if cv.dimension == un.voltage]
            if len(candidate_vs) == 1:
                orig_v = candidate_vs[0]
                print ("Guessing that '{}' is the membrane voltage"
                       .format(orig_v))
            elif len(candidate_vs) > 1:
                try:
                    orig_v = next(c for c in candidate_vs if c.name == 'v')
                    print ("Guessing that '{}' is the membrane voltage"
                           .format(orig_v))
                except StopIteration:
                    raise Pype9BuildError(
                        "Could not guess the membrane voltage, candidates: "
                        "'{}'" .format("', '".join(v.name
                                                   for v in candidate_vs)))
            else:
                raise Pype9BuildError(
                    "No candidates for the membrane voltage, "
                    "state_variables '{}', analog_receive_ports '{}'"
                    .format("', '".join(orig.state_variables),
                            "', '".join(orig.analog_receive_ports)))
        # Map voltage to hard-coded 'v' symbol
        if orig_v.name != 'v':
            trfrm.rename_symbol(orig_v.name, 'v')
            v = ['v']
            v.annotations[PYPE9_NS][TRANSFORM_SRC] = orig_v
        else:
            v = trfrm['v']
        # Add annotations to the original and build models
        orig.annotations[PYPE9_NS][MEMBRANE_VOLTAGE] = orig_v.name
        trfrm.annotations[PYPE9_NS][MEMBRANE_VOLTAGE] = 'v'
        # Remove associated analog send port if present
        try:
            trfrm.remove(trfrm.analog_send_port('v'))
        except KeyError:
            pass
        # Need to convert to AnalogReceivePort if v is a StateVariable
        if isinstance(v, StateVariable):
            # -----------------------------------------------------------------
            # Insert membrane capacitance if not present
            # -----------------------------------------------------------------
            # Get or guess the location of the membrane capacitance
            try:
                name = kwargs['membrane_capacitance']
                try:
                    orig_cm = orig.parameter(name)
                except KeyError:
                    raise Pype9BuildError(
                        "Could not find specified membrane capacitance '{}'"
                        .format(name))
                cm = trfrm.parameter(orig_cm.name)
            except KeyError:  # 'membrane_capacitance' was not specified
                candidate_cms = [ccm for ccm in orig.parameters
                                 if ccm.dimension == un.capacitance]
                if len(candidate_cms) == 1:
                    orig_cm = candidate_cms[0]
                    cm = trfrm[orig_cm.name]
                    print ("Guessing that '{}' is the membrane capacitance"
                           .format(orig_cm))
                elif len(candidate_cms) > 1:
                    raise Pype9BuildError(
                        "Could not guess the membrane capacitance, candidates:"
                        " '{}'".format("', '".join(candidate_cms)))
                else:
                    cm = Parameter("cm_", dimension=un.capacitance)
                    trfrm.add(cm)
                    qty = kwargs.get('default_capacitance', (1.0, un.nF))
                    props.append(Property('cm_', *qty))
            cm.annotations[PYPE9_NS][TRANSFORM_SRC] = None
            trfrm.annotations[PYPE9_NS][MEMBRANE_CAPACITANCE] = cm.name
            # -----------------------------------------------------------------
            # Replace membrane voltage equation with membrane current
            # -----------------------------------------------------------------
            # Determine the regimes in which each state variables has a time
            # derivative in
            has_td = defaultdict(list)
            # List which regimes need to be clamped to their last voltage
            # (as it has no time derivative)
            clamped_regimes = []
            # The voltage clamp equation where v_clamp is the last voltage
            # value and g_clamp_ is a large conductance
            clamp_i = sympy.sympify('g_clamp_ * (v - v_clamp_)')
            memb_is = []
            for regime in trfrm.regimes:
                # Add an appropriate membrane current
                try:
                    # Convert the voltage time derivative into a membrane
                    # current
                    dvdt = regime.time_derivative(v.name)
                    regime.remove(dvdt)
                    i = -dvdt.rhs * cm
                    memb_is.append(i)
                except KeyError:
                    i = clamp_i
                    clamped_regimes.append(regime)
                regime.add(Alias('i_', i))
                # Record state vars that have a time deriv. in this regime
                for var in regime.time_derivative_variables:
                    if var != 'v':
                        has_td[var].append(regime)
            # Pick the most popular membrane current to be the alias in
            # the global scope
            assert memb_is, "No regimes contain voltage time derivatives"
            memb_i = Alias('i_', max(memb_is, key=memb_is.count))
            # Add membrane current along with a analog send port
            trfrm.add(memb_i)
            i_port = AnalogSendPort('i_', dimension=un.current)
            i_port.annotations[PYPE9_NS][ION_SPECIES] = NONSPECIFIC_CURRENT
            trfrm.add(i_port)
            # Remove membrane currents that match the membrane current in the
            # outer scope
            for regime in trfrm.regimes:
                if regime.alias('i_') == memb_i:
                    regime.remove(regime.alias('i_'))
            # If there are clamped regimes add extra parameters and set the
            # voltage to clamp to in the regimes that trfrmition to them
            if clamped_regimes:
                trfrm.add(StateVariable('v_clamp_', un.voltage))
                trfrm.add(Constant('g_clamp_', 1e8, un.uS))
                for trans in trfrm.transitions:
                    if trans.target_regime in clamped_regimes:
                        # Assign v_clamp_ to the value
                        try:
                            v_clamp_rhs = trans.state_assignment('v').rhs
                        except KeyError:
                            v_clamp_rhs = 'v'
                        trans.add(StateAssignment('v_clamp_', v_clamp_rhs))
            # -----------------------------------------------------------------
            trfrm.annotations[PYPE9_NS][NO_TIME_DERIVS] = (
                ['v'] + [sv for sv in trfrm.state_variable_names
                         if sv not in has_td])
            # -----------------------------------------------------------------
            # Get the external input currents
            # -----------------------------------------------------------------
            # Analog receive or reduce ports that are of dimension current and
            # are purely additive to the membrane current and nothing else
            # (actually subtractive as it is outward current)
            try:
                ext_is = []
                for i_name in kwargs['external_currents']:
                    try:
                        ext_i = trfrm.analog_receive_port(i_name)
                    except KeyError:
                        try:
                            ext_i = trfrm.analog_reduce_port(i_name)
                        except KeyError:
                            raise Pype9BuildError(
                                "Did not find specified external current port "
                                "'{}'".format(i_name))
                    if ext_i.dimension != un.current:
                        raise Pype9BuildError(
                            "Analog receive port matching specified external "
                            "current '{}' does not have 'current' dimension "
                            "({})".format(ext_i.name, ext_i.dimension))
                    ext_is.append(ext_i)
            except KeyError:
                ext_is = [
                    i for i in chain(orig.analog_receive_ports,
                                     orig.analog_reduce_ports)
                    if (i.dimension == un.current and
                        i.name in memb_i.rhs_symbol_names and
                        len([e for e in orig.all_expressions
                             if i.symbol in e.free_symbols]) == 1)]
                print ("Guessing '{}' external currents to be removed"
                       .format("', '".join(i.name for i in ext_is)))
            trfrm.annotations[PYPE9_NS][EXTERNAL_CURRENTS] = ext_is
            # Remove external input current ports (as NEURON handles them)
            for ext_i in ext_is:
                trfrm.remove(ext_i)
                for expr in chain(trfrm.aliases, trfrm.all_time_derivatives()):
                    expr.subs(ext_i, 0)
                    expr.simplify()
        else:
            # -----------------------------------------------------------------
            # Sort out different analog ports into ionic species
            # -----------------------------------------------------------------
            assigned_species = kwargs.get('ion_species', {})
            for port in trfrm.analog_ports:
                # TODO: Need to check for temperature analog ports or more
                #       general analog ports (i.e. POINTERS)
                if port.name != 'v':
                    try:
                        species = assigned_species[port.name]
                        if species is None:
                            if port.dimension not in (un.current,
                                                      un.currentDensity):
                                raise Pype9BuildError(
                                    "Only current ports can be ion "
                                    "non-specific {}".format(port))
                            species = NONSPECIFIC_CURRENT
                    except KeyError:
                        if ION_SPECIES not in port.annotations[PYPE9_NS]:
                            raise Pype9BuildError(
                                "'{}' port was not assigned a ionic species"
                                .format(port.name))
                        species = port.annotations[PYPE9_NS][ION_SPECIES]
                    if species != NONSPECIFIC_CURRENT:
                        if port.dimension == un.voltage:
                            new_name = 'e' + species
                        elif port.dimension == un.currentDensity:
                            new_name = 'i' + species
                        elif port.dimension == un.concentration:
                            try:
                                if species[1] == INTERNAL_CONCENTRATION:
                                    new_name = species[0] + 'i'
                                elif species[1] == EXTERNAL_CONCENTRATION:
                                    new_name = species[0] + 'o'
                                else:
                                    raise Pype9BuildError(
                                        "Concentration receive ports must "
                                        "specify whether they are internal or "
                                        "external")
                            except IndexError:
                                raise Pype9BuildError(
                                    "Concentration receive ports must specify "
                                    "whether they are internal or external")
                        else:
                            raise Pype9BuildError(
                                "Unrecognised dimension of analog receive port"
                                " '{}', can only be voltage or current density"
                                .format(port.dimension))
                        trfrm.rename_symbol(port.name, new_name)
                    port.annotations[PYPE9_NS][ION_SPECIES] = species
            # Collate all ports relating to each ion species
            key_func = lambda p: p.annotations[PYPE9_NS][ION_SPECIES]
            sorted_ion_ports = sorted(
                (p for p in trfrm.analog_ports
                 if ION_SPECIES in p.annotations[PYPE9_NS]), key=key_func)
            trfrm.annotations[PYPE9_NS][ION_SPECIES] = dict(
                (s, list(ps)) for s, ps in groupby(sorted_ion_ports,
                                                   key=key_func))
            try:
                non_specifics = trfrm.annotations[
                    PYPE9_NS][ION_SPECIES][NONSPECIFIC_CURRENT]
                if len(non_specifics) != 1:
                    raise Pype9BuildError(
                        "More than one non-specific current port found ('{}')"
                        .format("', '".join(p.name for p in non_specifics)))
                non_spec = non_specifics[0]
                if not (isinstance(non_spec, AnalogSendPort) and
                        non_spec.dimension in (un.current, un.currentDensity)):
                    raise Pype9BuildError(
                        "Only analog send ports with current or current "
                        "density dimensiones can be non-specific ({})"
                        .format(non_spec))
            except KeyError:
                pass  # No non-specific currents
        # -----------------------------------------------------------------
        # Validate the transformed component class and construct prototype
        # -----------------------------------------------------------------
        trfrm.validate()
        # Retun a prototype of the transformed class
        return DynamicsProperties(
            prototype.name, Definition(trfrm.name, Document(trfrm)), props)

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
            print ("Building NMODL mechanisms in '{}' directory."
                   .format(compile_dir))
        # Run nrnivmodl command in src directory
        try:
            pipe = sp.Popen([self.nrnivmodl_path], stdout=sp.PIPE,
                            stderr=sp.PIPE)
            stdout, stderr = pipe.communicate()
        except sp.CalledProcessError as e:
            raise Pype9BuildError(
                "Compilation of NMODL files for '{}' model failed. See src "
                "directory '{}':\n\n{}".format(component_name, compile_dir, e))
        if stderr.strip().endswith('Error 1'):
            raise Pype9BuildError(
                "Generated mod file failed to compile with output:\n{}\n{}"
                .format(stdout, stderr))
        if verbose:
            print stdout
            print stderr

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

    def assign_str(self, expr):
        rhs = expr.expand_integer_powers()
        nmodl_str = ccode(rhs, user_functions=expr._cfunc_map,
                          assign_to=expr.lhs)
        nmodl_str = expr.rationals_re.sub(r'\1/\2', nmodl_str)
        nmodl_str = nmodl_str.replace(';', '')
        return nmodl_str
