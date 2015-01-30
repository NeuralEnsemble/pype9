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
import platform
import tempfile
import uuid
import subprocess as sp
import quantities as pq
from .. import BaseCodeGenerator
import nineml.abstraction_layer.units as un
from pype9.exceptions import Pype9BuildError


if 'NRNHOME' in os.environ:
    os.environ['PATH'] += (os.pathsep +
                           os.path.join(os.environ['NRNHOME'],
                                        platform.machine(), 'bin'))
else:
    try:
        if os.environ['HOME'] == '/home/tclose':
            # I apologise for this little hack (this is the path on my machine,
            # to save me having to set the environment variable in eclipse)
            os.environ['PATH'] += os.pathsep + '/opt/NEURON/nrn-7.3/x86_64/bin'
    except KeyError:
        pass


class CodeGenerator(BaseCodeGenerator):

    SIMULATOR_NAME = 'neuron'
    _DEFAULT_SOLVER = 'derivimplicit'
    _TMPL_PATH = os.path.join(os.path.dirname(__file__), 'jinja_templates')

    _neuron_units = {un.mV: 'millivolt',
                     un.S: 'siemens',
                     un.mA: 'milliamp'}

    _inbuilt_ions = ['na', 'k', 'ca']

    def __init__(self):
        super(CodeGenerator, self).__init__()
        # Find the path to nrnivmodl
        self.nrnivmodl_path = self._path_to_exec('nrnivmodl')
        # Work out the name of the installation directory for the compiled
        # NMODL files on the current platform
        self.specials_dir = self._get_specials_dir()

    def _extract_template_args(self, component, initial_state,  # @UnusedVariable @IgnorePep8
                               **template_args):
        model = component.component_class
        args = super(CodeGenerator, self)._extract_template_args(
            component, **template_args)
        args['ode_solver'] = template_args.get('ode_solver', 'derivimplicit')
        args['point_process'] = False
        args['parameter_names'] = list(p.name for p in model.parameters)
        args['alias_names'] = list(a.lhs for a in model.aliases)
        args['state_variable_names'] = list(s.name
                                            for s in model.state_variables)
# <<<<<<< HEAD
        args['properties'] = component.properties.values()
        args['analog_send_ports'] = [p.name for p in model.analog_send_ports]
        # Set dynamics --------------------------------------------------------
        dynamics = []
        for regime in model.dynamics.regimes:
            # Get name for regime dynamics function ---------------------------
            regime_name = regime.name or 'default'
            req_defs = self._required_defs(regime.time_derivatives, model)
            dynamics.append((regime_name, regime.time_derivatives, req_defs))
