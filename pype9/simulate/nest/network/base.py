"""

  This package mirrors the one in pyNN

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
import sys
from pype9.exceptions import Pype9RuntimeError
# Remove any system arguments that may conflict with
if '--debug' in sys.argv:
    raise Pype9RuntimeError(
        "'--debug' argument passed to script conflicts with an argument to "
        "nest, causing the import to stop at the NEST prompt")
import pyNN.nest  # @IgnorePep8
from pyNN.common.control import build_state_queries  # @IgnorePep8
from pyNN.nest.standardmodels.synapses import StaticSynapse  # @IgnorePep8
from pype9.simulate.common.network.base import (  # @IgnorePep8
    Network as BaseNetwork, ComponentArray as BaseComponentArray,
    ConnectionGroup as BaseConnectionGroup, Selection as BaseSelection)
import pyNN.nest.simulator as simulator  # @IgnorePep8
from .cell_wrapper import PyNNCellWrapperMetaClass  # @IgnorePep8
from .connectivity import PyNNConnectivity  # @IgnorePep8
from ..code_gen import CodeGenerator as CodeGenerator  # @IgnorePep8
from ..units import UnitHandler  # @IgnorePep8
from ..simulation import Simulation  # @IgnorePep8


(get_current_time, get_time_step,
 get_min_delay, get_max_delay,
 num_processes, rank) = build_state_queries(simulator)


class ComponentArray(BaseComponentArray, pyNN.nest.Population):

    PyNNCellWrapperMetaClass = PyNNCellWrapperMetaClass
    PyNNPopulationClass = pyNN.nest.Population
    PyNNProjectionClass = pyNN.nest.Projection
    SynapseClass = StaticSynapse
    SpikeSourceArray = pyNN.nest.SpikeSourceArray
    AllToAllConnector = pyNN.nest.AllToAllConnector
    OneToOneConnector = pyNN.nest.OneToOneConnector
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
        pyNN.nest.Population.record(self, to_record)


class Selection(BaseSelection, pyNN.nest.Assembly):

    PyNNAssemblyClass = pyNN.nest.Assembly


class ConnectionGroup(BaseConnectionGroup, pyNN.nest.Projection):

    SynapseClass = StaticSynapse
    PyNNProjectionClass = pyNN.nest.Projection
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
