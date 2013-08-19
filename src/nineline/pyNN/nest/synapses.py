from __future__ import absolute_import
import pyNN.nest.standardmodels.synapses
from nineline.pyNN.common.synapses import StaticSynapse

class StaticSynapse(StaticSynapse, pyNN.nest.standardmodels.synapses.StaticSynapse): pass
    
# class ElectricalSynapse(Synapse, pyNN.nest.standardmodels.synapses.ElectricalSynapse): pass