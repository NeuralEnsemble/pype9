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
import neuron
import logging
from pype9.base.network.base import (
    Network as BaseNetwork, DynamicsArray as BaseDynamicsArray,
    ConnectionGroup as BaseConnectionGroup)
from .cell_wrapper import PyNNCellWrapperMetaClass
from pype9.neuron.network import synapses as synapses_module
from .connectors import Connector


logger = logging.getLogger("PyPe9")

get_current_time, get_time_step, get_min_delay, \
    get_max_delay, num_processes, rank = build_state_queries(simulator)


class DynamicsArray(BaseDynamicsArray, pyNN.neuron.Population):

    def _pynn_cell_wrapper_meta_class(self):
        return PyNNCellWrapperMetaClass

    def _pynn_population_class(self):
        return pyNN.neuron.Population


class ConnectionGroup(BaseConnectionGroup, pyNN.neuron.Projection):

    _synapses_module = synapses_module

    @classmethod
    def get_min_delay(self):
        return get_min_delay()

    def _pynn_connector_class(self):
        raise Connector

    def _pynn_projection_class(self):
        return pyNN.neuron.Projection


class Network(BaseNetwork):

    DynamicsArrayClass = DynamicsArray
    ConnectionGroupClass = ConnectionGroup

    def __init__(self, nineml_model, min_delay=None, temperature=None,
                 **kwargs):
        # Sets the 'get_min_delay' function for use in the network init
        self.get_min_delay = get_min_delay
        BaseNetwork.__init__(
            self, nineml_model, min_delay=min_delay, temperature=temperature,
            **kwargs)

    def _set_simulation_params(self, **params):
        """
        Sets the simulation parameters either from the passed parameters or
        from the nineml description

        @param params[**kwargs]: Parameters that are either passed to the pyNN
                                 setup method or set explicitly
        """
        p = self._get_simulation_params(**params)
        pyNN.neuron.setup(p['timestep'], p['min_delay'], p['max_delay'])
        neuron.h.celsius = p['temperature']
