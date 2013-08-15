from __future__ import absolute_import
import pyNN.neuron.standardmodels.synapses
from nineline.pyNN.common.synapses import Synapse

class StaticSynapse(Synapse, pyNN.neuron.standardmodels.synapses.StaticSynapse): pass
    
class ElectricalSynapse(Synapse, pyNN.neuron.standardmodels.synapses.ElectricalSynapse): pass