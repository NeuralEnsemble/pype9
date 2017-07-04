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
from copy import copy, deepcopy
import uuid
from itertools import chain, groupby
import subprocess as sp
from collections import defaultdict
import sympy
import nineml.units as un
from nineml.abstraction import Alias, AnalogSendPort, Dynamics
from pype9.simulate.common.cells.code_gen import BaseCodeGenerator
from pype9.simulate.common.cells import (
    WithSynapses, DynamicsWithSynapses, DynamicsWithSynapsesProperties,
    MultiDynamicsWithSynapsesProperties)
from pype9.exceptions import Pype9BuildError, Pype9RuntimeError
import pype9
from datetime import datetime
from nineml import Document
from nineml.user import (
    MultiDynamicsProperties, DynamicsProperties, Definition, Property)
from nineml.abstraction import (StateAssignment, Parameter, StateVariable,
                                Constant, Expression)
from nineml.abstraction.dynamics.visitors.cloner import DynamicsCloner
from sympy.printing import ccode
from pype9.simulate.neuron.units import UnitHandler
try:
    from nineml.extensions.kinetics import Kinetics  # @UnusedImport
except ImportError:
    KineticsClass = type(None)
from pype9.annotations import (
    PYPE9_NS, ION_SPECIES, MEMBRANE_VOLTAGE, MEMBRANE_CAPACITANCE,
    TRANSFORM_SRC, TRANSFORM_DEST, NONSPECIFIC_CURRENT, BUILD_TRANS,
    EXTERNAL_CURRENTS, NO_TIME_DERIVS, INTERNAL_CONCENTRATION,
    EXTERNAL_CONCENTRATION, NUM_TIME_DERIVS, MECH_TYPE, FULL_CELL_MECH,
    SUB_COMPONENT_MECH, ARTIFICIAL_CELL_MECH)
import logging

TRANSFORM_NS = 'NeuronBuildTransform'

logger = logging.getLogger("PyPe9")

REGIME_VARNAME = 'regime_'
SEED_VARNAME = 'seed_'


class CodeGenerator(BaseCodeGenerator):

    SIMULATOR_NAME = 'neuron'
    ODE_SOLVER_DEFAULT = 'derivimplicit'
    BASE_TMPL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                  'templates'))
    LIBNINEMLNRN_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                     'libninemlnrn'))

    _neuron_units = {un.mV: 'millivolt',
                     un.S: 'siemens',
                     un.mA: 'milliamp'}

    _inbuilt_ions = ['na', 'k', 'ca']

    def __init__(self, gsl_path=None):
        super(CodeGenerator, self).__init__()
        self.nrnivmodl_path = self.path_to_utility('nrnivmodl')
        self.modlunit_path = self.path_to_utility('modlunit')
        self.nrnivmodl_flags = [
            '-L' + self.LIBNINEMLNRN_PATH,
            '-Wl,-rpath,' + self.LIBNINEMLNRN_PATH,
            '-lninemlnrn', '-lgsl', '-lgslcblas']
        if gsl_path is not None:
            self.nrnivmodl_path.append('-L' + gsl_path)
        else:
            try:
                # Check nest-config (if installed) to get any paths needed for
                # gsl
                nest_config_path = self.path_to_utility('nest-config')
                nest_lflags = sp.Popen(
                    [nest_config_path, '--libs'],
                    stdout=sp.PIPE).communicate()[0].split()
                self.nrnivmodl_flags.extend(
                    f for f in nest_lflags
                    if f.startswith('-L') and 'gsl' in f)
            except:
                logger.warning(
                    "Could not run nest-config to check the path for gsl. You"
                    " may need to supply the gsl path to the CodeGenerator "
                    "__init__ directly")
        # Work out the name of the installation directory for the compiled
        # NMODL files on the current platform
        self.specials_dir = self._get_specials_dir()

    def generate_source_files(self, component_class, src_dir, name=None,
                              **kwargs):
        """
        Generates main NMODL file for cell (and synapse) class

        Parameters
        ----------
        membrane_voltage : str
            Specifies the state that represents membrane voltage.
        membrane_capacitance : str
            Specifies the state that represents membrane capacitance.
        default_capacitance : float
            Specifies the quantity assigned to the membrane capacitance by
            default
        v_threshold: float
            The threshold for the neuron to emit a spike.
        external_ports : list(str)
            Analog ports to strip from expressions as they represent synapses
            or injected currents, which can be inserted manually by NEURON
            objects.
        is_subcomponent : bool
            Whether to use the 'SUFFIX' tag or not.
        ode_solver : str
            specifies the ODE solver to use
        """
        if name is None:
            name = component_class.name
        template = 'main.tmpl'
        self.generate_mod_file(template, component_class, src_dir, name,
                               kwargs)

    def generate_mod_file(self, template, component_class, src_dir, name,
                          template_args):
        tmpl_args = {
            'code_gen': self,
            'component_name': name,
            'component_class': component_class,
            'version': pype9.__version__, 'src_dir': src_dir,
            'timestamp': datetime.now().strftime('%a %d %b %y %I:%M:%S%p'),
            'unit_handler': UnitHandler(component_class),
            'ode_solver': self.ODE_SOLVER_DEFAULT,
            'external_ports': [],
            'is_subcomponent': True,
            'regime_varname': REGIME_VARNAME,
            'seed_varname': SEED_VARNAME}
