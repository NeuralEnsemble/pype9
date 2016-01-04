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
import pyNN.nest  # @IgnorePep8
from nest.hl_api import NESTError  # @IgnorePep8
from pyNN.common.control import build_state_queries  # @IgnorePep8
from pype9.base.network.base import (  # @IgnorePep8
    Network as BaseNetwork, ComponentArray as BaseComponentArray,
    ConnectionGroup as BaseConnectionGroup)
import pyNN.nest.simulator as simulator  # @IgnorePep8
from .cell_wrapper import PyNNCellWrapperMetaClass  # @IgnorePep8
from pype9.nest.network.synapses import StaticSynapse  # @IgnorePep8
from .connectivity import PyNNConnectivity  # @IgnorePep8


(get_current_time, get_time_step,
 get_min_delay, get_max_delay,
 num_processes, rank) = build_state_queries(simulator)


class ComponentArray(BaseComponentArray, pyNN.nest.Population):

    PyNNCellWrapperMetaClass = PyNNCellWrapperMetaClass
    PyNNPopulationClass = pyNN.nest.Population

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
        super(ComponentArray, self).record(variable, to_file)

    def _get_cell_initial_value(self, id, variable):  # @ReservedAssignment
        """Get the initial value of a state variable of the cell."""
        return super(ComponentArray, self)._get_cell_initial_value(
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
        super(ComponentArray, self).initialize(**translated_initial_values)


class ConnectionGroup(BaseConnectionGroup, pyNN.nest.Projection):

    SynapseClass = StaticSynapse
    PyNNProjectionClass = pyNN.nest.Projection

    @classmethod
    def get_min_delay(self):
        return get_min_delay()


class Network(BaseNetwork):

    ComponentArrayClass = ComponentArray
    ConnectionGroupClass = ConnectionGroup
    ConnectivityClass = PyNNConnectivity

    def _set_simulation_params(self, timestep, min_delay, max_delay, **kwargs):  # @UnusedVariable @IgnorePep8
        """
        Sets the simulation parameters either from the passed parameters or
        from the nineml description

        @param params[**kwargs]: Parameters that are either passed to the pyNN
                                 setup method or set explicitly
        """
        try:
            pyNN.nest.setup(timestep, min_delay, max_delay)
        except (NESTError, TypeError) as e:
            raise Exception("There was an error setting the min_delay of the "
                            "simulation, try changing the values for timestep "
                            "({time}) and min_delay ({delay}). (Message - {e})"
                            .format(time=timestep, delay=min_delay, e=e))

    @property
    def min_delay(self):
        return get_min_delay()

    @property
    def time_step(self):
        return get_time_step()

    @property
    def max_delay(self):
        return get_max_delay()

    @property
    def num_processes(self):
        return num_processes()

    @property
    def rank(self):
        return rank()

    @property
    def current_time(self):
        return get_current_time()
