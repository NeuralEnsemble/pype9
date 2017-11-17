"""

  This module contains functions for building and loading NMODL mechanisms

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
from __future__ import unicode_literals
from builtins import next, str
import os.path
import tempfile
import platform
import re
import uuid
from itertools import chain
import subprocess as sp
from collections import defaultdict
import sympy
import neuron
import nineml.units as un
from nineml.abstraction import Alias, AnalogSendPort, Dynamics
from neuron import load_mechanisms
from pype9.simulate.common.code_gen import BaseCodeGenerator
from pype9.simulate.common.cells import (
    WithSynapses, DynamicsWithSynapses)
from pype9.exceptions import (
    Pype9BuildError, Pype9RuntimeError, Pype9CommandNotFoundError)
import pype9
from datetime import datetime
from nineml.abstraction import (StateAssignment, Parameter, StateVariable,
                                Constant, Expression)
from nineml.abstraction.dynamics.visitors.queriers import (
    DynamicsInterfaceInferer)
from sympy.printing import ccode
from pype9.utils.mpi import is_mpi_master, mpi_comm
from pype9.simulate.neuron.units import UnitHandler
try:
    from nineml.extensions.kinetics import Kinetics  # @UnusedImport
except ImportError:
    KineticsClass = type(None)
from pype9.annotations import (
    PYPE9_NS, ION_SPECIES, MEMBRANE_VOLTAGE, MEMBRANE_CAPACITANCE,
    TRANSFORM_SRC, NONSPECIFIC_CURRENT, BUILD_TRANS,
    EXTERNAL_CURRENTS, NO_TIME_DERIVS,
    NUM_TIME_DERIVS, MECH_TYPE, FULL_CELL_MECH,
    ARTIFICIAL_CELL_MECH)
import logging

TRANSFORM_NS = 'NeuronBuildTransform'

logger = logging.getLogger("pype9")


class CodeGenerator(BaseCodeGenerator):

    SIMULATOR_NAME = 'neuron'
    SIMULATOR_VERSION = neuron.h.nrnversion(0)
    ODE_SOLVER_DEFAULT = 'derivimplicit'
    REGIME_VARNAME = 'regime_'
    SEED_VARNAME = 'seed_'
    BASE_TMPL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                  'templates'))
    UnitHandler = UnitHandler

    _neuron_units = {un.mV: 'millivolt',
                     un.S: 'siemens',
                     un.mA: 'milliamp'}

    _inbuilt_ions = ['na', 'k', 'ca']

    def __init__(self, gsl_path=None, **kwargs):
        super(CodeGenerator, self).__init__(**kwargs)
        self.nrnivmodl_path = self.get_neuron_util_path('nrnivmodl')
        self.modlunit_path = self.get_neuron_util_path('modlunit',
                                                       default=None)
        # Compile wrappers around GSL random distribution functions
        if is_mpi_master():
            if not os.path.exists(self.libninemlnrn_so):
                self.compile_libninemlnrn()
        mpi_comm.barrier()
        self.nrnivmodl_flags = [
            '-L' + self.libninemlnrn_dir,
            '-Wl,-rpath,' + self.libninemlnrn_dir,
            '-lninemlnrn', '-lgsl', '-lgslcblas']
        if gsl_path is not None:
            self.nrnivmodl_path.append('-L' + gsl_path)
        else:
            self.nrnivmodl_flags.extend(self.get_gsl_prefixes())
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
        # Get list of all unique triggers within the component class so they
        # can be referred to by an index (i.e. their index in the list).
        all_triggers = []
        for regime in component_class.regimes:
            for on_condition in regime.on_conditions:
                if on_condition.trigger.rhs not in all_triggers:
                    all_triggers.append(on_condition.trigger.rhs)
        tmpl_args = {
            'code_gen': self,
            'component_name': name,
            'component_class': component_class,
            'all_triggers': all_triggers,
            'version': pype9.__version__, 'src_dir': src_dir,
            'timestamp': datetime.now().strftime('%a %d %b %y %I:%M:%S%p'),
            'unit_handler': UnitHandler(component_class),
            'ode_solver': self.ODE_SOLVER_DEFAULT,
            'external_ports': [],
            'is_subcomponent': True,
            'regime_varname': self.REGIME_VARNAME,
            'seed_varname': self.SEED_VARNAME}
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
        trfrm = component_class.dynamics.flatten()
        # ---------------------------------------------------------------------
        # Get the membrane voltage and convert it to 'v'
        # ---------------------------------------------------------------------
        try:
            name = kwargs['membrane_voltage']
            try:
                orig_v = component_class.element(
                    name, nineml_children=Dynamics.nineml_children)
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
        # Insert dummy aliases for parameters (such as capacitance) that
        # now do not show up in the inferred interface for the transformed
        # class (i.e. that were only # present in the voltage time derivative)
        # -----------------------------------------------------------------

        # Infer required parameters
        inferred = DynamicsInterfaceInferer(trfrm)

        for parameter in list(trfrm.parameters):
            if parameter.name not in inferred.parameter_names:
                trfrm.add(Alias(parameter.name + '___dummy', parameter.name))

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
        if __debug__ and self.modlunit_path is not None:
            for fname in os.listdir('.'):
                if fname.endswith('.mod'):
                    try:
                        stdout, stderr = self.run_command([self.modlunit_path,
                                                           fname])
                        assert '<<ERROR>>' not in stderr, (
                            "Incorrect units assigned in NMODL file:\n {}{}"
                            .format(stdout, stderr))
                    except sp.CalledProcessError as e:
                        raise Pype9BuildError(
                            "Could not run 'modlunit' to check dimensions in "
                            "NMODL file: {}\n{}".format(fname, e))
        # Run nrnivmodl command in src directory
        nrnivmodl_cmd = [self.nrnivmodl_path, '-loadflags',
                         ' '.join(self.nrnivmodl_flags)]
        logger.debug("Building nrnivmodl in {} with {}".format(
            compile_dir, nrnivmodl_cmd))
        self.run_command(nrnivmodl_cmd, fail_msg=(
            "Compilation of NMODL files for '{}' model failed. See src "
            "directory '{}':\n\n{{}}".format(name, compile_dir)))
        if stderr.strip().endswith('Error 1'):
            raise Pype9BuildError(
                "Generated mod file failed to compile with output:\n{}\n{}"
                .format(stdout, stderr))
        logger.info("Compilation of NEURON (NMODL) files for '{}' "
                    "completed successfully".format(name))

    def get_install_dir(self, name, url):
        # return the platform-specific location of the nrnivmodl output files
        return os.path.join(self.get_source_dir(name, url), self.specials_dir)

    def get_compile_dir(self, name, url):
        """
        The compile dir is the same as the src dir for NEURON compile
        """
        return self.get_source_dir(name, url)

    def load_libraries(self, name, url):
        install_dir = self.get_install_dir(name, url)
        load_mechanisms(os.path.dirname(install_dir))

    def clean_compile_dir(self, *args, **kwargs):
        pass  # NEURON doesn't use a separate compile dir

    def _get_specials_dir(self):
        # Create a temporary directory to run nrnivmodl in
        tmp_dir_path = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
        try:
            os.mkdir(tmp_dir_path)
        except OSError:
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

    @property
    def libninemlnrn_dir(self):
        return os.path.join(self.base_dir, 'libninemlnrn')

    @property
    def libninemlnrn_so(self):
        return os.path.join(self.libninemlnrn_dir, 'libninemlnrn.so')

    def compile_libninemlnrn(self):
        """
        Complies libninemlnrn for random distribution support in generated
        NMODL mechanisms
        """
        logger.info("Attempting to build libninemlnrn")
        cc = self.get_cc()
        gsl_prefixes = self.get_gsl_prefixes()
        # Compile libninemlnrn
        compile_cmd = ('{} -fPIC -c -o ninemlnrn.o {}/ninemlnrn.cpp {}'
                       .format(cc, self.BASE_TMPL_PATH,
                               ' '.join('-I{}/include'.format(p)
                                        for p in gsl_prefixes)))
        os.makedirs(self.libninemlnrn_dir)
        self.run_cmd(
            compile_cmd, work_dir=self.libninemlnrn_dir,
            fail_msg=("Unable to compile libninemlnrn extensions"))
        # Link libninemlnrn
        if platform.system() == 'Darwin':
            # On macOS '-install_name' option needs to be set to allow
            # rpath to find the compiled library
            install_name = "-install_name @rpath/libninemlnrn.so "
        else:
            install_name = ""
        link_cmd = (
            "{} -shared {} {} -lm -lgslcblas -lgsl "
            "-o libninemlnrn.so ninemlnrn.o -lc".format(
                cc, ' '.join('-L{}/lib'.format(p) for p in gsl_prefixes),
                install_name))
        self.run_cmd(
            link_cmd, work_dir=self.libninemlnrn_dir,
            fail_msg=("Unable to link libninemlnrn extensions"))
        logger.info("Successfully compiled libninemlnrn extension.")

    def run_cmd(self, cmd, work_dir, fail_msg):
        p = sp.Popen(cmd, shell=True, stdin=sp.PIPE, stdout=sp.PIPE,
                     stderr=sp.STDOUT, close_fds=True, cwd=work_dir)
        stdout = p.stdout.readlines()
        result = p.wait()
        # test if cmd was successful
        if result != 0:
            raise Pype9BuildError(
                "{}:\n{}".format(fail_msg, '  '.join([''] + stdout)))

    @classmethod
    def get_neuron_bin_path(cls):
        path = neuron.h.neuronhome()
        path_contents = os.listdir(path)
        if 'examples' in path_contents:  # returned NRNHOME/share/nrn
            nrnhome = os.path.join(path, '..', '..')
            if os.path.exists(os.path.join(nrnhome, 'x86_64')):
                bin_path = os.path.join(nrnhome, 'x86_64', 'bin')
            else:
                bin_path = os.path.join(nrnhome, 'bin')
        elif 'bin' in path_contents:
            bin_path = os.path.join(path, 'bin')
        elif 'nrnivmodl' in path_contents:
            bin_path = path
        if not os.path.exists(bin_path):
            raise Pype9BuildError(
                "Did not find NEURON 'bin' path at expected '{}' location"
                .format(bin_path))
        return bin_path

    @classmethod
    def get_neuron_util_path(cls, util_name, **kwargs):
        util_path = os.path.join(cls.get_neuron_bin_path(), util_name)
        if not os.path.exists(util_path):
            try:
                default_path = kwargs['default']
                logger.warning("Did not find '{}' at expected path"
                               .format(util_name, util_path))
                util_path = default_path
            except KeyError:
                raise Pype9BuildError(
                    "Did not find '{}' at expected path '{}'"
                    .format(util_name, util_path))
        return util_path

    def get_cc(self):
        """
        Get the C compiler used to compile NMODL files

        Returns
        -------
        cc : str
            Name of the C compiler used to compile NMODL files
        """
        # Get path to the nrnmech_makefile, should be next to nrnivmodl
        nrnmech_makefile_path = os.path.join(
            os.path.dirname(os.path.realpath(self.nrnivmodl_path)),
            'nrnmech_makefile')
        # Extract C-compiler used in nrnmech_makefile
        try:
            with open(nrnmech_makefile_path) as f:
                contents = f.read()
        except OSError:
            raise Pype9BuildError(
                "Could not read nrnmech_makefile at '{}'"
                .format(nrnmech_makefile_path))
        matches = re.findall(r'\s*CC\s*=\s*(.*)', contents)
        if len(matches) != 1:
            raise Pype9BuildError(
                "Could not extract CC variable from nrnmech_makefile at '{}'"
                .format(nrnmech_makefile_path))
        cc = matches[0]
        return cc

    def get_gsl_prefixes(self):
        """
        Get the library paths used to link GLS to PyNEST

        Returns
        -------
        lib_paths : list(str)
            List of library paths passed to the PyNEST compile
        """
        try:
            # Used to attempt to determine the location of the GSL library
            nest_config_path = self.path_to_utility('nest-config')
        except Pype9CommandNotFoundError:
            prefixes = []
        except sp.CalledProcessError:
            raise Pype9BuildError(
                "Could not run '{} --libs'".format(self.nest_config_path))
        else:
            libs = str(sp.check_output('{} --libs'.format(nest_config_path),
                                       shell=True))
            prefixes = [
                p[2:-3] for p in libs.split()
                if p.startswith('-L') and p.endswith('lib') and 'gsl' in p]
        return prefixes
