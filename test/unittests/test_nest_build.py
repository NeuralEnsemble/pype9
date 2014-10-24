import os
from jinja2 import Environment, FileSystemLoader
from nineline.cells.build.nest import (run_bootstrap, create_configure_ac,
                                       create_makefile,
                                       create_boilerplate_cpp,
                                       create_sli_initialiser)
import subprocess as sp

env = Environment(loader=FileSystemLoader(os.getenv("HOME") + "/git/nineline/nineline/cells/build/nest/templates/"),
                  trim_blocks=True)

build_dir = '/home/tclose/Desktop/hodgkin_huxley_test'
biophysics_name = 'hodgkin_huxley'

cpp_template = env.get_template('NEST.tmpl')
header_template = env.get_template('NEST-header.tmpl')

template_args = {'parameters' : {'localVars' : [], 'parameterEqDefs' : ['''comp29_e_K  (-77.0)''', '''comp21_gbar_Na  (0.12)''', '''comp21_e_Na  (50.0)''', '''comp19_Vrest  (-65.0)''', '''comp35_e_Leak  (-54.4)''', '''comp35_gbar_Leak  (0.0003)''', '''comp19_V_t  (-35.0)''', '''comp29_gbar_K  (0.036)''', '''comp20_C  (1.0)'''], 'parameterDefs' : [{'name' : '''comp29_e_K''', 'scale' : False}, {'name' : '''comp21_gbar_Na''', 'scale' : False}, {'name' : '''comp21_e_Na''', 'scale' : False}, {'name' : '''comp19_Vrest''', 'scale' : False}, {'name' : '''comp35_e_Leak''', 'scale' : False}, {'name' : '''comp35_gbar_Leak''', 'scale' : False}, {'name' : '''comp19_V_t''', 'scale' : False}, {'name' : '''comp29_gbar_K''', 'scale' : False}, {'name' : '''comp20_C''', 'scale' : False}], 'defaultDefs' : [{'name' : '''Vrest''', 'scale' : False}, {'name' : '''V_t''', 'scale' : False}]},
                 'steadystate' : {'localVars' : ['''v''', '''comp19_Vrest''', '''Na_m42''', '''Na_m42O''', '''Na_h43''', '''Na_h43O''', '''K_m48''', '''K_m48O''', '''i_K''', '''ik''', '''i_Na''', '''ina''', '''i_Leak''', '''i''', '''comp29_e_K''', '''comp21_gbar_Na''', '''comp21_e_Na''', '''comp35_e_Leak''', '''comp35_gbar_Leak''', '''comp19_V_t''', '''comp29_gbar_K''', '''comp20_C'''], 'parameterDefs' : ['''comp29_e_K  =  params->comp29_e_K;''', '''comp21_gbar_Na  =  params->comp21_gbar_Na;''', '''comp21_e_Na  =  params->comp21_e_Na;''', '''comp19_Vrest  =  params->comp19_Vrest;''', '''comp35_e_Leak  =  params->comp35_e_Leak;''', '''comp35_gbar_Leak  =  params->comp35_gbar_Leak;''', '''comp19_V_t  =  params->comp19_V_t;''', '''comp29_gbar_K  =  params->comp29_gbar_K;''', '''comp20_C  =  params->comp20_C;'''], 'SScurrentEqDefs' : ['''i_K  =  0.0;''', '''ik  =  0.0;''', '''i_Na  =  0.0;''', '''ina  =  0.0;''', '''i_Leak  =  0.0;''', '''i  =  0.0;'''], 'SSgetStateDefs' : [], 'SSsetStateDefsLbs' : []},
                 'init' : {'localVars' : ['''v''', '''comp19_Vrest''', '''Na_m42''', '''Na_m42O''', '''Na_h43''', '''Na_h43O''', '''K_m48''', '''K_m48O''', '''i_K''', '''ik''', '''i_Na''', '''ina''', '''i_Leak''', '''i''', '''comp29_e_K''', '''comp21_gbar_Na''', '''comp21_e_Na''', '''comp35_e_Leak''', '''comp35_gbar_Leak''', '''comp19_V_t''', '''comp29_gbar_K''', '''comp20_C'''], 'parameterDefs' : ['''comp29_e_K  =  p.comp29_e_K;''', '''comp21_gbar_Na  =  p.comp21_gbar_Na;''', '''comp21_e_Na  =  p.comp21_e_Na;''', '''comp19_Vrest  =  p.comp19_Vrest;''', '''comp35_e_Leak  =  p.comp35_e_Leak;''', '''comp35_gbar_Leak  =  p.comp35_gbar_Leak;''', '''comp19_V_t  =  p.comp19_V_t;''', '''comp29_gbar_K  =  p.comp29_gbar_K;''', '''comp20_C  =  p.comp20_C;'''], 'initOrder' : ['''v  =  -65.0;''', '''Na_m42  =  (comp21_amf(comp19_Vrest, params)) / (comp21_amf(comp19_Vrest, params) + comp21_bmf(comp19_Vrest, params));''', '''Na_m42O  =  Na_m42;''', '''Na_h43  =  (comp21_ahf(comp19_Vrest, params)) / (comp21_ahf(comp19_Vrest, params) + comp21_bhf(comp19_Vrest, params));''', '''Na_h43O  =  Na_h43;''', '''K_m48  =  (comp29_anf(comp19_Vrest, params)) / (comp29_anf(comp19_Vrest, params) + comp29_bnf(comp19_Vrest, params));''', '''K_m48O  =  K_m48;'''], 'initEqDefs' : ['''y_[0]  =  v;''', '''y_[1]  =  Na_m42O;''', '''y_[2]  =  Na_h43O;''', '''y_[3]  =  K_m48O;'''], 'rateEqStates' : ['''v''', '''Na_m42O''', '''Na_h43O''', '''K_m48O'''], 'reactionEqDefs' : []},
                 'dynamics' : {'localVars' : ['''v50''', '''v52''', '''v54''', '''K_m48O''', '''K_m48''', '''Na_h43O''', '''Na_h43''', '''Na_m42O''', '''Na_m42''', '''comp29_e_K''', '''v''', '''comp29_gbar_K''', '''i_K''', '''ik''', '''comp21_e_Na''', '''comp21_gbar_Na''', '''i_Na''', '''ina''', '''comp35_e_Leak''', '''comp35_gbar_Leak''', '''i_Leak''', '''i''', '''comp19_Vrest''', '''comp19_V_t''', '''comp20_C'''], 'parameterDefs' : ['''comp29_e_K  =  params->comp29_e_K;''', '''comp21_gbar_Na  =  params->comp21_gbar_Na;''', '''comp21_e_Na  =  params->comp21_e_Na;''', '''comp19_Vrest  =  params->comp19_Vrest;''', '''comp35_e_Leak  =  params->comp35_e_Leak;''', '''comp35_gbar_Leak  =  params->comp35_gbar_Leak;''', '''comp19_V_t  =  params->comp19_V_t;''', '''comp29_gbar_K  =  params->comp29_gbar_K;''', '''comp20_C  =  params->comp20_C;'''], 'ratePrevEqDefs' : ['''v  =  Ith(y,0);''', '''Na_m42O  =  Ith(y,1);''', '''Na_h43O  =  Ith(y,2);''', '''K_m48O  =  Ith(y,3);'''], 'eqOrderDefs' : ['''K_m48  =  K_m48O;''', '''Na_h43  =  Na_h43O;''', '''Na_m42  =  Na_m42O;''', '''i_K  =  (comp29_gbar_K * pow(K_m48, 4.0)) * (v - comp29_e_K);''', '''ik  =  i_K;''', '''i_Na  =  (comp21_gbar_Na * pow(Na_m42, 3.0) * Na_h43) * (v - comp21_e_Na);''', '''ina  =  i_Na;''', '''i_Leak  =  comp35_gbar_Leak * (v - comp35_e_Leak);''', '''i  =  i_Leak;'''], 'rateEqDefs' : ['''Ith(f,0)  =  ((node.B_.I_stim_) + -0.001 * (ina + ik + i)) / comp20_C;''', '''v50  =  Na_m42O;; 
Ith(f,1)  =  -(Na_m42O * comp21_bmf(v, params)) + (1.0 - v50) * (comp21_amf(v, params));''', '''v52  =  Na_h43O;; 
Ith(f,2)  =  -(Na_h43O * comp21_bhf(v, params)) + (1.0 - v52) * (comp21_ahf(v, params));''', '''v54  =  K_m48O;; 
Ith(f,3)  =  -(K_m48O * comp29_bnf(v, params)) + (1.0 - v54) * (comp29_anf(v, params));''']},
                 'synapticEventDefs' : [],
                 'constraintEqDefs' : [{'op' : '''>''', 'left' : '''comp21_gbar_Na''', 'right' : '''0.0''', 'str' : '''(> comp21:gbar_Na 0.0)'''}, {'op' : '''>''', 'left' : '''comp29_gbar_K''', 'right' : '''0.0''', 'str' : '''(> comp29:gbar_K 0.0)'''}, {'op' : '''>''', 'left' : '''comp35_gbar_Leak''', 'right' : '''0.0''', 'str' : '''(> comp35:gbar_Leak 0.0)'''}],
                 'defaultEqDefs' : ['''Vrest  =  comp19_Vrest;''', '''V_t  =  comp19_V_t;'''],
                 'residualRateEqDefs' : ['''Ith(f,0)  =  Ith(y1,0) - Ith(yp,0);''', '''Ith(f,1)  =  Ith(y1,1) - Ith(yp,1);''', '''Ith(f,2)  =  Ith(y1,2) - Ith(yp,2);''', '''Ith(f,3)  =  Ith(y1,3) - Ith(yp,3);'''],
                 'currentEqDefs' : ['''i_K  =  (comp29_gbar_K * pow(K_m48, 4.0)) * (v - comp29_e_K);''', '''ik  =  i_K;''', '''i_Na  =  (comp21_gbar_Na * pow(Na_m42, 3.0) * Na_h43) * (v - comp21_e_Na);''', '''ina  =  i_Na;''', '''i_Leak  =  comp35_gbar_Leak * (v - comp35_e_Leak);''', '''i  =  i_Leak;'''],
                 'functionDefs' : [{'consts' : [], 'returnVar' : '''rv56''', 'returnType' : '''double''', 'exprString' : '''rv56  =  0.1 * (v + 40.0) / (1.0 + -(exp(-(v + 40.0) / 10.0)));''', 'localVars' : [], 'vars' : ['''double v''', '''const void* params'''], 'name' : '''comp21_amf'''}, 
                                 {'consts' : [], 'returnVar' : '''rv57''', 'returnType' : '''double''', 'exprString' : '''rv57  =  0.125 * exp(-(v + 65.0) / 80.0);''', 'localVars' : [], 'vars' : ['''double v''', '''const void* params'''], 'name' : '''comp29_bnf'''}, 
                                 {'consts' : [], 'returnVar' : '''rv58''', 'returnType' : '''double''', 'exprString' : '''rv58  =  0.07 * exp(-(v + 65.0) / 20.0);''', 'localVars' : [], 'vars' : ['''double v''', '''const void* params'''], 'name' : '''comp21_ahf'''}, {'consts' : [], 'returnVar' : '''rv59''', 'returnType' : '''double''', 'exprString' : '''rv59  =  4.0 * exp(-(v + 65.0) / 18.0);''', 'localVars' : [], 'vars' : ['''double v''', '''const void* params'''], 'name' : '''comp21_bmf'''}, {'consts' : [], 'returnVar' : '''rv60''', 'returnType' : '''double''', 'exprString' : '''rv60  =  1.0 / (1.0 + exp(-(v + 35.0) / 10.0));''', 'localVars' : [], 'vars' : ['''double v''', '''const void* params'''], 'name' : '''comp21_bhf'''}, {'consts' : [], 'returnVar' : '''rv61''', 'returnType' : '''double''', 'exprString' : '''rv61  =  0.01 * (v + 55.0) / (1.0 + -(exp(-(v + 55.0) / 10.0)));''', 'localVars' : [], 'vars' : ['''double v''', '''const void* params'''], 'name' : '''comp29_anf'''}],

                 'exports' : ['''comp19_Vrest''', '''comp19_V_t''', '''comp20_C''', '''comp21_e_Na''', '''comp21_gbar_Na''', '''comp29_gbar_K''', '''comp29_e_K''', '''comp35_e_Leak''', '''comp35_gbar_Leak''', '''Na_m42''', '''Na_h43''', '''K_m48'''],

                 'hasEvents' : False,

                 'defaultDefs' : ['''Vrest''', '''V_t'''],

                 'stateDefs' : [{'name' : '''K_m48O''', 'scale' : False}, {'name' : '''Na_h43O''', 'scale' : False}, {'name' : '''Na_m42O''', 'scale' : False}, {'name' : '''v''', 'scale' : False}],

                 'steadyStateIndexMap' : {},

                 'stateIndexMap' : {'K_m48O' : 3, 'Na_h43O' : 2, 'Na_m42O' : 1, 'v' : 0},

                 'steadyStateSize' : 0,
                 'stateSize' : 4,

                 'SSvector' : '''ssvect55''',
                 'SSmethod' : False,
                 'ODEmethod' : '''gsl''',
                 'reltol' : False,
                 'abstol' : False,

                 'modelName' : '''hodgkin_huxley''',
                 'nemoVersionString' : '''NEMO (http://wiki.call-cc.org/nemo) version 9.0''',
                 'currentTimestamp' : '''Thu Oct  9 10:28:01 2014'''}

output_cpp = cpp_template.render(**template_args)
output_header = header_template.render(**template_args)


with open(os.path.join(build_dir, 'hodgkin_huxley.cpp'), 'w') as f:
    f.write(output_cpp)

with open(os.path.join(build_dir, biophysics_name + '.h'), 'w') as f:
    f.write(output_header)

os.chdir(build_dir)
if not os.path.exists(os.path.join(build_dir, 'Makefile')):
    # Generate configure.ac and Makefile
    create_configure_ac(biophysics_name, build_dir)
    create_makefile(biophysics_name, biophysics_name, build_dir)
    create_boilerplate_cpp(biophysics_name, build_dir)
    create_sli_initialiser(biophysics_name, build_dir)
    # Run bootstrapping
    run_bootstrap(build_dir)
    # Run configure script
    sp.check_call('{src_dir}/configure --prefix={install_dir}'
                  .format(src_dir=build_dir,
                          install_dir=os.path.join(build_dir, 'bin')),
                  shell=True)
# Run make
sp.check_call('make', shell=True)
# Run install
sp.check_call('make install', shell=True)
