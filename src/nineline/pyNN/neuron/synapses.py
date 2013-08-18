from __future__ import absolute_import
import pyNN.neuron.standardmodels.synapses
import nineline.pyNN.common.synapses

class StaticSynapse(nineline.pyNN.common.synapses.StaticSynapse, 
                    pyNN.neuron.standardmodels.synapses.StaticSynapse): pass
    
class ElectricalSynapse(nineline.pyNN.common.synapses.ElectricalSynapse, 
                        pyNN.neuron.standardmodels.synapses.ElectricalSynapse): pass