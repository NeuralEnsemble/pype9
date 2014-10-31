"""

  This module contains functions for building and loading nest modules

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
import time
import os.path
import subprocess as sp
import re
import shutil
from .. import BaseCodeGenerator
from nineline import __version__
from nineline.utils import remove_ignore_missing

# Add Nest installation directory to the system path
if 'NEST_INSTALL_DIR' in os.environ:
    os.environ['PATH'] += (os.pathsep +
                           os.path.join(os.environ['NEST_INSTALL_DIR'], 'bin'))
else:
    try:
        if os.environ['HOME'] == '/home/tclose':
            # I apologise for this little hack (this is the path on my machine,
            # to save me having to set the environment variable in eclipse)
            os.environ['PATH'] += os.pathsep + '/opt/NEST/2.2.1/bin'
    except KeyError:
        pass


class CodeGenerator(BaseCodeGenerator):

    SIMULATOR_NAME = 'nest'
    _DEFAULT_SOLVER = 'gsl'
    _TMPL_PATH = os.path.join(os.path.dirname(__file__), 'jinja_templates')

    def _extract_template_args(self, args, component, initial_state,
                               ode_method='gsl', v_threshold=None):
        model = component.component_class
        args['ModelName'] = model.name
        args['ODEmethod'] = ode_method
        parameter_names = [p.name for p in model.parameters]
        args['parameter_names'] = parameter_names
        args['parameter_init'] = ['NAN'] * len(parameter_names)  # TODO: Need to provide default values
        args['parameter_scales'] = {}  #TODO: Need to ask Ivan out why scaling is required in some cases
        state_names = [v.name for v in model.dynamics.state_variables]
        args['num_states'] = len(state_names)
        args['state_variables'] = state_names
        args['state_variables_init'] = [0.0] * len(state_names)  #TODO: Come up with initialisations
        args['parameter_constraints'] = [] #TODO: Add parameter constraints to model
        args['steady_state'] = False  # This needs to be implemented (difficult without "state layer")
        args['timestamp'] = time.strftime('%X %a %d %b %Y')
        args['version'] = __version__
        args['synaptic_events'] = [p.name for p in model.event_receive_ports]
        args['synaptic_event_pscIDs'] = ['UNKNOWN' for p in model.event_receive_ports]
        volt_states = [s.name for s in model.dynamics.state_variables
                       if s.dimension == 'voltage']
        if not volt_states:
            raise Exception("Did not find a state with dimension 'voltage' in "
                            "the list of state names so couldn't "
                            "determine the membrane voltage")
        elif len(volt_states) > 2:
            raise Exception("Found multiple states with dimension 'voltage' "
                            "({}) in the list of state names so couldn't "
                            "determine the membrane voltage"
                            .format(', '.join(volt_states)))
        else:
            args['membrane_voltage'] = volt_states[0]
        args['v_threshold'] = v_threshold
        args['parameters'] = {'localVars' : [],
                                'parameterEqDefs' : ['''K_erev  (-77.0)''', '''Na_C_alpha_h  (20.0)''', '''Na_C_alpha_m  (10.0)''', '''Na_A_alpha_h  (0.07)''', '''Na_gbar  (0.12)''', '''Na_A_alpha_m  (0.1)''', '''K_gbar  (0.036)''', '''K_B_alpha_n  (-55.0)''', '''K_e  (-77.0)''', '''Leak_erev  (-54.4)''', '''comp19_V_t  (-35.0)''', '''K_g  (0.036)''', '''K_A_alpha_n  (0.01)''', '''Na_erev  (50.0)''', '''comp20_C  (1.0)''', '''Na_C_beta_h  (10.0)''', '''K_C_beta_n  (80.0)''', '''Na_C_beta_m  (18.0)''', '''Na_A_beta_m  (4.0)''', '''comp19_Vrest  (-65.0)''', '''K_B_beta_n  (-65.0)''', '''Leak_gbar  (0.0003)''', '''Na_B_alpha_m  (-40.0)''', '''Na_A_beta_h  (1.0)''', '''Na_e  (50.0)''', '''Na_B_alpha_h  (-65.0)''', '''Na_g  (0.12)''', '''Na_B_beta_m  (-65.0)''', '''K_C_alpha_n  (10.0)''', '''Leak_g  (0.0003)''', '''K_A_beta_n  (0.125)''', '''Leak_e  (-54.4)''', '''Na_B_beta_h  (-35.0)'''],
                                'parameterDefs' : [{'name' : '''K_erev''', 'scale' : False},
                                                   {'name' : '''Na_C_alpha_h''', 'scale' : False},
                                                   {'name' : '''Na_C_alpha_m''', 'scale' : False},
                                                   {'name' : '''Na_A_alpha_h''', 'scale' : False},
                                                   {'name' : '''Na_gbar''', 'scale' : False},
                                                   {'name' : '''Na_A_alpha_m''', 'scale' : False},
                                                   {'name' : '''K_gbar''', 'scale' : False},
                                                   {'name' : '''K_B_alpha_n''', 'scale' : False},
                                                   {'name' : '''K_e''', 'scale' : False},
                                                   {'name' : '''Leak_erev''', 'scale' : False},
                                                   {'name' : '''comp19_V_t''', 'scale' : False},
                                                   {'name' : '''K_g''', 'scale' : False},
                                                   {'name' : '''K_A_alpha_n''', 'scale' : False},
                                                   {'name' : '''Na_erev''', 'scale' : False},
                                                   {'name' : '''comp20_C''', 'scale' : False},
                                                   {'name' : '''Na_C_beta_h''', 'scale' : False},
                                                   {'name' : '''K_C_beta_n''', 'scale' : False},
                                                   {'name' : '''Na_C_beta_m''', 'scale' : False},
                                                   {'name' : '''Na_A_beta_m''', 'scale' : False},
                                                   {'name' : '''comp19_Vrest''', 'scale' : False},
                                                   {'name' : '''K_B_beta_n''', 'scale' : False},
                                                   {'name' : '''Leak_gbar''', 'scale' : False},
                                                   {'name' : '''Na_B_alpha_m''', 'scale' : False},
                                                   {'name' : '''Na_A_beta_h''', 'scale' : False},
                                                   {'name' : '''Na_e''', 'scale' : False},
                                                   {'name' : '''Na_B_alpha_h''', 'scale' : False},
                                                   {'name' : '''Na_g''', 'scale' : False},
                                                   {'name' : '''Na_B_beta_m''', 'scale' : False},
                                                   {'name' : '''K_C_alpha_n''', 'scale' : False},
                                                   {'name' : '''Leak_g''', 'scale' : False},
                                                   {'name' : '''K_A_beta_n''', 'scale' : False},
                                                   {'name' : '''Leak_e''', 'scale' : False},
                                                   {'name' : '''Na_B_beta_h''', 'scale' : False}],
                                'defaultDefs': [{'name' : '''Vrest''', 'scale' : False},
                                                {'name' : '''V_t''', 'scale' : False}]}
        args['steadystate'] = {'localVars' : [
                                              '''v''',
                                              '''comp19_Vrest''', '''Na_h61''', '''Na_h61O''', '''K_m66''', '''K_m66O''', '''Na_m60''', '''Na_m60O''', '''i_K''', '''ik''', '''i_Na''', '''ina''', '''i_Leak''', '''i''', '''K_erev''', '''Na_C_alpha_h''', '''Na_C_alpha_m''', '''Na_A_alpha_h''', '''Na_gbar''', '''Na_A_alpha_m''', '''K_gbar''', '''K_B_alpha_n''', '''K_e''', '''Leak_erev''', '''comp19_V_t''', '''K_g''', '''K_A_alpha_n''', '''Na_erev''', '''comp20_C''', '''Na_C_beta_h''', '''K_C_beta_n''', '''Na_C_beta_m''', '''Na_A_beta_m''', '''K_B_beta_n''', '''Leak_gbar''', '''Na_B_alpha_m''', '''Na_A_beta_h''', '''Na_e''', '''Na_B_alpha_h''', '''Na_g''', '''Na_B_beta_m''', '''K_C_alpha_n''', '''Leak_g''', '''K_A_beta_n''', '''Leak_e''', '''Na_B_beta_h'''],
                               'parameterDefs' : ['''K_erev  =  params->K_erev;''', '''Na_C_alpha_h  =  params->Na_C_alpha_h;''', '''Na_C_alpha_m  =  params->Na_C_alpha_m;''', '''Na_A_alpha_h  =  params->Na_A_alpha_h;''', '''Na_gbar  =  params->Na_gbar;''', '''Na_A_alpha_m  =  params->Na_A_alpha_m;''', '''K_gbar  =  params->K_gbar;''', '''K_B_alpha_n  =  params->K_B_alpha_n;''', '''K_e  =  params->K_e;''', '''Leak_erev  =  params->Leak_erev;''', '''comp19_V_t  =  params->comp19_V_t;''', '''K_g  =  params->K_g;''', '''K_A_alpha_n  =  params->K_A_alpha_n;''', '''Na_erev  =  params->Na_erev;''', '''comp20_C  =  params->comp20_C;''', '''Na_C_beta_h  =  params->Na_C_beta_h;''', '''K_C_beta_n  =  params->K_C_beta_n;''', '''Na_C_beta_m  =  params->Na_C_beta_m;''', '''Na_A_beta_m  =  params->Na_A_beta_m;''', '''comp19_Vrest  =  params->comp19_Vrest;''', '''K_B_beta_n  =  params->K_B_beta_n;''', '''Leak_gbar  =  params->Leak_gbar;''', '''Na_B_alpha_m  =  params->Na_B_alpha_m;''', '''Na_A_beta_h  =  params->Na_A_beta_h;''', '''Na_e  =  params->Na_e;''', '''Na_B_alpha_h  =  params->Na_B_alpha_h;''', '''Na_g  =  params->Na_g;''', '''Na_B_beta_m  =  params->Na_B_beta_m;''', '''K_C_alpha_n  =  params->K_C_alpha_n;''', '''Leak_g  =  params->Leak_g;''', '''K_A_beta_n  =  params->K_A_beta_n;''', '''Leak_e  =  params->Leak_e;''', '''Na_B_beta_h  =  params->Na_B_beta_h;'''],
                               'SScurrentEqDefs' : ['''i_K  =  0.0;''', '''ik  =  0.0;''', '''i_Na  =  0.0;''', '''ina  =  0.0;''', '''i_Leak  =  0.0;''', '''i  =  0.0;'''],
                               'SSgetStateDefs' : [],
                               'SSsetStateDefsLbs' : []}
        args['init'] = {'localVars' : [
                                       '''v''', '''comp19_Vrest''', '''Na_h61''', '''Na_h61O''', '''K_m66''', '''K_m66O''', '''Na_m60''', '''Na_m60O''', '''i_K''', '''ik''', '''i_Na''', '''ina''', '''i_Leak''', '''i''', '''K_erev''', '''Na_C_alpha_h''', '''Na_C_alpha_m''', '''Na_A_alpha_h''', '''Na_gbar''', '''Na_A_alpha_m''', '''K_gbar''', '''K_B_alpha_n''', '''K_e''', '''Leak_erev''', '''comp19_V_t''', '''K_g''', '''K_A_alpha_n''', '''Na_erev''', '''comp20_C''', '''Na_C_beta_h''', '''K_C_beta_n''', '''Na_C_beta_m''', '''Na_A_beta_m''', '''K_B_beta_n''', '''Leak_gbar''', '''Na_B_alpha_m''', '''Na_A_beta_h''', '''Na_e''', '''Na_B_alpha_h''', '''Na_g''', '''Na_B_beta_m''', '''K_C_alpha_n''', '''Leak_g''', '''K_A_beta_n''', '''Leak_e''', '''Na_B_beta_h'''],
                        'parameterDefs' : ['''K_erev  =  p.K_erev;''', '''Na_C_alpha_h  =  p.Na_C_alpha_h;''', '''Na_C_alpha_m  =  p.Na_C_alpha_m;''', '''Na_A_alpha_h  =  p.Na_A_alpha_h;''', '''Na_gbar  =  p.Na_gbar;''', '''Na_A_alpha_m  =  p.Na_A_alpha_m;''', '''K_gbar  =  p.K_gbar;''', '''K_B_alpha_n  =  p.K_B_alpha_n;''', '''K_e  =  p.K_e;''', '''Leak_erev  =  p.Leak_erev;''', '''comp19_V_t  =  p.comp19_V_t;''', '''K_g  =  p.K_g;''', '''K_A_alpha_n  =  p.K_A_alpha_n;''', '''Na_erev  =  p.Na_erev;''', '''comp20_C  =  p.comp20_C;''', '''Na_C_beta_h  =  p.Na_C_beta_h;''', '''K_C_beta_n  =  p.K_C_beta_n;''', '''Na_C_beta_m  =  p.Na_C_beta_m;''', '''Na_A_beta_m  =  p.Na_A_beta_m;''', '''comp19_Vrest  =  p.comp19_Vrest;''', '''K_B_beta_n  =  p.K_B_beta_n;''', '''Leak_gbar  =  p.Leak_gbar;''', '''Na_B_alpha_m  =  p.Na_B_alpha_m;''', '''Na_A_beta_h  =  p.Na_A_beta_h;''', '''Na_e  =  p.Na_e;''', '''Na_B_alpha_h  =  p.Na_B_alpha_h;''', '''Na_g  =  p.Na_g;''', '''Na_B_beta_m  =  p.Na_B_beta_m;''', '''K_C_alpha_n  =  p.K_C_alpha_n;''', '''Leak_g  =  p.Leak_g;''', '''K_A_beta_n  =  p.K_A_beta_n;''', '''Leak_e  =  p.Leak_e;''', '''Na_B_beta_h  =  p.Na_B_beta_h;'''],
                        'initOrder' : ['''v  =  -65.0;''', '''Na_h61  =  (Na_ahf(comp19_Vrest, params)) / (Na_ahf(comp19_Vrest, params) + Na_bhf(comp19_Vrest, params));''', '''Na_h61O  =  Na_h61;''', '''K_m66  =  (K_anf(comp19_Vrest, params)) / (K_anf(comp19_Vrest, params) + K_bnf(comp19_Vrest, params));''', '''K_m66O  =  K_m66;''', '''Na_m60  =  (Na_amf(comp19_Vrest, params)) / (Na_amf(comp19_Vrest, params) + Na_bmf(comp19_Vrest, params));''', '''Na_m60O  =  Na_m60;'''],
                        'initEqDefs' : ['''y_[0]  =  v;''', '''y_[1]  =  Na_h61O;''', '''y_[2]  =  K_m66O;''', '''y_[3]  =  Na_m60O;'''],
                        'rateEqStates' : ['''v''', '''Na_h61O''', '''K_m66O''', '''Na_m60O'''],
                        'reactionEqDefs' : []}
        args['dynamics'] = {'localVars' : ['''v68''', '''v70''', '''v72''', '''Na_m60O''', '''Na_m60''', '''K_m66O''', '''K_m66''', '''Na_h61O''', '''Na_h61''', '''K_erev''', '''v''', '''K_gbar''', '''i_K''', '''ik''', '''Na_erev''', '''Na_gbar''', '''i_Na''', '''ina''', '''Leak_erev''', '''Leak_gbar''', '''i_Leak''', '''i''', '''Na_C_alpha_h''', '''Na_C_alpha_m''', '''Na_A_alpha_h''', '''Na_A_alpha_m''', '''K_B_alpha_n''', '''K_e''', '''comp19_V_t''', '''K_g''', '''K_A_alpha_n''', '''comp20_C''', '''Na_C_beta_h''', '''K_C_beta_n''', '''Na_C_beta_m''', '''Na_A_beta_m''', '''comp19_Vrest''', '''K_B_beta_n''', '''Na_B_alpha_m''', '''Na_A_beta_h''', '''Na_e''', '''Na_B_alpha_h''', '''Na_g''', '''Na_B_beta_m''', '''K_C_alpha_n''', '''Leak_g''', '''K_A_beta_n''', '''Leak_e''', '''Na_B_beta_h'''],
                                'parameterDefs' : ['''K_erev  =  params->K_erev;''', '''Na_C_alpha_h  =  params->Na_C_alpha_h;''', '''Na_C_alpha_m  =  params->Na_C_alpha_m;''', '''Na_A_alpha_h  =  params->Na_A_alpha_h;''', '''Na_gbar  =  params->Na_gbar;''', '''Na_A_alpha_m  =  params->Na_A_alpha_m;''', '''K_gbar  =  params->K_gbar;''', '''K_B_alpha_n  =  params->K_B_alpha_n;''', '''K_e  =  params->K_e;''', '''Leak_erev  =  params->Leak_erev;''', '''comp19_V_t  =  params->comp19_V_t;''', '''K_g  =  params->K_g;''', '''K_A_alpha_n  =  params->K_A_alpha_n;''', '''Na_erev  =  params->Na_erev;''', '''comp20_C  =  params->comp20_C;''', '''Na_C_beta_h  =  params->Na_C_beta_h;''', '''K_C_beta_n  =  params->K_C_beta_n;''', '''Na_C_beta_m  =  params->Na_C_beta_m;''', '''Na_A_beta_m  =  params->Na_A_beta_m;''', '''comp19_Vrest  =  params->comp19_Vrest;''', '''K_B_beta_n  =  params->K_B_beta_n;''', '''Leak_gbar  =  params->Leak_gbar;''', '''Na_B_alpha_m  =  params->Na_B_alpha_m;''', '''Na_A_beta_h  =  params->Na_A_beta_h;''', '''Na_e  =  params->Na_e;''', '''Na_B_alpha_h  =  params->Na_B_alpha_h;''', '''Na_g  =  params->Na_g;''', '''Na_B_beta_m  =  params->Na_B_beta_m;''', '''K_C_alpha_n  =  params->K_C_alpha_n;''', '''Leak_g  =  params->Leak_g;''', '''K_A_beta_n  =  params->K_A_beta_n;''', '''Leak_e  =  params->Leak_e;''', '''Na_B_beta_h  =  params->Na_B_beta_h;'''],
                                'ratePrevEqDefs' : ['''v  =  Ith(y,0);''', '''Na_h61O  =  Ith(y,1);''', '''K_m66O  =  Ith(y,2);''', '''Na_m60O  =  Ith(y,3);'''],
                                'eqOrderDefs' : ['''Na_m60  =  Na_m60O;''', '''K_m66  =  K_m66O;''', '''Na_h61  =  Na_h61O;''', '''i_K  =  (K_gbar * pow(K_m66, 4.0)) * (v - K_erev);''', '''ik  =  i_K;''', '''i_Na  =  (Na_gbar * pow(Na_m60, 3.0) * Na_h61) * (v - Na_erev);''', '''ina  =  i_Na;''', '''i_Leak  =  Leak_gbar * (v - Leak_erev);''', '''i  =  i_Leak;'''],
                                'rateEqDefs' : ['''Ith(f,0)  =  ((node.B_.I_stim_) + -0.001 * (ina + ik + i)) / comp20_C;''', '''v68  =  Na_h61O;; 
                                                   Ith(f,1)  =  -(Na_h61O * Na_bhf(v, params)) + (1.0 - v68) * (Na_ahf(v, params));''', '''v70  =  K_m66O;; 
                                                   Ith(f,2)  =  -(K_m66O * K_bnf(v, params)) + (1.0 - v70) * (K_anf(v, params));''', '''v72  =  Na_m60O;; 
                                                   Ith(f,3)  =  -(Na_m60O * Na_bmf(v, params)) + (1.0 - v72) * (Na_amf(v, params));''']}
        args['synapticEventDefs'] = []
        args['constraintEqDefs'] = [{'op' : '''>''', 'left' : '''Na_gbar''', 'right' : '''0.0''', 'str' : '''(> Na:gbar 0.0)'''},
                                        {'op' : '''>''', 'left' : '''K_gbar''', 'right' : '''0.0''', 'str' : '''(> K:gbar 0.0)'''},
                                        {'op' : '''>''', 'left' : '''Leak_gbar''', 'right' : '''0.0''', 'str' : '''(> Leak:gbar 0.0)'''}]
        args['defaultEqDefs'] = ['''Vrest  =  comp19_Vrest;''', '''V_t  =  comp19_V_t;''']
        args['residualRateEqDefs'] = ['''Ith(f,0)  =  Ith(y1,0) - Ith(yp,0);''', '''Ith(f,1)  =  Ith(y1,1) - Ith(yp,1);''', '''Ith(f,2)  =  Ith(y1,2) - Ith(yp,2);''', '''Ith(f,3)  =  Ith(y1,3) - Ith(yp,3);''']
        args['currentEqDefs'] = ['''i_K  =  (K_gbar * pow(K_m66, 4.0)) * (v - K_erev);''', '''ik  =  i_K;''', '''i_Na  =  (Na_gbar * pow(Na_m60, 3.0) * Na_h61) * (v - Na_erev);''', '''ina  =  i_Na;''', '''i_Leak  =  Leak_gbar * (v - Leak_erev);''', '''i  =  i_Leak;''']
        args['functionDefs'] = [{
                                     'consts' : ['''K_C_beta_n''', '''K_B_beta_n''', '''K_A_beta_n'''],
                                     'returnVar' : '''rv74''',
                                     'returnType' : '''double''',
                                     'exprString' : '''rv74  =  K_A_beta_n * exp(-(v + -(K_B_beta_n)) / K_C_beta_n);''',
                                     'localVars' : [],
                                     'vars' : ['''double v''', '''const void* params'''],
                                     'name' : '''K_bnf'''},
                                    {
                                     'consts' : ['''Na_C_alpha_m''', '''Na_B_alpha_m''', '''Na_A_alpha_m'''],
                                     'returnVar' : '''rv75''',
                                     'returnType' : '''double''',
                                     'exprString' : '''rv75  =  Na_A_alpha_m * (v + -(Na_B_alpha_m)) / (1.0 + -(exp(-(v + -(Na_B_alpha_m)) / Na_C_alpha_m)));''',
                                     'localVars' : [],
                                     'vars' : ['''double v''', '''const void* params'''],
                                     'name' : '''Na_amf'''}]
        args['exports'] = ['''comp19_Vrest''', '''comp19_V_t''', '''comp20_C''', '''Na_erev''', '''Na_gbar''', '''K_gbar''', '''K_erev''', '''Leak_gbar''', '''Leak_erev''', '''Na_m60''', '''Na_h61''', '''K_m66''']
        args['hasEvents'] = False
        args['defaultDefs'] = ['''Vrest''', '''V_t''']
        args['stateDefs'] = [{'name' : '''Na_m60O''', 'scale' : False},
                             {'name' : '''K_m66O''', 'scale' : False},
                             {'name' : '''Na_h61O''', 'scale' : False},
                             {'name' : '''v''', 'scale' : False}]
        args['steadyStateIndexMap'] = {}
        args['stateIndexMap'] = {'Na_m60O' : 3, 'K_m66O' : 2, 'Na_h61O' : 1, 'v' : 0}
        args['steadyStateSize'] = 0
        args['stateSize'] = 4
        args['SSvector'] = '''ssvect73'''
        args['SSmethod'] = False
        args['reltol'] = False
        args['abstol'] = False
        args['nemoVersionString'] = '''NEMO (http://wiki.call-cc.org/nemo) version 9.0'''
        args['currentTimestamp'] = '''Thu Oct 23 23:30:27 2014'''
        return args

    def _render_source_files(self, template_args, src_dir, install_dir):
        model_name = template_args['ModelName']
        # Render C++ header file
        self._render_to_file('NEST-header.tmpl', template_args,
                             model_name + '.h', src_dir)
        # Render C++ class file
        self._render_to_file('NEST.tmpl', template_args, model_name + '.cpp',
                             src_dir)
        build_args = {'celltype_name': model_name, 'src_dir': src_dir}
        # Render Loader header file
        self._render_to_file('loader-header.tmpl', build_args,
                             model_name + 'Loader.h', src_dir)
        # Render Loader C++ class
        self._render_to_file('loader-cpp.tmpl', build_args,
                             model_name + 'Loader.cpp', src_dir)
        # Render SLI initialiser
        self._render_to_file('sli_initialiser.tmpl', build_args,
                             model_name + 'Loader.sli', src_dir)
        # Generate Makefile if it is not present
        if not os.path.exists(os.path.join(src_dir, 'Makefile')):
            self._render_to_file('configure-ac.tmpl', build_args,
                                 'configure.ac', src_dir)
            self._render_to_file('Makefile-am.tmpl', build_args,
                                 'Makefile.am', src_dir)
            self._render_to_file('bootstrap-sh.tmpl', build_args,
                                 'bootstrap.sh', src_dir)
            os.chdir(src_dir)
            try:
                sp.check_call('./bootstrap.sh', shell=True)
            except sp.CalledProcessError:
                raise Exception("Bootstrapping of '{}' NEST module failed."
                                .format(model_name or src_dir))
            try:
                sp.check_call('{src_dir}/configure --prefix={install_dir}'
                              .format(src_dir=src_dir,
                                      install_dir=install_dir), shell=True)
            except sp.CalledProcessError:
                raise Exception("Configuration of '{}' NEST module failed. "
                                "See src directory '{}':\n "
                                .format(model_name, src_dir))

    def compile_source_files(self, compile_dir, component_name, verbose):
        # Run configure script, make and make install
        os.chdir(compile_dir)
        if verbose:
            print ("Compiling NEST model class in '{}' directory."
                  .format(compile_dir))
        try:
            sp.check_call('make', shell=True)
        except sp.CalledProcessError:
            raise Exception("Compilation of '{}' NEST module failed. "
                            .format(component_name))
        try:
            sp.check_call('make install', shell=True)
        except sp.CalledProcessError:
            raise Exception("Installation of '{}' NEST module failed. "
                            .format(component_name))

    def _clean_src_dir(self, src_dir, component_name):
        # Clean existing src directories from previous builds.
        prefix = os.path.join(src_dir, component_name)
        remove_ignore_missing(prefix + '.h')
        remove_ignore_missing(prefix + '.cpp')
        remove_ignore_missing(prefix + 'Loader.h')
        remove_ignore_missing(prefix + 'Loader.cpp')
        remove_ignore_missing(prefix + 'Loader.sli')
