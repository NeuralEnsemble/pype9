"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
import pyNN.neuron.standardmodels.synapses
import nineline.pyNN.common.synapses


class StaticSynapse(nineline.pyNN.common.synapses.StaticSynapse,
                    pyNN.neuron.standardmodels.synapses.StaticSynapse):
    pass


class ElectricalSynapse(nineline.pyNN.common.synapses.ElectricalSynapse,
                        pyNN.neuron.standardmodels.synapses.ElectricalSynapse):
    pass