#             # FIXME: weight_vars needs to be removed or implemented properly
#             'weight_variables': []}
        tmpl_args.update(template_args)
        # Render mod file
        self.render_to_file(
            template, tmpl_args, component_class.name + '.mod', src_dir)

    def transform_for_build(self, name, component_class, **kwargs):
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
        self._set_build_props(component_class, **kwargs)
        if not isinstance(component_class, WithSynapses):
            raise Pype9RuntimeError(
                "'component_class' must be a DynamicsWithSynapses object")
        # ---------------------------------------------------------------------
        # Clone original component class
        # ---------------------------------------------------------------------
        trfrm = DynamicsCloner().visit(component_class.dynamics)
#         trfrm.name = name
        # ---------------------------------------------------------------------
        # Get the membrane voltage and convert it to 'v'
        # ---------------------------------------------------------------------
        try:
            name = kwargs['membrane_voltage']
            try:
                orig_v = component_class.element(
                    name, class_map=Dynamics.class_to_member)
            except KeyError:
                raise Pype9BuildError(
                    "Could not find specified membrane voltage '{}'"
                    .format(name))
        except KeyError:  # Guess voltage from its dimension if not supplied
            candidate_vs = [cv for cv in component_class.state_variables
                            if cv.dimension == un.voltage]
            if len(candidate_vs) == 0:
                candidate_vs = [
                    cv for cv in component_class.analog_receive_ports
                    if cv.dimension == un.voltage]
            if len(candidate_vs) == 1:
                orig_v = candidate_vs[0]
                logger.info("Guessing that '{}' is the membrane voltage"
                            .format(orig_v))
            elif len(candidate_vs) > 1:
                try:
                    orig_v = next(c for c in candidate_vs if c.name == 'v')
                    logger.info("Guessing that '{}' is the membrane voltage"
                                .format(orig_v))
                except StopIteration:
                    raise Pype9BuildError(
                        "Could not guess the membrane voltage, candidates: "
                        "'{}'" .format("', '".join(v.name
                                                   for v in candidate_vs)))
            else:
                orig_v = None
                logger.info(
                    "Can't find candidate for the membrane voltage in "
                    "state_variables '{}' or analog_receive_ports '{}', "
                    "treating '{}' as an \"artificial cell\"".format(
                        "', '".join(
                            sv.name for sv in component_class.state_variables),
                        "', '".join(
                            p.name
                            for p in component_class.analog_receive_ports),
                        component_class.name))
        if orig_v is not None:
            # Map voltage to hard-coded 'v' symbol
            if orig_v.name != 'v':
                trfrm.rename_symbol(orig_v.name, 'v')
                v = trfrm.state_variable('v')
                v.annotations.set((BUILD_TRANS, PYPE9_NS),
                                  TRANSFORM_SRC, orig_v)
            else:
                v = trfrm.state_variable('v')
            # Add annotations to the original and build models
            component_class.annotations.set((BUILD_TRANS, PYPE9_NS),
                                            MEMBRANE_VOLTAGE, orig_v.name)  # @IgnorePep8
            trfrm.annotations.set((BUILD_TRANS, PYPE9_NS),
                                  MEMBRANE_VOLTAGE, 'v')
            # Remove associated analog send port if present
            try:
                trfrm.remove(trfrm.analog_send_port('v'))
            except KeyError:
                pass
            # Need to convert to AnalogReceivePort if v is a StateVariable
            if isinstance(v, StateVariable):
                self._transform_full_component(trfrm, component_class, v,
                                               **kwargs)
                trfrm.annotations.set((BUILD_TRANS, PYPE9_NS),
                                      MECH_TYPE, FULL_CELL_MECH)
            else:
                raise NotImplementedError(
                    "Build sub-components is not supported in PyPe9 v0.1")
        else:
            trfrm.annotations.set((BUILD_TRANS, PYPE9_NS), MECH_TYPE,
                                  ARTIFICIAL_CELL_MECH)
        # -----------------------------------------------------------------
        # Validate the transformed component class and construct prototype
        # -----------------------------------------------------------------
        trfrm.validate()
        trfrm_with_syn = DynamicsWithSynapses(
            name, trfrm, component_class.synapses,
            component_class.connection_parameter_sets)
        # Retun a prototype of the transformed class
        return trfrm_with_syn

    def _transform_full_component(self, trfrm, component_class, v, **kwargs):
        # -----------------------------------------------------------------
        # Remove all analog send ports with 'current' dimension so they
        # don't get confused with the converted voltage time derivative
        # expression
        # -----------------------------------------------------------------
        for port in list(trfrm.analog_send_ports):
            if port.dimension == un.current:
                trfrm.remove(port)
        # -----------------------------------------------------------------
        # Insert membrane capacitance if not present
        # -----------------------------------------------------------------
        # Get or guess the location of the membrane capacitance
        try:
            name = kwargs['membrane_capacitance']
            try:
                orig_cm = component_class.parameter(name)
            except KeyError:
                raise Pype9BuildError(
                    "Could not find specified membrane capacitance '{}'"
                    .format(name))
            cm = trfrm.parameter(orig_cm.name)
        except KeyError:  # 'membrane_capacitance' was not specified
            candidate_cms = [ccm for ccm in component_class.parameters
                             if ccm.dimension == un.capacitance]
            if len(candidate_cms) == 1:
                orig_cm = candidate_cms[0]
                cm = trfrm.parameter(orig_cm.name)
                logger.info("Guessing that '{}' is the membrane capacitance"
                            .format(orig_cm))
            elif len(candidate_cms) > 1:
                raise Pype9BuildError(
                    "Could not guess the membrane capacitance, candidates:"
                    " '{}'".format("', '".join(candidate_cms)))
            else:
                cm = Parameter("cm___pype9", dimension=un.capacitance)
                trfrm.add(cm)
