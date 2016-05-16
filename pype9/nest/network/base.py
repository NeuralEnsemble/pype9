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
from nest.hl_api import NESTError  # @IgnorePep8
from pyNN.common.control import build_state_queries  # @IgnorePep8
from pype9.base.network.base import (  # @IgnorePep8
    Network as BaseNetwork, ComponentArray as BaseComponentArray,
    ConnectionGroup as BaseConnectionGroup)
import pyNN.nest.simulator as simulator  # @IgnorePep8
from .cell_wrapper import PyNNCellWrapperMetaClass  # @IgnorePep8
from .synapses import StaticSynapse  # @IgnorePep8
from .connectivity import PyNNConnectivity  # @IgnorePep8
from ..cells.code_gen import CodeGenerator as CellCodeGenerator  # @IgnorePep8
from ..units import UnitHandler  # @IgnorePep8


(get_current_time, get_time_step,
 get_min_delay, get_max_delay,
 num_processes, rank) = build_state_queries(simulator)


class ComponentArray(BaseComponentArray, pyNN.nest.Population):

    PyNNCellWrapperMetaClass = PyNNCellWrapperMetaClass
    PyNNPopulationClass = pyNN.nest.Population
    UnitHandler = UnitHandler


class ConnectionGroup(BaseConnectionGroup, pyNN.nest.Projection):

    SynapseClass = StaticSynapse
    PyNNProjectionClass = pyNN.nest.Projection

    @classmethod
    def get_min_delay(self):
        return get_min_delay()


class Network(BaseNetwork):

    ComponentArrayClass = ComponentArray
    ConnectionGroupClass = ConnectionGroup
    ConnectivityClass = PyNNConnectivity
    CellCodeGenerator = CellCodeGenerator

    def _set_simulation_params(self, timestep, min_delay, max_delay, **kwargs):  # @UnusedVariable @IgnorePep8
        """
        Sets the simulation parameters either from the passed parameters or
        from the nineml description

        @param params[**kwargs]: Parameters that are either passed to the pyNN
                                 setup method or set explicitly
        """
        try:
            pyNN.nest.setup(timestep, min_delay, max_delay)
        except (NESTError, TypeError) as e:
            raise Exception("There was an error setting the min_delay of the "
                            "simulation, try changing the values for timestep "
                            "({time}) and min_delay ({delay}). (Message - {e})"
                            .format(time=timestep, delay=min_delay, e=e))

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
