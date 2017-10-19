"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
from builtins import object
from abc import ABCMeta
from .values import get_pyNN_value
from future.utils import with_metaclass


class Synapse(with_metaclass(ABCMeta, object)):

    def __init__(self, nineml_params, min_delay, rng):
        params = self._convert_params(nineml_params, rng)
        params['delay'].set_min_value(min_delay)
        super(self.PyNNClass, self).__init__(**params)

    @classmethod
    def _convert_params(cls, nineml_props, rng):
        """
        Converts parameters from lib9ml objects into values with 'quantities'
        units and or random distributions
        """
        converted_params = {}
        for prop in nineml_props.items():
            val = get_pyNN_value(prop, rng, cls.UnitHandler)
            converted_params[cls.nineml_translations[prop.name]] = val
        return converted_params


class StaticSynapse(Synapse):

    nineml_translations = {'weight': 'weight', 'delay': 'delay'}


class ElectricalSynapse(Synapse):

    nineml_translations = {'weight': 'weight'}
