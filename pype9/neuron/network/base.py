"""

  This package mirrors the one in pyNN

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
# This is required to ensure that the right MPI variables are set before
# NEURON is initiated to avoid NEURON bug
from __future__ import absolute_import
try:
    from mpi4py import MPI  # @UnresolvedImport @UnusedImport
except:
    pass
import pyNN.neuron
from pyNN.common.control import build_state_queries
import pyNN.neuron.simulator as simulator
from pyNN.neuron.standardmodels.synapses import StaticSynapse
import neuron
import logging
from pype9.base.network.base import (
    Network as BaseNetwork, ComponentArray as BaseComponentArray,
    ConnectionGroup as BaseConnectionGroup, Selection as BaseSelection)
from .cell_wrapper import PyNNCellWrapperMetaClass
from .connectivity import PyNNConnectivity
from ..cells.code_gen import CodeGenerator as CellCodeGenerator  # @IgnorePep8
from ..units import UnitHandler  # @IgnorePep8

logger = logging.getLogger("PyPe9")

get_current_time, get_time_step, get_min_delay, \
    get_max_delay, num_processes, rank = build_state_queries(simulator)


class ComponentArray(BaseComponentArray, pyNN.neuron.Population):

    PyNNCellWrapperMetaClass = PyNNCellWrapperMetaClass
    PyNNPopulationClass = pyNN.neuron.Population
    UnitHandler = UnitHandler


class Selection(BaseSelection, pyNN.neuron.Assembly):

    PyNNAssemblyClass = pyNN.neuron.Assembly


class ConnectionGroup(BaseConnectionGroup, pyNN.neuron.Projection):

    SynapseClass = StaticSynapse
    PyNNProjectionClass = pyNN.neuron.Projection
    UnitHandler = UnitHandler

    @classmethod
    def get_min_delay(self):
        return get_min_delay()


class Network(BaseNetwork):

    ComponentArrayClass = ComponentArray
    SelectionClass = Selection
    ConnectionGroupClass = ConnectionGroup
    ConnectivityClass = PyNNConnectivity
    CellCodeGenerator = CellCodeGenerator

    def _set_simulation_params(self, timestep, min_delay, max_delay, **kwargs):
        """
        Sets the simulation parameters either from the passed parameters or
        from the nineml description

        @param params[**kwargs]: Parameters that are either passed to the pyNN
                                 setup method or set explicitly
        """
        pyNN.neuron.setup(timestep, min_delay, max_delay)
        if 'temperature' in kwargs:
            neuron.h.celsius = kwargs['temperature']

    @property
    def min_delay(self):
        return get_min_delay()

    @property
    def time_step(self):
        return get_time_step()

    @property
    def max_delay(self):
        return get_max_delay()

    @property
    def num_processes(self):
        return num_processes()

    @property
    def rank(self):
        return rank()

    @property
    def current_time(self):
        return get_current_time()
