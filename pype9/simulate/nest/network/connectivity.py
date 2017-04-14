"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
import pyNN.nest.connectors
from pype9.simulate.common.network.connectivity import (
    PyNNConnectivity as BasePyNNConnectivity)


class PyNNConnectivity(BasePyNNConnectivity):

    _pyNN_module = pyNN.nest.connectors
