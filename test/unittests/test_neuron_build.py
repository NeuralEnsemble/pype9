import os
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader(os.getenv("HOME") + "/git/nineline/nineline/cells/build/neuron/templates/"),
                  trim_blocks=True)

template = env.get_template('NMODL.tmpl')

output_Na = template.render (functionDefs = 
                          [{'indent' : 2, 'name' : '''comp21_bmf''', 'vars' : ['''v'''], 'localVars' : [], 'exprString' : '''comp21_bmf  =  4.0 * exp(-(v + 65.0) / 18.0)'''}, 
                           {'indent' : 2, 'name' : '''comp21_bhf''', 'vars' : ['''v'''], 'localVars' : [], 'exprString' : '''comp21_bhf  =  1.0 / (1.0 + exp(-(v + 35.0) / 10.0))'''}, 
                           {'indent' : 2, 'name' : '''comp21_amf''', 'vars' : ['''v'''], 'localVars' : [], 'exprString' : '''comp21_amf  =  0.1 * (v + 40.0) / (1.0 + -(exp(-(v + 40.0) / 10.0)))'''}, 
                           {'indent' : 2, 'name' : '''comp21_ahf''', 'vars' : ['''v'''], 'localVars' : [], 'exprString' : '''comp21_ahf  =  0.07 * exp(-(v + 65.0) / 20.0)'''}],
                          transientEventEqDefs = [],
                          externalEventEqDefs = [],
                          eventVars = [],
                          eventLocals = [],
                          initEqDefs = ['''Na_h34  = 
                          (comp21_ahf(comp19_Vrest)) /
                          (comp21_ahf(comp19_Vrest) + comp21_bhf(comp19_Vrest))''', '''Na_h34O  =  Na_h34''', 
                                        '''Na_m33  = 
                                        (comp21_amf(comp19_Vrest)) /
                                        (comp21_amf(comp19_Vrest) + comp21_bmf(comp19_Vrest))''', '''Na_m33O  =  Na_m33'''],
                          initEqLocals = [],
                          reversalPotentialEqDefs = [],
                          kineticEqDefs = [],
                          kineticEqLocals = [],
                          externalEqDefs = [],
                          rateEqDefs = ['''v82  =  Na_h34O
                          Na_h34O'  =  (1.0 - v82) * (comp21_ahf(v)) - Na_h34O * comp21_bhf(v)''', 
                                        '''v84  =  Na_m33O
                          Na_m33O'  =  (1.0 - v84) * (comp21_amf(v)) - Na_m33O * comp21_bmf(v)'''],
                          rateEqLocals = ['''v82''', '''v84'''],
                          reactionEqDefs = ['''Na_m33  =  Na_m33O''', '''Na_h34  =  Na_h34O'''],
                          reactionEqLocals = [],
                          assignedEqDefs = ['''ena  =  comp21_e_Na'''],
                          assignedEqLocals = [],
                          assignedDefs = ['''v''', '''ina''', '''ena''', '''i_Na'''],
                          stateDefs = ['''Na_m33C''', '''Na_m33O''', '''Na_h34C''', '''Na_h34O''', '''Na_m33''', '''Na_h34'''],
                          parameterDefs = ['''comp21_e_Na  =  50.0''', '''comp21_gbar_Na  =  0.12''', '''comp19_V_t  =  -35.0''', '''comp19_Vrest  =  -65.0''', '''comp20_C  =  1.0'''],
                          parameterLocals = [],
                          rangeParameters = ['''comp21_e_Na'''],
                          useIons = [{'nonSpecific' : False, 'name' : '''na''', 'read' : ['''ena'''], 'write' : ['''ina'''], 'valence' : False}],
                          poolIons = [],
                          accumulatingIons = [],
                          modulatingIons = [],
                          permeatingIons = [{'species' : '''na''', 'i' : '''ina''', 'e' : '''ena''', 'erev' : '''comp21:e_Na''', 'valence' : False}],
                          currentEqDefs = ['''i_Na  =  (comp21_gbar_Na * Na_m33 ^ 3.0 * Na_h34) * (v - comp21_e_Na)''', '''ina  =  i_Na'''],
                          currentEqLocals = [],
                          currents = ['''i_Na'''],
                          exports = ['''comp19_Vrest''', '''comp19_V_t''', '''comp20_C''', '''comp21_e_Na''', '''comp21_gbar_Na''', '''Na_m33''', '''Na_h34'''],
                          hasEvents = False,
                          nemoVersionString = '''NEMO (http://wiki.call-cc.org/nemo) version 9.0''',
                          currentTimestamp = '''Mon Sep 22 19:32:25 2014''',
                          modelName = '''hodgkin_huxley_Na''',
                          ODEmethod = '''cnexp''',
                          indent = 2)

