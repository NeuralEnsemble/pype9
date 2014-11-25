import os
from nineline.cells.code_gen.nest import CodeGenerator

# 
# env = Environment(loader=FileSystemLoader(
#                          os.getenv("HOME") +
#                          "/git/nineline/nineline/cells/build/nest/templates/"),
#                   trim_blocks=True)

# components = NineMLReader.read_components(os.getenv("HOME") +
#                                "/git/nineline/examples/HodgkinHuxleyClass.xml")
# 
# cpp_template = env.get_template('NEST.tmpl')
# header_template = env.get_template('NEST-header.tmpl')
# 
# template_args = { 'parameters': {'localVars' : [],
#                                  'parameterEqDefs' : ['''K_erev  (-77.0)''', '''Na_C_alpha_h  (20.0)''', '''Na_C_alpha_m  (10.0)''', '''Na_A_alpha_h  (0.07)''', '''Na_gbar  (0.12)''', '''Na_A_alpha_m  (0.1)''', '''K_gbar  (0.036)''', '''K_B_alpha_n  (-55.0)''', '''K_e  (-77.0)''', '''Leak_erev  (-54.4)''', '''comp19_V_t  (-35.0)''', '''K_g  (0.036)''', '''K_A_alpha_n  (0.01)''', '''Na_erev  (50.0)''', '''comp20_C  (1.0)''', '''Na_C_beta_h  (10.0)''', '''K_C_beta_n  (80.0)''', '''Na_C_beta_m  (18.0)''', '''Na_A_beta_m  (4.0)''', '''comp19_Vrest  (-65.0)''', '''K_B_beta_n  (-65.0)''', '''Leak_gbar  (0.0003)''', '''Na_B_alpha_m  (-40.0)''', '''Na_A_beta_h  (1.0)''', '''Na_e  (50.0)''', '''Na_B_alpha_h  (-65.0)''', '''Na_g  (0.12)''', '''Na_B_beta_m  (-65.0)''', '''K_C_alpha_n  (10.0)''', '''Leak_g  (0.0003)''', '''K_A_beta_n  (0.125)''', '''Leak_e  (-54.4)''', '''Na_B_beta_h  (-35.0)'''],
#                                  'parameterDefs' : [{'name' : '''K_erev''', 'scale' : False},
#                                                     {'name' : '''Na_C_alpha_h''', 'scale' : False},
#                                                     {'name' : '''Na_C_alpha_m''', 'scale' : False},
#                                                     {'name' : '''Na_A_alpha_h''', 'scale' : False},
#                                                     {'name' : '''Na_gbar''', 'scale' : False},
#                                                     {'name' : '''Na_A_alpha_m''', 'scale' : False},
#                                                     {'name' : '''K_gbar''', 'scale' : False},
#                                                     {'name' : '''K_B_alpha_n''', 'scale' : False},
#                                                     {'name' : '''K_e''', 'scale' : False},
#                                                     {'name' : '''Leak_erev''', 'scale' : False},
#                                                     {'name' : '''comp19_V_t''', 'scale' : False},
#                                                     {'name' : '''K_g''', 'scale' : False},
#                                                     {'name' : '''K_A_alpha_n''', 'scale' : False},
#                                                     {'name' : '''Na_erev''', 'scale' : False},
#                                                     {'name' : '''comp20_C''', 'scale' : False},
#                                                     {'name' : '''Na_C_beta_h''', 'scale' : False},
#                                                     {'name' : '''K_C_beta_n''', 'scale' : False},
#                                                     {'name' : '''Na_C_beta_m''', 'scale' : False},
#                                                     {'name' : '''Na_A_beta_m''', 'scale' : False},
#                                                     {'name' : '''comp19_Vrest''', 'scale' : False},
#                                                     {'name' : '''K_B_beta_n''', 'scale' : False},
#                                                     {'name' : '''Leak_gbar''', 'scale' : False},
#                                                     {'name' : '''Na_B_alpha_m''', 'scale' : False},
#                                                     {'name' : '''Na_A_beta_h''', 'scale' : False},
#                                                     {'name' : '''Na_e''', 'scale' : False},
#                                                     {'name' : '''Na_B_alpha_h''', 'scale' : False},
#                                                     {'name' : '''Na_g''', 'scale' : False},
#                                                     {'name' : '''Na_B_beta_m''', 'scale' : False},
#                                                     {'name' : '''K_C_alpha_n''', 'scale' : False},
#                                                     {'name' : '''Leak_g''', 'scale' : False},
#                                                     {'name' : '''K_A_beta_n''', 'scale' : False},
#                                                     {'name' : '''Leak_e''', 'scale' : False},
#                                                     {'name' : '''Na_B_beta_h''', 'scale' : False}],
#                                  'defaultDefs': [{'name' : '''Vrest''', 'scale' : False},
#                                                  {'name' : '''V_t''', 'scale' : False}]},
#                   'steadystate' : {
#                                    'localVars' : [
#                                                   '''v''',
#                                                   '''comp19_Vrest''', '''Na_h61''', '''Na_h61O''', '''K_m66''', '''K_m66O''', '''Na_m60''', '''Na_m60O''', '''i_K''', '''ik''', '''i_Na''', '''ina''', '''i_Leak''', '''i''', '''K_erev''', '''Na_C_alpha_h''', '''Na_C_alpha_m''', '''Na_A_alpha_h''', '''Na_gbar''', '''Na_A_alpha_m''', '''K_gbar''', '''K_B_alpha_n''', '''K_e''', '''Leak_erev''', '''comp19_V_t''', '''K_g''', '''K_A_alpha_n''', '''Na_erev''', '''comp20_C''', '''Na_C_beta_h''', '''K_C_beta_n''', '''Na_C_beta_m''', '''Na_A_beta_m''', '''K_B_beta_n''', '''Leak_gbar''', '''Na_B_alpha_m''', '''Na_A_beta_h''', '''Na_e''', '''Na_B_alpha_h''', '''Na_g''', '''Na_B_beta_m''', '''K_C_alpha_n''', '''Leak_g''', '''K_A_beta_n''', '''Leak_e''', '''Na_B_beta_h'''],
#                                    'parameterDefs' : ['''K_erev  =  params->K_erev;''', '''Na_C_alpha_h  =  params->Na_C_alpha_h;''', '''Na_C_alpha_m  =  params->Na_C_alpha_m;''', '''Na_A_alpha_h  =  params->Na_A_alpha_h;''', '''Na_gbar  =  params->Na_gbar;''', '''Na_A_alpha_m  =  params->Na_A_alpha_m;''', '''K_gbar  =  params->K_gbar;''', '''K_B_alpha_n  =  params->K_B_alpha_n;''', '''K_e  =  params->K_e;''', '''Leak_erev  =  params->Leak_erev;''', '''comp19_V_t  =  params->comp19_V_t;''', '''K_g  =  params->K_g;''', '''K_A_alpha_n  =  params->K_A_alpha_n;''', '''Na_erev  =  params->Na_erev;''', '''comp20_C  =  params->comp20_C;''', '''Na_C_beta_h  =  params->Na_C_beta_h;''', '''K_C_beta_n  =  params->K_C_beta_n;''', '''Na_C_beta_m  =  params->Na_C_beta_m;''', '''Na_A_beta_m  =  params->Na_A_beta_m;''', '''comp19_Vrest  =  params->comp19_Vrest;''', '''K_B_beta_n  =  params->K_B_beta_n;''', '''Leak_gbar  =  params->Leak_gbar;''', '''Na_B_alpha_m  =  params->Na_B_alpha_m;''', '''Na_A_beta_h  =  params->Na_A_beta_h;''', '''Na_e  =  params->Na_e;''', '''Na_B_alpha_h  =  params->Na_B_alpha_h;''', '''Na_g  =  params->Na_g;''', '''Na_B_beta_m  =  params->Na_B_beta_m;''', '''K_C_alpha_n  =  params->K_C_alpha_n;''', '''Leak_g  =  params->Leak_g;''', '''K_A_beta_n  =  params->K_A_beta_n;''', '''Leak_e  =  params->Leak_e;''', '''Na_B_beta_h  =  params->Na_B_beta_h;'''],
#                                    'SScurrentEqDefs' : ['''i_K  =  0.0;''', '''ik  =  0.0;''', '''i_Na  =  0.0;''', '''ina  =  0.0;''', '''i_Leak  =  0.0;''', '''i  =  0.0;'''],
#                                    'SSgetStateDefs' : [],
#                                    'SSsetStateDefsLbs' : []},
#                   'init' : {
#                             'localVars' : [
#                                            '''v''', '''comp19_Vrest''', '''Na_h61''', '''Na_h61O''', '''K_m66''', '''K_m66O''', '''Na_m60''', '''Na_m60O''', '''i_K''', '''ik''', '''i_Na''', '''ina''', '''i_Leak''', '''i''', '''K_erev''', '''Na_C_alpha_h''', '''Na_C_alpha_m''', '''Na_A_alpha_h''', '''Na_gbar''', '''Na_A_alpha_m''', '''K_gbar''', '''K_B_alpha_n''', '''K_e''', '''Leak_erev''', '''comp19_V_t''', '''K_g''', '''K_A_alpha_n''', '''Na_erev''', '''comp20_C''', '''Na_C_beta_h''', '''K_C_beta_n''', '''Na_C_beta_m''', '''Na_A_beta_m''', '''K_B_beta_n''', '''Leak_gbar''', '''Na_B_alpha_m''', '''Na_A_beta_h''', '''Na_e''', '''Na_B_alpha_h''', '''Na_g''', '''Na_B_beta_m''', '''K_C_alpha_n''', '''Leak_g''', '''K_A_beta_n''', '''Leak_e''', '''Na_B_beta_h'''],
#                             'parameterDefs' : ['''K_erev  =  p.K_erev;''', '''Na_C_alpha_h  =  p.Na_C_alpha_h;''', '''Na_C_alpha_m  =  p.Na_C_alpha_m;''', '''Na_A_alpha_h  =  p.Na_A_alpha_h;''', '''Na_gbar  =  p.Na_gbar;''', '''Na_A_alpha_m  =  p.Na_A_alpha_m;''', '''K_gbar  =  p.K_gbar;''', '''K_B_alpha_n  =  p.K_B_alpha_n;''', '''K_e  =  p.K_e;''', '''Leak_erev  =  p.Leak_erev;''', '''comp19_V_t  =  p.comp19_V_t;''', '''K_g  =  p.K_g;''', '''K_A_alpha_n  =  p.K_A_alpha_n;''', '''Na_erev  =  p.Na_erev;''', '''comp20_C  =  p.comp20_C;''', '''Na_C_beta_h  =  p.Na_C_beta_h;''', '''K_C_beta_n  =  p.K_C_beta_n;''', '''Na_C_beta_m  =  p.Na_C_beta_m;''', '''Na_A_beta_m  =  p.Na_A_beta_m;''', '''comp19_Vrest  =  p.comp19_Vrest;''', '''K_B_beta_n  =  p.K_B_beta_n;''', '''Leak_gbar  =  p.Leak_gbar;''', '''Na_B_alpha_m  =  p.Na_B_alpha_m;''', '''Na_A_beta_h  =  p.Na_A_beta_h;''', '''Na_e  =  p.Na_e;''', '''Na_B_alpha_h  =  p.Na_B_alpha_h;''', '''Na_g  =  p.Na_g;''', '''Na_B_beta_m  =  p.Na_B_beta_m;''', '''K_C_alpha_n  =  p.K_C_alpha_n;''', '''Leak_g  =  p.Leak_g;''', '''K_A_beta_n  =  p.K_A_beta_n;''', '''Leak_e  =  p.Leak_e;''', '''Na_B_beta_h  =  p.Na_B_beta_h;'''],
#                             'initOrder' : ['''v  =  -65.0;''', '''Na_h61  =  (Na_ahf(comp19_Vrest, params)) / (Na_ahf(comp19_Vrest, params) + Na_bhf(comp19_Vrest, params));''', '''Na_h61O  =  Na_h61;''', '''K_m66  =  (K_anf(comp19_Vrest, params)) / (K_anf(comp19_Vrest, params) + K_bnf(comp19_Vrest, params));''', '''K_m66O  =  K_m66;''', '''Na_m60  =  (Na_amf(comp19_Vrest, params)) / (Na_amf(comp19_Vrest, params) + Na_bmf(comp19_Vrest, params));''', '''Na_m60O  =  Na_m60;'''],
#                             'initEqDefs' : ['''y_[0]  =  v;''', '''y_[1]  =  Na_h61O;''', '''y_[2]  =  K_m66O;''', '''y_[3]  =  Na_m60O;'''],
#                             'rateEqStates' : ['''v''', '''Na_h61O''', '''K_m66O''', '''Na_m60O'''],
#                             'reactionEqDefs' : []},
#                   'dynamics' : {'localVars' : ['''v68''', '''v70''', '''v72''', '''Na_m60O''', '''Na_m60''', '''K_m66O''', '''K_m66''', '''Na_h61O''', '''Na_h61''', '''K_erev''', '''v''', '''K_gbar''', '''i_K''', '''ik''', '''Na_erev''', '''Na_gbar''', '''i_Na''', '''ina''', '''Leak_erev''', '''Leak_gbar''', '''i_Leak''', '''i''', '''Na_C_alpha_h''', '''Na_C_alpha_m''', '''Na_A_alpha_h''', '''Na_A_alpha_m''', '''K_B_alpha_n''', '''K_e''', '''comp19_V_t''', '''K_g''', '''K_A_alpha_n''', '''comp20_C''', '''Na_C_beta_h''', '''K_C_beta_n''', '''Na_C_beta_m''', '''Na_A_beta_m''', '''comp19_Vrest''', '''K_B_beta_n''', '''Na_B_alpha_m''', '''Na_A_beta_h''', '''Na_e''', '''Na_B_alpha_h''', '''Na_g''', '''Na_B_beta_m''', '''K_C_alpha_n''', '''Leak_g''', '''K_A_beta_n''', '''Leak_e''', '''Na_B_beta_h'''],
#                                 'parameterDefs' : ['''K_erev  =  params->K_erev;''', '''Na_C_alpha_h  =  params->Na_C_alpha_h;''', '''Na_C_alpha_m  =  params->Na_C_alpha_m;''', '''Na_A_alpha_h  =  params->Na_A_alpha_h;''', '''Na_gbar  =  params->Na_gbar;''', '''Na_A_alpha_m  =  params->Na_A_alpha_m;''', '''K_gbar  =  params->K_gbar;''', '''K_B_alpha_n  =  params->K_B_alpha_n;''', '''K_e  =  params->K_e;''', '''Leak_erev  =  params->Leak_erev;''', '''comp19_V_t  =  params->comp19_V_t;''', '''K_g  =  params->K_g;''', '''K_A_alpha_n  =  params->K_A_alpha_n;''', '''Na_erev  =  params->Na_erev;''', '''comp20_C  =  params->comp20_C;''', '''Na_C_beta_h  =  params->Na_C_beta_h;''', '''K_C_beta_n  =  params->K_C_beta_n;''', '''Na_C_beta_m  =  params->Na_C_beta_m;''', '''Na_A_beta_m  =  params->Na_A_beta_m;''', '''comp19_Vrest  =  params->comp19_Vrest;''', '''K_B_beta_n  =  params->K_B_beta_n;''', '''Leak_gbar  =  params->Leak_gbar;''', '''Na_B_alpha_m  =  params->Na_B_alpha_m;''', '''Na_A_beta_h  =  params->Na_A_beta_h;''', '''Na_e  =  params->Na_e;''', '''Na_B_alpha_h  =  params->Na_B_alpha_h;''', '''Na_g  =  params->Na_g;''', '''Na_B_beta_m  =  params->Na_B_beta_m;''', '''K_C_alpha_n  =  params->K_C_alpha_n;''', '''Leak_g  =  params->Leak_g;''', '''K_A_beta_n  =  params->K_A_beta_n;''', '''Leak_e  =  params->Leak_e;''', '''Na_B_beta_h  =  params->Na_B_beta_h;'''],
#                                 'ratePrevEqDefs' : ['''v  =  Ith(y,0);''', '''Na_h61O  =  Ith(y,1);''', '''K_m66O  =  Ith(y,2);''', '''Na_m60O  =  Ith(y,3);'''],
#                                 'eqOrderDefs' : ['''Na_m60  =  Na_m60O;''', '''K_m66  =  K_m66O;''', '''Na_h61  =  Na_h61O;''', '''i_K  =  (K_gbar * pow(K_m66, 4.0)) * (v - K_erev);''', '''ik  =  i_K;''', '''i_Na  =  (Na_gbar * pow(Na_m60, 3.0) * Na_h61) * (v - Na_erev);''', '''ina  =  i_Na;''', '''i_Leak  =  Leak_gbar * (v - Leak_erev);''', '''i  =  i_Leak;'''],
#                                 'rateEqDefs' : ['''Ith(f,0)  =  ((node.B_.I_stim_) + -0.001 * (ina + ik + i)) / comp20_C;''', '''v68  =  Na_h61O;; 
#                                                    Ith(f,1)  =  -(Na_h61O * Na_bhf(v, params)) + (1.0 - v68) * (Na_ahf(v, params));''', '''v70  =  K_m66O;; 
#                                                    Ith(f,2)  =  -(K_m66O * K_bnf(v, params)) + (1.0 - v70) * (K_anf(v, params));''', '''v72  =  Na_m60O;; 
#                                                    Ith(f,3)  =  -(Na_m60O * Na_bmf(v, params)) + (1.0 - v72) * (Na_amf(v, params));''']},
#                   'synapticEventDefs' : [],
#                   'constraintEqDefs' : [{'op' : '''>''', 'left' : '''Na_gbar''', 'right' : '''0.0''', 'str' : '''(> Na:gbar 0.0)'''},
#                                         {'op' : '''>''', 'left' : '''K_gbar''', 'right' : '''0.0''', 'str' : '''(> K:gbar 0.0)'''},
#                                         {'op' : '''>''', 'left' : '''Leak_gbar''', 'right' : '''0.0''', 'str' : '''(> Leak:gbar 0.0)'''}],
#                   'defaultEqDefs' : ['''Vrest  =  comp19_Vrest;''', '''V_t  =  comp19_V_t;'''],
#                   'residualRateEqDefs' : ['''Ith(f,0)  =  Ith(y1,0) - Ith(yp,0);''', '''Ith(f,1)  =  Ith(y1,1) - Ith(yp,1);''', '''Ith(f,2)  =  Ith(y1,2) - Ith(yp,2);''', '''Ith(f,3)  =  Ith(y1,3) - Ith(yp,3);'''],
#                   'currentEqDefs' : ['''i_K  =  (K_gbar * pow(K_m66, 4.0)) * (v - K_erev);''', '''ik  =  i_K;''', '''i_Na  =  (Na_gbar * pow(Na_m60, 3.0) * Na_h61) * (v - Na_erev);''', '''ina  =  i_Na;''', '''i_Leak  =  Leak_gbar * (v - Leak_erev);''', '''i  =  i_Leak;'''],
#                   'functionDefs' : [
#                                     {
#                                      'consts' : ['''K_C_beta_n''', '''K_B_beta_n''', '''K_A_beta_n'''],
#                                      'returnVar' : '''rv74''',
#                                      'returnType' : '''double''',
#                                      'exprString' : '''rv74  =  K_A_beta_n * exp(-(v + -(K_B_beta_n)) / K_C_beta_n);''',
#                                      'localVars' : [],
#                                      'vars' : ['''double v''', '''const void* params'''],
#                                      'name' : '''K_bnf'''},
#                                     {
#                                      'consts' : ['''Na_C_alpha_m''', '''Na_B_alpha_m''', '''Na_A_alpha_m'''],
#                                      'returnVar' : '''rv75''',
#                                      'returnType' : '''double''',
#                                      'exprString' : '''rv75  =  Na_A_alpha_m * (v + -(Na_B_alpha_m)) / (1.0 + -(exp(-(v + -(Na_B_alpha_m)) / Na_C_alpha_m)));''',
#                                      'localVars' : [],
#                                      'vars' : ['''double v''', '''const void* params'''],
#                                      'name' : '''Na_amf'''},
#                                     {
#                                      'consts' : ['''K_C_alpha_n''', '''K_B_alpha_n''', '''K_A_alpha_n'''],
#                                      'returnVar' : '''rv76''',
#                                      'returnType' : '''double''',
#                                      'exprString' : '''rv76  =  K_A_alpha_n * (v + -(K_B_alpha_n)) / (1.0 + -(exp(-(v + -(K_B_alpha_n)) / K_C_alpha_n)));''',
#                                      'localVars' : [],
#                                      'vars' : ['''double v''', '''const void* params'''],
#                                      'name' : '''K_anf'''},
#                                     {
#                                      'consts' : ['''Na_C_beta_h''', '''Na_B_beta_h''', '''Na_A_beta_h'''], 
#                                      'returnVar' : '''rv77''', 
#                                      'returnType' : '''double''', 
#                                      'exprString' : '''rv77  =  Na_A_beta_h / (1.0 + exp(-(v + -(Na_B_beta_h)) / Na_C_beta_h));''', 
#                                      'localVars' : [], 
#                                      'vars' : ['''double v''', '''const void* params'''], 
#                                      'name' : '''Na_bhf'''},
#                                     {
#                                      'consts' : ['''Na_C_alpha_h''', '''Na_B_alpha_h''', '''Na_A_alpha_h'''], 
#                                      'returnVar' : '''rv78''', 
#                                      'returnType' : '''double''', 
#                                      'exprString' : '''rv78  =  Na_A_alpha_h * exp(-(v + -(Na_B_alpha_h)) / Na_C_alpha_h);''', 
#                                      'localVars' : [], 
#                                      'vars' : ['''double v''', '''const void* params'''], 
#                                      'name' : '''Na_ahf'''},
#                                     {
#                                      'consts' : ['''Na_C_beta_m''', '''Na_B_beta_m''', '''Na_A_beta_m'''], 
#                                      'returnVar' : '''rv79''', 
#                                      'returnType' : '''double''', 
#                                      'exprString' : '''rv79  =  Na_A_beta_m * exp(-(v + -(Na_B_beta_m)) / Na_C_beta_m);''', 
#                                      'localVars' : [], 
#                                      'vars' : ['''double v''', '''const void* params'''], 
#                                      'name' : '''Na_bmf'''}],
#                   'exports' : ['''comp19_Vrest''', '''comp19_V_t''', '''comp20_C''', '''Na_erev''', '''Na_gbar''', '''K_gbar''', '''K_erev''', '''Leak_gbar''', '''Leak_erev''', '''Na_m60''', '''Na_h61''', '''K_m66'''],
#                   'hasEvents' : False,
#                   'defaultDefs' : ['''Vrest''', '''V_t'''],
#                   'stateDefs' : [{'name' : '''Na_m60O''', 'scale' : False},
#                                  {'name' : '''K_m66O''', 'scale' : False},
#                                  {'name' : '''Na_h61O''', 'scale' : False},
#                                  {'name' : '''v''', 'scale' : False}],
#                   'steadyStateIndexMap' : {},
#                   'stateIndexMap' : {'Na_m60O' : 3, 'K_m66O' : 2, 'Na_h61O' : 1, 'v' : 0},
#                   'steadyStateSize' : 0,
#                   'stateSize' : 4,
#                   'SSvector' : '''ssvect73''',
#                   'SSmethod' : False,
#                   'ODEmethod' : '''gsl''',
#                   'reltol' : False,
#                   'abstol' : False,
#                   'modelName' : '''hodgkin_huxley''',
#                   'nemoVersionString' : '''NEMO (http://wiki.call-cc.org/nemo) version 9.0''',
#                   'currentTimestamp' : '''Thu Oct 23 23:30:27 2014'''}
# 
# # Generate and write header to file
# output_header = header_template.render(**template_args)
# with open(join(build_dir, biophysics_name + '.h'), 'w') as f:
#     f.write(output_header)
# # Generate and write C++ to file
# output_cpp = cpp_template.render(**template_args)
# with open(join(build_dir, 'hodgkin_huxley.cpp'), 'w') as f:
#     f.write(output_cpp)
import nineml
from os.path import dirname, join, abspath, realpath
build_dir = join(dirname(__file__), 'build')
test_dir = abspath(join(dirname(realpath(nineml.__file__)), '..', 'test',
                        'xml'))
