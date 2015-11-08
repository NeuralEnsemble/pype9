"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
from abc import ABCMeta
import pyNN.connectors
from .values import get_pyNN_value


class Connector(object):

    __metaclass__ = ABCMeta

    def __init__(self, nineml_params, rng=None):
        # Sorry if this feels a bit hacky (i.e. relying on the pyNN class being
        # the third class in the MRO), I thought of a few ways to do this but
        # none were completely satisfactory.
        PyNNClass = self.__class__.__mro__[2]
        assert (PyNNClass.__module__.startswith('pyNN') and
                PyNNClass.__module__.endswith('connectors'))
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


class OneToOneConnector(Connector, pyNN.connectors.OneToOneConnector):

    nineml_translations = {}


class AllToAllConnector(Connector, pyNN.connectors.AllToAllConnector):

    nineml_translations = {'allowSelfConnections': 'allow_self_connections'}


class ExplicitConnectionListConnector(Connector,
                                      pyNN.connectors.FromListConnector):

    nineml_translations = {'allowSelfConnections': 'allow_self_connections',
                           'probability': 'p_connect'}


class FixedProbabilityConnector(Connector,
                                pyNN.connectors.FixedProbabilityConnector):

    nineml_translations = {'allowSelfConnections': 'allow_self_connections',
                           'probability': 'p_connect'}


class FixedNumberPostConnector(
        Connector, pyNN.connectors.FixedNumberPostConnector):

    nineml_translations = {
        'allowSelfConnections': 'allow_self_connections', 'number': 'n'}


class FixedNumberPreConnector(
        Connector, pyNN.connectors.FixedNumberPreConnector):

    nineml_translations = {
        'allowSelfConnections': 'allow_self_connections', 'number': 'n'}