#                 qty = kwargs.get('default_capacitance', 1.0 * un.nF)
#                 if trfrm_properties:
#                     trfrm_properties.add(Property('cm___pype9', qty))
            cm.annotations.set((BUILD_TRANS, PYPE9_NS), TRANSFORM_SRC, None)
        trfrm.annotations.set((BUILD_TRANS, PYPE9_NS),
                              MEMBRANE_CAPACITANCE, cm.name)
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
        clamp_i = sympy.sympify('g_clamp___pype9 * (v - v_clamp___pype9)')
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
            regime.add(Alias('i___pype9', i))
            # Record state vars that have a time deriv. in this regime
            for var in regime.time_derivative_variables:
                if var != 'v':
                    has_td[var].append(regime)
        # Pick the most popular membrane current to be the alias in
        # the global scope
        assert memb_is, "No regimes contain voltage time derivatives"
        memb_i = Alias('i___pype9', max(memb_is, key=memb_is.count))
        # Add membrane current along with a analog send port
        trfrm.add(memb_i)
        i_port = AnalogSendPort('i___pype9', dimension=un.current)
        i_port.annotations.set((BUILD_TRANS, PYPE9_NS), ION_SPECIES,
                               NONSPECIFIC_CURRENT)
        trfrm.add(i_port)
        # Remove membrane currents that match the membrane current in the
        # outer scope
        for regime in trfrm.regimes:
            if regime.alias('i___pype9') == memb_i:
                regime.remove(regime.alias('i___pype9'))
        # If there are clamped regimes add extra parameters and set the
        # voltage to clamp to in the regimes that trfrmition to them
        if clamped_regimes:
            trfrm.add(StateVariable('v_clamp___pype9', un.voltage))
            trfrm.add(Constant('g_clamp___pype9', 1e8, un.uS))
            for trans in trfrm.transitions:
                if trans.target_regime in clamped_regimes:
                    # Assign v_clamp_ to the value
                    try:
                        v_clamp_rhs = trans.state_assignment('v').rhs
                    except KeyError:
                        v_clamp_rhs = 'v'
                    trans.add(StateAssignment('v_clamp___pype9',
                                              v_clamp_rhs))
        # -----------------------------------------------------------------
        trfrm.annotations.set(
            (BUILD_TRANS, PYPE9_NS), NO_TIME_DERIVS,
            ','.join(['v'] + [sv for sv in trfrm.state_variable_names
                              if sv not in has_td]))
        trfrm.annotations.set((BUILD_TRANS, PYPE9_NS), NUM_TIME_DERIVS,
                              len(has_td))
        # -----------------------------------------------------------------
        # Remove the external input currents
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
            ext_is = []
            for port in chain(component_class.analog_receive_ports,
                              component_class.analog_reduce_ports):
                # Check to see if the receive/reduce port has current dimension
                if port.dimension != un.current:
                    continue
                # Check to see if the current appears in the membrane current
                # expression
                # FIXME: This test should check to to see if the port is
                #        additive to the membrane current and substitute all
                #        aliases.
                if port.name not in memb_i.rhs_symbol_names:
                    continue
                # Get the number of expressions the receive port appears in
                # an expression
                if len([e for e in component_class.all_expressions
                        if port.symbol in e.free_symbols]) > 1:
                    continue
                # If all those conditions are met guess that port is a external
                # current that can be removed (ports that don't meet these
                # conditions will have to be specified separately)
                ext_is.append(port)
            if ext_is:
                logger.info("Guessing '{}' are external currents to be removed"
                            .format(ext_is))
        trfrm.annotations.set((BUILD_TRANS, PYPE9_NS), EXTERNAL_CURRENTS,
                              ','.join(p.name for p in ext_is))
        # Remove external input current ports (as NEURON handles them)
        for ext_i in ext_is:
            trfrm.remove(ext_i)
            for expr in chain(trfrm.aliases, trfrm.all_time_derivatives()):
                expr.subs(ext_i, 0)
                expr.simplify()

    def compile_source_files(self, compile_dir, name):
        """
        Builds all NMODL files in a directory

        Parameters
        ----------
        src_dir : str
            The path of the directory to build
        build_mode : str
            Can be one of either, 'lazy', 'super_lazy', 'require', 'force', or
            'build_only'. 'lazy' doesn't run nrnivmodl if the library is found,
            'require', requires that the library is found otherwise throws an
            exception (useful on clusters that require precompilation before
            parallelisation where the error message could otherwise be
            confusing), 'force' removes existing library if found and
            recompiles, and 'build_only' removes existing library if found,
            recompile and then exit
        ignore_units :
            Flag whether to only print a warning when units don't match instead
            of throwing an error
        """
        # Change working directory to model directory
        os.chdir(compile_dir)
        logger.info("Building NMODL mechanisms in '{}' directory."
                    .format(compile_dir))
        # Check the created units by running modlunit
        if __debug__:
            for fname in os.listdir('.'):
                if fname.endswith('.mod'):
                    try:
                        pipe = sp.Popen(
                            [self.modlunit_path, fname], stdout=sp.PIPE,
                            stderr=sp.PIPE)
                        stdout, stderr = pipe.communicate()
                        assert '<<ERROR>>' not in stderr, (
                            "Incorrect units assigned in NMODL file:\n {}{}"
                            .format(stdout, stderr))
                    except sp.CalledProcessError as e:
                        raise Pype9BuildError(
                            "Could not run 'modlunit' to check dimensions in "
                            "NMODL file: {}\n{}".format(stdout, stderr))
        # Run nrnivmodl command in src directory
        try:
            nrnivmodl_cmd = [self.nrnivmodl_path, '-loadflags',
                             ' '.join(self.nrnivmodl_flags)]
            logger.debug("Building nrnivmodl in {} with '{}'".format(
                compile_dir, ' '.join(nrnivmodl_cmd)))
            pipe = sp.Popen(nrnivmodl_cmd, stdout=sp.PIPE, stderr=sp.PIPE)
            stdout, stderr = pipe.communicate()
        except sp.CalledProcessError as e:
            raise Pype9BuildError(
                "Compilation of NMODL files for '{}' model failed. See src "
                "directory '{}':\n\n{}".format(name, compile_dir, e))
        if stderr.strip().endswith('Error 1'):
            raise Pype9BuildError(
                "Generated mod file failed to compile with output:\n{}\n{}"
                .format(stdout, stderr))
        logger.debug(stdout)
        logger.debug(stderr)
        logger.info("Compilation of NEURON (NMODL) files for '{}' "
                    "completed successfully".format(name))

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

    def assign_str(self, lhs, rhs):
        rhs = Expression.expand_integer_powers(rhs)
        nmodl_str = ccode(rhs, user_functions=Expression._cfunc_map,
                          assign_to=lhs)
        nmodl_str = Expression.strip_L_from_rationals(nmodl_str)
        nmodl_str = nmodl_str.replace(';', '')
        return nmodl_str