component_file = join(test_dir, 'neurons', 'HodgkinHuxleyModified.xml')
comp = nineml.read(component_file)['HodgkinHuxleyModified']
initial_state_file = join(dirname(__file__), '..', '..',
                                  'examples', 'HodgkinHuxleyInitialState.xml')
code_generator = CodeGenerator()
code_generator.generate(component_file, 0.0,  # initial_state_file,
                        build_mode='generate_only')

# biophysics_name = 'HodgkinHuxleyClass'
# builder.create_model_files(biophysics_name, test_file, build_dir)
# os.chdir(build_dir)
# if not exists(join(build_dir, 'Makefile')):
# 
#     # Generate configure.ac and Makefile
#     builder.create_configure_ac(biophysics_name, build_dir)
#     builder.create_makefile(biophysics_name, biophysics_name, build_dir)
#     builder.create_boilerplate_cpp(biophysics_name, build_dir)
#     builder.create_sli_initialiser(biophysics_name, build_dir)
#     # Run bootstrapping
#     builder.run_bootstrap(build_dir)
#     # Run configure script
#     sp.check_call('{src_dir}/configure --prefix={install_dir}'
#                   .format(src_dir=build_dir,
#                           install_dir=join(build_dir, 'bin')),
#                   shell=True)
# if False:
#     # Run make
#     sp.check_call('make', shell=True)
#     # Run install
#     sp.check_call('make install', shell=True)