#         used_neuron_units = []
#         for ref_unit, ref_name in self._neuron_units.iteritems():
#             divides = False
#             ref_quantity = pq.Quantity(1, ref_unit.symbol)
#             for unit in componentclass.used_units:
#
#         args['used_units'] = list((u.name, self._neuron_units[u])
#                                   for u in componentclass.used_units
#                                   if u in self._neuron_units)
# =======
#         used_neuron_units = []
#         for ref_unit, ref_name in self._neuron_units.iteritems():
#             divides = False
#             ref_quantity = pq.Quantity(1, ref_unit.symbol)
#             for unit in componentclass.used_units:
#
#                 args['used_units'] = list((u.name, self._neuron_units[u])
#                                           for u in componentclass.used_units
#                                           if u in self._neuron_units)
# >>>>>>> 8fbf6059bb26792785d4b22d7eadf1c5a6070cb9
        # Sort ports by dimension ---------------------------------------------
        current_in = {}
        voltage_in = {}
        concentration_in = {}
        other_in_ports = []
        # FIXME: Guesses ion species from name (assuming Hoc syntax), this
        # should be done from annotations inserted on import or from the cell
        # class.
        for p in chain(model.analog_receive_ports, model.analog_reduce_ports):
            if p.dimension == un.currentDensity and p.name.startswith('i'):
                current_in[p.name[1:]] = p
            elif p.dimension == un.voltage and p.name.startswith('e'):
                voltage_in[p.name[1:]] = p
            elif p.dimension == un.concentration and (p.name.endswith('i') or
                                                      p.name.endswith('o')):
                concentration_in[p.name[:-1]] = p
            else:
                other_in_ports.append(p)
        current_out = {}
        concentration_out = {}
        other_out_ports = []
        for p in model.analog_send_ports:
            if p.dimension == un.currentDensity and p.name.startswith('i'):
                current_out[p.name[1:]] = p
            elif p.dimension == un.concentration and (p.name.endswith('i') or
                                                      p.name.endswith('o')):
                concentration_out[p.name[:-1]] = p
            else:
                other_out_ports.append(p)
        used_ions = set(chain(current_in.iterkeys(),
                              voltage_in.iterkeys(),
                              concentration_in.iterkeys(),
                              current_out.iterkeys(),
                              concentration_out.iterkeys()))
        ion_read_writes = []
        for ion in used_ions:
            read = []
            if ion in current_in:
                read.append(current_in[ion].name)
            if ion in voltage_in:
                read.append(voltage_in[ion].name)
            if ion in concentration_in:
                read.append(concentration_in[ion].name)
            write = []
            if ion in current_out:
                write.append(current_out[ion].name)
            if ion in concentration_out:
                write.append(concentration_out[ion].name)
            ion_read_writes.append((ion, read, write, None))
        args['ion_read_writes'] = ion_read_writes
        args['incoming_analog_ports'] = list(p.name for p in other_in_ports
                                             if p.name not in ('celsius', 'v'))
        return args

    def _render_source_files(self, template_args, src_dir, _, _, verbose):  # @UnusedVariable @IgnorePep8
        model_name = template_args['ModelName']
        # Render mod file
        self._render_to_file('main.tmpl', template_args, model_name + '.mod',
                             src_dir)

    def compile_source_files(self, compile_dir, component_name, verbose):
        """
        Builds all NMODL files in a directory
        @param src_dir: The path of the directory to build
        @param build_mode: Can be one of either, 'lazy', 'super_lazy',
                           'require', 'force', or 'build_only'. 'lazy' doesn't
                           run nrnivmodl if the library is found, 'require',
                           requires that the library is found otherwise throws
                           an exception (useful on clusters that require
                           precompilation before parallelisation where the
                           error message could otherwise be confusing), 'force'
                           removes existing library if found and recompiles,
                           and 'build_only' removes existing library if found,
                           recompile and then exit
        @param verbose: Prints out verbose debugging messages
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
                "directory '{}':\n ".format(component_name, compile_dir, e))

    def _get_install_dir(self, build_dir, install_dir):
        if install_dir:
            raise Pype9BuildError(
                "Cannot specify custom installation directory ('{}') for "
                "NEURON simulator as it needs to be located as a specifically "
                "named directory of the src directory (e.g. x86_64 for 64b "
                "unix/linux)".format(install_dir))
        # return the platform-specific location of the nrnivmodl output files
        return os.path.abspath(os.path.join(build_dir, self._SRC_DIR,
                                            self.specials_dir))

    def _get_compile_dir(self, build_dir):
        """
        The compile dir is the same as the src dir for NEURON compile
        """
        return os.path.abspath(os.path.join(build_dir, self._SRC_DIR))

    def _clean_compile_dir(self, compile_dir):
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

    def _simulator_specific_paths(self):
        path = []
        if 'NRNHOME' in os.environ:
            path.append(os.path.join(os.environ['NRNHOME'], self.specials_dir,
                                     'bin'))
        return path

# output_Na = template.render (functionDefs = [{'indent' : 2, 'name' : '''Na_bmf''', 'vars' : ['''v'''], 'localVars' : [], 'exprString' : '''Na_bmf  =  Na_A_beta_m * exp(-(v + -(Na_B_beta_m)) / Na_C_beta_m)'''}, 
#                                              {'indent' : 2, 'name' : '''Na_amf''', 'vars' : ['''v'''], 'localVars' : [], 'exprString' : '''Na_amf  =  Na_A_alpha_m *  (v + -(Na_B_alpha_m)) / (1.0 + -(exp(-(v + -(Na_B_alpha_m)) / Na_C_alpha_m)))'''}, 
#                                              {'indent' : 2, 'name' : '''Na_bhf''', 'vars' : ['''v'''], 'localVars' : [], 'exprString' : '''Na_bhf  =    Na_A_beta_h / (1.0 + exp(-(v + -(Na_B_beta_h)) / Na_C_beta_h))'''}, 
#                                              {'indent' : 2, 'name' : '''Na_ahf''', 'vars' : ['''v'''], 'localVars' : [], 'exprString' : '''Na_ahf  =  Na_A_alpha_h * exp(-(v + -(Na_B_alpha_h)) / Na_C_alpha_h)'''}],
#                              transientEventEqDefs = [],
#                              externalEventEqDefs = [],
#                              eventVars = [],
#                              eventLocals = [],
#                              initEqDefs = ['''Na_m45  =  (Na_amf(comp19_Vrest)) / (Na_amf(comp19_Vrest) + Na_bmf(comp19_Vrest))''',
#                                            '''Na_m45O  =  Na_m45''', '''Na_h46  =  (Na_ahf(comp19_Vrest)) / (Na_ahf(comp19_Vrest) + Na_bhf(comp19_Vrest))''', '''Na_h46O  =  Na_h46'''],
#                              initEqLocals = [],
#                              reversalPotentialEqDefs = [],
#                              kineticEqDefs = [],
#                              kineticEqLocals = [],
#                              externalEqDefs = [],
#                              rateEqDefs = ['''v100  =  Na_m45O
#                              Na_m45O'  =  (1.0 - v100) * (Na_amf(v)) - Na_m45O * Na_bmf(v)''', '''v102  =  Na_h46O
#                              Na_h46O'  =  (1.0 - v102) * (Na_ahf(v)) - Na_h46O * Na_bhf(v)'''],
#                              rateEqLocals = ['''v100''', '''v102'''],
#                              reactionEqDefs = ['''Na_h46  =  Na_h46O''', '''Na_m45  =  Na_m45O'''],
#                              reactionEqLocals = [],
#                              assignedEqDefs = ['''ena  =  Na_erev'''],
#                              assignedEqLocals = [],
#                              assignedDefs = ['''v''', '''ina''', '''ena''', '''i_Na'''],
#                              stateDefs = ['''Na_h46C''', '''Na_h46O''', '''Na_m45C''', '''Na_m45O''', '''Na_h46''', '''Na_m45'''],
#                              parameterDefs = ['''Na_g  =  0.12''', '''Na_e  =  50.0''', '''Na_erev  =  50.0''', '''comp19_Vrest  =  -65.0''', '''Na_A_alpha_m  =  0.1''', '''comp20_C  =  1.0''', '''Na_A_alpha_h  =  0.07''', '''Na_C_alpha_h  =  20.0''', '''Na_C_alpha_m  =  10.0''', '''Na_gbar  =  0.12''', '''Na_B_alpha_h  =  -65.0''', '''Na_B_alpha_m  =  -40.0''', '''Na_C_beta_m  =  18.0''', '''Na_C_beta_h  =  10.0''', '''Na_A_beta_m  =  4.0''', '''comp19_V_t  =  -35.0''', '''Na_A_beta_h  =  1.0''', '''Na_B_beta_m  =  -65.0''', '''Na_B_beta_h  =  -35.0'''],
#                              parameterLocals = [],
#                              rangeParameters = ['''Na_C_alpha_h''', '''Na_B_alpha_h''', '''Na_A_alpha_h''', '''Na_C_beta_h''', '''Na_B_beta_h''', '''Na_A_beta_h''', '''Na_C_alpha_m''', '''Na_B_alpha_m''', '''Na_A_alpha_m''', '''Na_C_beta_m''', '''Na_B_beta_m''', '''Na_A_beta_m''', '''Na_erev'''],
#                              useIons = [{'nonSpecific' : False, 'name' : '''na''', 'read' : ['''ena'''], 'write' : ['''ina'''], 'valence' : False}],
#                              poolIons = [],
#                              accumulatingIons = [],
#                              modulatingIons = [],
#                              permeatingIons = [{'species' : '''na''', 'i' : '''ina''', 'e' : '''ena''', 'erev' : '''Na:erev''', 'valence' : False}],
#                              currentEqDefs = ['''i_Na  =  (Na_gbar * Na_m45 ^ 3.0 * Na_h46) * (v - Na_erev)''', '''ina  =  i_Na'''],
#                              currentEqLocals = [],
#                              currents = ['''i_Na'''],
#                              exports = ['''comp19_Vrest''', '''comp19_V_t''', '''comp20_C''', '''Na_erev''', '''Na_gbar''', '''Na_m45''', '''Na_h46'''],
#                              hasEvents = False,
#                              nemoVersionString = '''NEMO (http://wiki.call-cc.org/nemo) version 9.0''',
#                              currentTimestamp = '''Thu Oct 23 14:06:12 2014''',
#                              modelName = '''hodgkin_huxley_Na''',
#                              ODEmethod = '''cnexp''',
#                              indent = 2)

# output_K = template.render (functionDefs = [{'indent' : 2, 'name' : '''K_bnf''', 'vars' : ['''v'''], 'localVars' : [], 'exprString' : '''K_bnf  =  K_A_beta_n * exp(-(v + -(K_B_beta_n)) / K_C_beta_n)'''}, 
#                                              {'indent' : 2, 'name' : '''K_anf''', 'vars' : ['''v'''], 'localVars' : [], 'exprString' : '''K_anf  =  
#   K_A_alpha_n * 
#     (v + -(K_B_alpha_n)) / 
#       (1.0 + -(exp(-(v + -(K_B_alpha_n)) / K_C_alpha_n)))'''}],
#                              transientEventEqDefs = [],
#                              externalEventEqDefs = [],
#                              eventVars = [],
#                              eventLocals = [],
#                              initEqDefs = ['''K_m79  =  
#                              (K_anf(comp61_Vrest)) / (K_anf(comp61_Vrest) + K_bnf(comp61_Vrest))''', '''K_m79O  =  K_m79'''],
#                              initEqLocals = [],
#                              reversalPotentialEqDefs = [],
#                              kineticEqDefs = [],
#                              kineticEqLocals = [],
#                              externalEqDefs = [],
#                              rateEqDefs = ['''v104  =  K_m79O
#                              K_m79O'  =  (1.0 - v104) * (K_anf(v)) - K_m79O * K_bnf(v)'''],
#                              rateEqLocals = ['''v104'''],
#                              reactionEqDefs = ['''K_m79  =  K_m79O'''],
#                              reactionEqLocals = [],
#                              assignedEqDefs = ['''ek  =  K_erev'''],
#                              assignedEqLocals = [],
#                              assignedDefs = ['''v''', '''ik''', '''ek''', '''i_K'''],
#                              stateDefs = ['''K_m79C''', '''K_m79O''', '''K_m79'''],
#                              parameterDefs = ['''K_A_alpha_n  =  0.01''', '''K_A_beta_n  =  0.125''', '''comp61_V_t  =  -35.0''', '''K_B_alpha_n  =  -55.0''', '''K_gbar  =  0.036''', '''comp61_Vrest  =  -65.0''', '''K_B_beta_n  =  -65.0''', '''comp62_C  =  1.0''', '''K_C_alpha_n  =  10.0''', '''K_erev  =  -77.0''', '''K_e  =  -77.0''', '''K_g  =  0.036''', '''K_C_beta_n  =  80.0'''],
#                              parameterLocals = [],
#                              rangeParameters = ['''K_C_alpha_n''', '''K_B_alpha_n''', '''K_A_alpha_n''', '''K_C_beta_n''', '''K_B_beta_n''', '''K_A_beta_n''', '''K_erev'''],
#                              useIons = [{'nonSpecific' : False, 'name' : '''k''', 'read' : ['''ek'''], 'write' : ['''ik'''], 'valence' : False}],
#                              poolIons = [],
#                              accumulatingIons = [],
#                              modulatingIons = [],
#                              permeatingIons = [{'species' : '''k''', 'i' : '''ik''', 'e' : '''ek''', 'erev' : '''K:erev''', 'valence' : False}],
#                              currentEqDefs = ['''i_K  =  (K_gbar * K_m79 ^ 4.0) * (v - K_erev)''', '''ik  =  i_K'''],
#                              currentEqLocals = [],
#                              currents = ['''i_K'''],
#                              exports = ['''comp61_Vrest''', '''comp61_V_t''', '''comp62_C''', '''K_gbar''', '''K_erev''', '''K_m79'''],
#                              hasEvents = False,
#                              nemoVersionString = '''NEMO (http://wiki.call-cc.org/nemo) version 9.0''',
#                              currentTimestamp = '''Thu Oct 23 14:06:12 2014''',
#                              modelName = '''hodgkin_huxley_K''',
#                              ODEmethod = '''cnexp''',
#                              indent = 2)


# output_Leak = template.render (functionDefs = [],
#                                transientEventEqDefs = [],
#                                externalEventEqDefs = [],
#                                eventVars = [],
#                                eventLocals = [],
#                                initEqDefs = [],
#                                initEqLocals = [],
#                                reversalPotentialEqDefs = ['''e  =  Leak_erev'''],
#                                kineticEqDefs = [],
#                                kineticEqLocals = [],
#                                externalEqDefs = [],
#                                rateEqDefs = [],
#                                rateEqLocals = [],
#                                reactionEqDefs = [],
#                                reactionEqLocals = [],
#                                assignedEqDefs = ['''e  =  Leak_erev'''],
#                                assignedEqLocals = [],
#                                assignedDefs = ['''v''', '''i''', '''e''', '''i_Leak'''],
#                                stateDefs = [],
#                                parameterDefs = ['''comp94_Vrest  =  -65.0''', '''Leak_e  =  -54.4''', '''Leak_g  =  0.0003''', '''comp94_V_t  =  -35.0''', '''Leak_erev  =  -54.4''', '''Leak_gbar  =  0.0003''', '''comp95_C  =  1.0'''],
#                                parameterLocals = [],
#                                rangeParameters = ['''Leak_erev'''],
#                                useIons = [{'nonSpecific' : True, 'name' : '''i'''}],
#                                poolIons = [],
#                                accumulatingIons = [],
#                                modulatingIons = [],
#                                permeatingIons = [{'species' : '''non-specific''', 'i' : '''i''', 'e' : '''e''', 'erev' : '''Leak:erev''', 'valence' : False}],
#                                currentEqDefs = ['''i_Leak  =  Leak_gbar * (v - Leak_erev)''', '''i  =  i_Leak'''],
#                                currentEqLocals = [],
#                                currents = ['''i_Leak'''],
#                                exports = ['''comp94_Vrest''', '''comp94_V_t''', '''comp95_C''', '''Leak_gbar''', '''Leak_erev'''],
#                                hasEvents = False,
#                                nemoVersionString = '''NEMO (http://wiki.call-cc.org/nemo) version 9.0''',
#                                currentTimestamp = '''Thu Oct 23 14:06:12 2014''',
#                                modelName = '''hodgkin_huxley_Leak''',
#                                ODEmethod = '''cnexp''',
#                                indent = 2)
