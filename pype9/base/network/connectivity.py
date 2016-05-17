"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
from nineml.user.projection import (
    BaseConnectivity, InverseConnectivity as BaseInverseConnectivity)
from pyNN.parameters import LazyArray
import numpy
from pype9.exceptions import Pype9RuntimeError


class PyNNConnectivity(BaseConnectivity):

    def __init__(self, *args, **kwargs):
        super(PyNNConnectivity, self).__init__(*args, **kwargs)
        self._prev_connected = None

    def connections(self):
        if not self.has_been_sampled():
            raise Pype9RuntimeError(
                "Connections have not been generated for PyNNConnectivity "
                "object (they are only generated during network construction "
                "for efficiency")
        raise NotImplementedError(
            "Need to work out connection list from connection map")

    def connect(self, connection_group):
        if self.has_been_sampled():
            # Get connection from previously connected projection
            connector = self._pyNN_module.MapConnector()
            connector._connect_with_map(connection_group, self._connection_map)
        else:
            if self._rule_props.lib_type == 'AllToAll':
                connector_cls = self._pyNN_module.AllToAllConnector
                params = {}
            elif self._rule_props.lib_type == 'OneToOne':
                connector_cls = self._pyNN_module.OneToOneConnector
                params = {}
            elif self._rule_props.lib_type == 'ExplicitConnectionList':
                connector_cls = self._pyNN_module.FromListConnector
                params = {}
            elif self._rule_props.lib_type == 'ProbabilisticConnectivity':
                connector_cls = self._pyNN_module.FixedProbabilityConnector
                params = {
                    'p_connect':
                    float(self._rule_props.property('probability').value)}
            elif self._rule_props.lib_type == 'RandomFanIn':
                connector_cls = self._pyNN_module.FixedNumberPostConnector
                params = {'n': int(self._rule_props.property('number').value)}
            elif self._rule_props.lib_type == 'RandomFanOut':
                connector_cls = self._pyNN_module.FixedNumberPreConnector
                params = {'n': int(self._rule_props.property('number').value)}
            else:
                assert False
            params.update(self._kwargs)
            connector = connector_cls(**params)
            connector.connect(connection_group)
            self._prev_connected = connection_group

    def has_been_sampled(self):
        return self._prev_connected is not None

    @property
    def _connection_map(self):
        return LazyArray(~numpy.isnan(
            self._prev_connected.get(['weight'], 'array', gather='all')[0]))


class InversePyNNConnectivity(BaseInverseConnectivity):

    def connect(self, connection_group):
        raise NotImplementedError(
            "Inverse connectivity from post-synaptic/synapse dynamics to "
            "pre-synaptic dynamics has not been implemented yet.")
