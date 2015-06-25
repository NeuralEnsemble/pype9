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
from pyNN.common.control import build_state_queries
import pyNN.neuron.standardmodels
import pyNN.neuron.simulator as simulator
from .wrapper import PyNNCellWrapperMetaClass
import logging
from .base import Population as BasePopulation


logger = logging.getLogger("PyNN")

get_current_time, get_time_step, get_min_delay, \
    get_max_delay, num_processes, rank = build_state_queries(simulator)


class Population(BasePopulation, pyNN.neuron.Population):

    _pyNN_standard_celltypes = dict(
        [(cellname, getattr(pyNN.neuron.standardmodels.cells, cellname))
         for cellname in pyNN.neuron.list_standard_models()])
    _CellMetaClass = PyNNCellWrapperMetaClass
