"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
import pyNN.nest.standardmodels.synapses
from pype9.simulate.common.network.synapses import StaticSynapse


class StaticSynapse(StaticSynapse,
                    pyNN.nest.standardmodels.synapses.StaticSynapse):
    pass

# class ElectricalSynapse(Synapse,
#                    pyNN.nest.standardmodels.synapses.ElectricalSynapse):
#     pass
