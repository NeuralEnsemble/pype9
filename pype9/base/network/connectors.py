"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
from nineml.user.projection import Connectivity
from pyNN.parameters import LazyArray
import numpy


class PyNNConnectivity(Connectivity):

    def __init__(self, *args, **kwargs):
        super(PyNNConnectivity, self).__init__(*args, **kwargs)
        self._prev_connected = None

    def connections(self):
        super(PyNNConnectivity, self).connections

    def connect(self, projection):
        if self._cache:
            connector = self._pyNN_module.FromListConnector(self._cache)
            connector.connect(projection)
        elif self._prev_connected:
            # Get connection from previously connected projection
            connection_map = LazyArray(~numpy.isnan(
                self.reference_projection.get(
                    ['weight'], 'array', gather='all')[0]))
            connector = self._pyNN_module.MapConnector()
            connector._connect_with_map(projection, connection_map)
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
                params = {'p_connect',
                          int(self._rule_props.property('probability').value)}
            elif self._rule_props.lib_type == 'RandomFanIn':
                connector_cls = self._pyNN_module.FixedNumberPostConnector
                params = {'n', int(self._rule_props.property('number').value)}
            elif self._rule_props.lib_type == 'RandomFanOut':
                connector_cls = self._pyNN_module.FixedNumberPreConnector
                params = {'n', int(self._rule_props.property('number').value)}
            else:
                assert False
            params.update(self._kwargs)
            connector = connector_cls(**params)
            connector.connect(projection)
            self._prev_connected = projection
