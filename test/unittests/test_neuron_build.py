from nineline.cells.code_gen.neuron import CodeGenerator
import nineml
from os.path import dirname, join, abspath
build_dir = join(dirname(__file__), 'build')
test_dir = abspath(join(dirname(__file__), '..', 'data',
                        'xml'))
component_file = join(test_dir, 'Golgi_hcn2.xml')
comp = nineml.read(component_file)['Golgi_hcn2']
# initial_state_file = join(
#     dirname(__file__), '..', '..', 'examples',
#     'HodgkinHuxleyInitialState.xml')
code_generator = CodeGenerator()
code_generator.generate(component_file, 0.0,  # initial_state_file,
                        build_mode='generate_only',
                        ode_solver='derivimplicit', v_threshold=None)

# env = Environment(loader=FileSystemLoader(os.getenv("HOME") + "/git/nineline/nineline/cells/build/neuron/templates/"),
#                   trim_blocks=True)
# 
# template = env.get_template('NMODL.tmpl')
# 
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
# 
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
# 
# 
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
# 
# with open('hodgkin_huxley_Na.mod', 'w') as f:
#     f.write(output_Na)
# with open('hodgkin_huxley_K.mod', 'w') as f:
#     f.write(output_K)
# with open('hodgkin_huxley_Leak.mod', 'w') as f:
#     f.write(output_Leak)