output_K = template.render(functionDefs = [{'indent' : 2, 'name' : '''comp51_bnf''', 'vars' : ['''v'''], 'localVars' : [], 'exprString' : '''comp51_bnf  =  0.125 * exp(-(v + 65.0) / 80.0)'''}, {'indent' : 2, 'name' : '''comp51_anf''', 'vars' : ['''v'''], 'localVars' : [], 'exprString' : '''comp51_anf  =  0.01 * (v + 55.0) / (1.0 + -(exp(-(v + 55.0) / 10.0)))'''}],
                            transientEventEqDefs = [],
                            externalEventEqDefs = [],
                            eventVars = [],
                            eventLocals = [],
                            initEqDefs = ['''K_m61  = 
                            (comp51_anf(comp49_Vrest)) /
                            (comp51_anf(comp49_Vrest) + comp51_bnf(comp49_Vrest))''', '''K_m61O  =  K_m61'''],
                            initEqLocals = [],
                            reversalPotentialEqDefs = [],
                            kineticEqDefs = [],
                            kineticEqLocals = [],
                            externalEqDefs = [],
                            rateEqDefs = ['''v86  =  K_m61O
                            K_m61O'  =  (1.0 - v86) * (comp51_anf(v)) - K_m61O * comp51_bnf(v)'''],
                            rateEqLocals = ['''v86'''],
                            reactionEqDefs = ['''K_m61  =  K_m61O'''],
                            reactionEqLocals = [],
                            assignedEqDefs = ['''ek  =  comp51_e_K'''],
                            assignedEqLocals = [],
                            assignedDefs = ['''v''', '''ik''', '''ek''', '''i_K'''],
                            stateDefs = ['''K_m61C''', '''K_m61O''', '''K_m61'''],
                            parameterDefs = ['''comp49_V_t  =  -35.0''', '''comp51_e_K  =  -77.0''', '''comp49_Vrest  =  -65.0''', '''comp50_C  =  1.0''', '''comp51_gbar_K  =  0.036'''],
                            parameterLocals = [],
                            rangeParameters = ['''comp51_e_K'''],
                            useIons = [{'nonSpecific' : False, 'name' : '''k''', 'read' : ['''ek'''], 'write' : ['''ik'''], 'valence' : False}],
                            poolIons = [],
                            accumulatingIons = [],
                            modulatingIons = [],
                            permeatingIons = [{'species' : '''k''', 'i' : '''ik''', 'e' : '''ek''', 'erev' : '''comp51:e_K''', 'valence' : False}],
                            currentEqDefs = ['''i_K  =  (comp51_gbar_K * K_m61 ^ 4.0) * (v - comp51_e_K)''', '''ik  =  i_K'''],
                            currentEqLocals = [],
                            currents = ['''i_K'''],
                            exports = ['''comp49_Vrest''', '''comp49_V_t''', '''comp50_C''', '''comp51_gbar_K''', '''comp51_e_K''', '''K_m61'''],
                            hasEvents = False,
                            nemoVersionString = '''NEMO (http://wiki.call-cc.org/nemo) version 9.0''',
                            currentTimestamp = '''Mon Sep 22 19:32:25 2014''',
                            modelName = '''hodgkin_huxley_K''',
                            ODEmethod = '''cnexp''',
                            indent = 2)

output_Leak = template.render(  functionDefs = [],
                                transientEventEqDefs = [],
                                externalEventEqDefs = [],
                                eventVars = [],
                                eventLocals = [],
                                initEqDefs = [],
                                initEqLocals = [],
                                reversalPotentialEqDefs = ['''e  =  comp78_e_Leak'''],
                                kineticEqDefs = [],
                                kineticEqLocals = [],
                                externalEqDefs = [],
                                rateEqDefs = [],
                                rateEqLocals = [],
                                reactionEqDefs = [],
                                reactionEqLocals = [],
                                assignedEqDefs = ['''e  =  comp78_e_Leak'''],
                                assignedEqLocals = [],
                                assignedDefs = ['''v''', '''i''', '''e''', '''i_Leak'''],
                                stateDefs = [],
                                parameterDefs = ['''comp78_e_Leak  =  -54.4''', '''comp78_gbar_Leak  =  0.0003''', '''comp76_Vrest  =  -65.0''', '''comp76_V_t  =  -35.0''', '''comp77_C  =  1.0'''],
                                parameterLocals = [],
                                rangeParameters = ['''comp78_e_Leak'''],
                                useIons = [{'nonSpecific' : True, 'name' : '''i'''}],
                                poolIons = [],
                                accumulatingIons = [],
                                modulatingIons = [],
                                permeatingIons = [{'species' : '''non-specific''', 'i' : '''i''', 'e' : '''e''', 'erev' : '''comp78:e_Leak''', 'valence' : False}],
                                currentEqDefs = ['''i_Leak  =  comp78_gbar_Leak * (v - comp78_e_Leak)''', '''i  =  i_Leak'''],
                                currentEqLocals = [],
                                currents = ['''i_Leak'''],
                                exports = ['''comp76_Vrest''', '''comp76_V_t''', '''comp77_C''', '''comp78_e_Leak''', '''comp78_gbar_Leak'''],
                                hasEvents = False,
                                nemoVersionString = '''NEMO (http://wiki.call-cc.org/nemo) version 9.0''',
                                currentTimestamp = '''Mon Sep 22 19:32:25 2014''',
                                modelName = '''hodgkin_huxley_Leak''',
                                ODEmethod = '''cnexp''',
                                indent = 2)

with open('hodgkin_huxley_Na.mod', 'w') as f:
    f.write(output_Na)
with open('hodgkin_huxley_K.mod', 'w') as f:
    f.write(output_K)
with open('hodgkin_huxley_Leak.mod', 'w') as f:
    f.write(output_Leak)
