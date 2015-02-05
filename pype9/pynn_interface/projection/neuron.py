"""

  This package mirrors the one in pyNN

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
# This is required to ensure that the right MPI variables are set before
# NEURON is initiated
from __future__ import absolute_import
try:
    from mpi4py import MPI  # @UnresolvedImport @UnusedImport
except:
    pass
import pyNN.neuron
from pyNN.common.control import build_state_queries
import pyNN.neuron.simulator as simulator
from pype9.pynn_interface.synapses import neuron as synapses_module
import logging
from .base import Projection as BaseProjection


logger = logging.getLogger("PyNN")

(_, _, get_min_delay, _, _, _) = build_state_queries(simulator)


class Projection(BaseProjection, pyNN.neuron.Projection):

    _synapses_module = synapses_module

    @classmethod
    def get_min_delay(self):
        return get_min_delay()
