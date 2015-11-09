"""

  This package mirrors the one in pyNN

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
import sys
from pype9.exceptions import Pype9RuntimeError
# Remove any system arguments that may conflict with
if '--debug' in sys.argv:
    raise Pype9RuntimeError(
        "'--debug' argument passed to script conflicts with an argument to "
        "nest, causing the import to stop at the NEST prompt")
import pyNN.nest
from nest.hl_api import NESTError
from pyNN.common.control import build_state_queries
from pype9.base.network.base import (
    Network as BaseNetwork, DynamicsArray as BaseDynamicsArray,
    ConnectionGroup as BaseConnectionGroup)
import pyNN.nest.simulator as simulator
from .cell_wrapper import PyNNCellWrapperMetaClass
from pype9.nest.network import synapses as synapses_module
from .connectors import Connector


(get_current_time, get_time_step,
 get_min_delay, get_max_delay,
 num_processes, rank) = build_state_queries(simulator)


class DynamicsArray(BaseDynamicsArray, pyNN.nest.Population):

    @classmethod
    def _translate_variable(cls, variable):
        # FIXME: This is a bit of a hack until I coordinate with Ivan about the
        # naming of variables in NEST
        if variable.startswith('{'):
            variable = variable[variable.find('}') + 1:]
        if variable == 'v':
            variable = 'V_m'
        return variable

    def record(self, variable, to_file=None):
        variable = self._translate_variable(variable)
        super(DynamicsArray, self).record(variable, to_file)

    def _get_cell_initial_value(self, id, variable):  # @ReservedAssignment
        """Get the initial value of a state variable of the cell."""
        return super(DynamicsArray, self)._get_cell_initial_value(
            id, self._translate_variable(variable))

    def initialize(self, **initial_values):
        """
        Set initial values of state variables, e.g. the membrane potential.

        Values passed to initialize() may be:
            (1) single numeric values (all neurons set to the same value)
            (2) RandomDistribution objects
            (3) lists/arrays of numbers of the same size as the population
            (4) mapping functions, where a mapping function accepts a single
                argument (the cell index) and returns a single number.

        Values should be expressed in the standard PyNN units (i.e. millivolts,
        nanoamps, milliseconds, microsiemens, nanofarads, event per second).

        Examples::

            p.initialize(v=-70.0)
            p.initialize(v=rand_distr, gsyn_exc=0.0)
            p.initialize(v=lambda i: -65 + i/10.0)
        """
        translated_initial_values = {}
        for name, value in initial_values.iteritems():
            translated_name = self.celltype.translations[
                name]['reverse_transform']
            translated_initial_values[translated_name] = value
        super(DynamicsArray, self).initialize(**translated_initial_values)

    def _pynn_cell_wrapper_meta_class(self):
        return PyNNCellWrapperMetaClass

    def _pynn_population_class(self):
        return pyNN.nest.Population


class ConnectionGroup(BaseConnectionGroup, pyNN.nest.Projection):

    _synapses_module = synapses_module

    @classmethod
    def get_min_delay(self):
        return get_min_delay()

    def _pynn_connector_class(self):
        raise Connector

    def _pynn_projection_class(self):
        return pyNN.nest.Projection


class Network(BaseNetwork):

    DynamicsArrayClass = DynamicsArray
    ConnectionGroupClass = ConnectionGroup

    def __init__(self, nineml_model, min_delay=None, temperature=None,
                 **kwargs):
        # Sets the 'get_min_delay' function for use in the network init
        self.get_min_delay = get_min_delay
        self.temperature = None
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
        try:
            pyNN.nest.setup(p['timestep'], p['min_delay'], p['max_delay'])
        except NESTError as e:
            raise Exception("There was an error setting the min_delay of the "
                            "simulation, try changing the values for timestep "
                            "({time}) and min_delay ({delay}). (Message - {e})"
                            .format(time=p['timestep'], delay=p['min_delay'],
                                    e=e))
        self.temperature = p['temperature']
