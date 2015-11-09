"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
from abc import ABCMeta, abstractmethod
import pyNN.connectors
from .values import get_pyNN_value


class Connector(object):

    __metaclass__ = ABCMeta

    def __init__(self, nineml_params, rng=None):
        PyNNClass = getattr(self._pynn_module(), self.pyNN_name)
        PyNNClass.__init__(self, **self._convert_params(nineml_params, rng))

    @classmethod
    def _convert_params(cls, nineml_props, rng):
        """
        Converts parameters from lib9ml objects into values with 'quantities'
        units and or random distributions
        """
        converted_params = {}
        for prop in nineml_props.properties:
            val = get_pyNN_value(prop, cls._unit_handler, rng)
            converted_params[cls.translate(prop.name)] = val
        return converted_params

    @classmethod
    def translate(cls, name):
        return cls.nineml_translations[name]

    @abstractmethod
    def _pynn_module(self):
        pass


class OneToOneConnector(Connector, pyNN.connectors.OneToOneConnector):

    pyNN_name = 'OneToOneConnector'
    nineml_translations = {}


class AllToAllConnector(Connector, pyNN.connectors.AllToAllConnector):

    pyNN_name = 'AllToAllConnector'
    nineml_translations = {'allowSelfConnections': 'allow_self_connections'}


class ExplicitConnectionListConnector(Connector,
                                      pyNN.connectors.FromListConnector):

    pyNN_name = 'FromListConnector'
    nineml_translations = {'allowSelfConnections': 'allow_self_connections',
                           'probability': 'p_connect'}


class FixedProbabilityConnector(Connector,
                                pyNN.connectors.FixedProbabilityConnector):

    pyNN_name = 'FixedProbabilityConnector'
    nineml_translations = {'allowSelfConnections': 'allow_self_connections',
                           'probability': 'p_connect'}


class FixedNumberPostConnector(
        Connector, pyNN.connectors.FixedNumberPostConnector):

    pyNN_name = 'FixedNumberPostConnector'
    nineml_translations = {
        'allowSelfConnections': 'allow_self_connections', 'number': 'n'}


class FixedNumberPreConnector(
        Connector, pyNN.connectors.FixedNumberPreConnector):

    pyNN_name = 'FixedNumberPreConnector'
    nineml_translations = {
        'allowSelfConnections': 'allow_self_connections', 'number': 'n'}
