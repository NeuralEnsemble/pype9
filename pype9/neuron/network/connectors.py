"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
import pyNN.neuron.connectors
from pype9.base.network.connectors import Connector as BaseConnector


class Connector(BaseConnector):

    def _pynn_module(self):
        return pyNN.neuron.connectors


class OneToOneConnector(Connector, pyNN.connectors.OneToOneConnector):
    pass


class AllToAllConnector(Connector, pyNN.connectors.AllToAllConnector):
    pass


class ExplicitConnectionListConnector(Connector,
                                      pyNN.connectors.FromListConnector):
    pass


class FixedProbabilityConnector(Connector,
                                pyNN.connectors.FixedProbabilityConnector):
    pass


class FixedNumberPostConnector(
        Connector, pyNN.connectors.FixedNumberPostConnector):
    pass


class FixedNumberPreConnector(
        Connector, pyNN.connectors.FixedNumberPreConnector):
    pass
