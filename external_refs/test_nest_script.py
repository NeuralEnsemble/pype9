"""

This file is just for testing my NEST installation

"""

import math
import pylab
import nest


Params = {'N'         : 40,
        'visSize'     : 8.0,
        'fdg'         : 2.0,
        'lambdadg'    : 2.0,
        'phidg'       : 0.0,
        'retDC'       : 30.0,
        'retAC'       : 30.0,
        'simtime'     : 100.0,
        'siminterval' : 5.0
        }


nest.CopyModel('iaf_cond_alpha', 'NeuronModel',
               params={ 'C_m'         : 16.0,
                        'E_L'         : (0.2 * 30.0 + 1.5 * -90.0) / (0.2 + 1.5),
                        'g_L'         : 0.2 + 1.5,
                        'E_ex'        : 0.0,
                        'E_in'        :-70.0,
                        'V_reset'     :-60.0,
                        'V_th'        :-51.0,
                        't_ref'       : 2.0,
                        'tau_syn_ex'  : 1.0,
                        'tau_syn_in'  : 2.0,
                        'I_e'         : 0.0,
                        'V_m'         :-70.0})

nest.CopyModel('NeuronModel', 'CtxExNeuron')


nest.CopyModel('NeuronModel', 'CtxInNeuron',
               params={'C_m'    : 8.0,
                        'V_th'  :-53.0,
                        't_ref' : 1.0})


nest.CopyModel('NeuronModel', 'ThalamicNeuron',
                params={'Cm'    : 8.0,
                        'Vth'   :-53.0,
                        'tref'  : 1.0,
                        'Ein'   :-80.0})


def phiInit(pos, lam, alpha):
  """Initializer function for phase of drifting grating nodes.
  
    @param pos [tuple(2)]:  Position(x,y) of node, in degree
    @param lam [float]:  Wavelength of grating, in degree
    @param alpha [float]:  Angle of grating in radian, zero is horizontal
  
    @return Number to be used as phase of AC Poisson generator.
  """

  return 2.0 * math.pi / lam * (math.cos(alpha) * pos[0] + math.sin(alpha) * pos[1])
  nest.CopyModel('acpoissongenerator', 'RetinaNode',
                  params={'AC'    : [Params['retAC']],
                          'DC'    : Params['retDC'],
                          'Freq'  : [Params['fdg']],
                          'Phi'   : [0.0]})





#from scipy.optimize import bisect
#from nest import *
#import nest.voltage_trace as voltage_trace


#t_sim = 10000.0
#n_ex = 16000
#n_in = 4000
#r_ex = 5.0
#r_in = 12.5
#epsc = 45.0
#ipsc = -45.0
#neuron = Create("iaf_neuron")
#noise = Create("poisson_generator", 2)
#voltmeter = Create("voltmeter")
#spikedetector = Create("spike_detector")
#SetStatus(noise, [{"rate":n_ex * r_ex}, {"rate":n_in * r_in}])
#SetStatus(voltmeter, {"interval": 10.0, "withgid": True})
#ConvergentConnect(noise, neuron, [epsc, ipsc], 1.0)
#Connect(voltmeter, neuron)
#Connect(neuron, spikedetector)
#def output_rate(guess):
#    rate = float(abs(n_in * guess))
#    SetStatus([noise[1]], "rate", rate)
#    SetStatus(spikedetector, "n_events", 0)
#    Simulate(t_sim)
#    r_target = GetStatus(spikedetector, "n_events")[0] * 1000.0 / t_sim
#    print "  r_in=%.4f Hz, r_target=%.3f Hz" % (guess, r_target)
#    return r_target
#print "Desired target rate: %.2f Hz" % r_ex
#in_rate = bisect(lambda x: output_rate(x) - r_ex, 5.0, 25.0, xtol=0.01)

