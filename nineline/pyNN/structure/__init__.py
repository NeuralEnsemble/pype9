"""

  This module contains extensions to the pyNN.space module

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
from abc import ABCMeta
import quantities
import nineml.user_layer
import pyNN.space
from pyNN.random import NumpyRNG, RandomDistribution
import nineline.pyNN.random
from . import layout


class Structure(object):

    def __init__(self, name, size, nineml_model, rng=None):
        self.name = name
        self.size = size
        self._positions = None
        LayoutClass = getattr(layout,
                              nineml_model.layout.definition.component.name)
        self.layout = LayoutClass(size, nineml_model.layout.parameters, rng)

    @property
    def positions(self):
        if self._positions is None:
            self._positions = self.layout.generate_positions(self.size)
        return self._positions
