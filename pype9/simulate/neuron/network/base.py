"""

  This package mirrors the one in pyNN

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
import pyNN.neuron
from pyNN.common.control import build_state_queries
import pyNN.neuron.simulator as simulator
from pyNN.neuron.standardmodels.synapses import StaticSynapse
import logging
from pype9.simulate.common.network.base import (
    Network as BaseNetwork, ComponentArray as BaseComponentArray,
    ConnectionGroup as BaseConnectionGroup, Selection as BaseSelection)
from .cell_wrapper import PyNNCellWrapperMetaClass
from .connectivity import PyNNConnectivity
from ..code_gen import CodeGenerator as CodeGenerator  # @IgnorePep8
from ..units import UnitHandler  # @IgnorePep8
from ..simulation import Simulation  # @IgnorePep8

logger = logging.getLogger("pype9")

get_current_time, get_time_step, get_min_delay, \
    get_max_delay, num_processes, rank = build_state_queries(simulator)


class ComponentArray(BaseComponentArray, pyNN.neuron.Population):

    PyNNCellWrapperMetaClass = PyNNCellWrapperMetaClass
    PyNNPopulationClass = pyNN.neuron.Population
    PyNNProjectionClass = pyNN.neuron.Projection
    SynapseClass = StaticSynapse
    SpikeSourceArray = pyNN.neuron.SpikeSourceArray
    AllToAllConnector = pyNN.neuron.AllToAllConnector
    OneToOneConnector = pyNN.neuron.OneToOneConnector
    UnitHandler = UnitHandler
    Simulation = Simulation

    def __init__(self, *args, **kwargs):
        super(ComponentArray, self).__init__(*args, **kwargs)

    @property
    def _min_delay(self):
        return get_min_delay()

    def record(self, port_name):
        communicates, to_record = self._get_port_details(port_name)
        if communicates == 'event':
            to_record = 'spikes'  # FIXME: Need a way of differentiating event send ports @IgnorePep8
        pyNN.neuron.Population.record(self, to_record)


class Selection(BaseSelection, pyNN.neuron.Assembly):

    PyNNAssemblyClass = pyNN.neuron.Assembly


class ConnectionGroup(BaseConnectionGroup, pyNN.neuron.Projection):

    SynapseClass = StaticSynapse
    PyNNProjectionClass = pyNN.neuron.Projection
    UnitHandler = UnitHandler
    Simulation = Simulation

    @classmethod
    def get_min_delay(self):
        return get_min_delay()


class Network(BaseNetwork):

    ComponentArrayClass = ComponentArray
    SelectionClass = Selection
    ConnectionGroupClass = ConnectionGroup
    ConnectivityClass = PyNNConnectivity
    CodeGenerator = CodeGenerator
    Simulation = Simulation

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
