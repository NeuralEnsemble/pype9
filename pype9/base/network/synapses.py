"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
from abc import ABCMeta
from .values import get_pyNN_value


class Synapse(object):

    __metaclass__ = ABCMeta

    def __init__(self, nineml_params, min_delay, rng):
        # Sorry if this feels a bit hacky (i.e. relying on the pyNN class being
        # the third class in the MRO), I thought of a few ways to do this but
        # none were completely satisfactory.
        PyNNClass = self.__class__.__mro__[3]
        assert (PyNNClass.__module__.startswith('pyNN') and
                PyNNClass.__module__.endswith('standardmodels.synapses'))
        params = self._convert_params(nineml_params, rng)
        params['delay'].set_min_value(min_delay)
        super(PyNNClass, self).__init__(**params)

    @classmethod
    def _convert_params(cls, nineml_props, rng):
        """
        Converts parameters from lib9ml objects into values with 'quantities'
        units and or random distributions
        """
        converted_params = {}
        for prop in nineml_props.iteritems():
            val = get_pyNN_value(prop, rng, cls._unit_handler)
            converted_params[cls.nineml_translations[prop.name]] = val
        return converted_params


class StaticSynapse(Synapse):

    nineml_translations = {'weight': 'weight', 'delay': 'delay'}


class ElectricalSynapse(Synapse):

    nineml_translations = {'weight': 'weight'}
