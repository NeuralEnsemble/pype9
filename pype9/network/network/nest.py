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
from pyNN.nest import setup
from nest.hl_api import NESTError
from pyNN.common.control import build_state_queries
from . import Network as BaseNetwork
import pyNN.nest.simulator as simulator
from ..population.nest import Population
from ..projection.nest import Projection


(get_current_time, get_time_step,
 get_min_delay, get_max_delay,
 num_processes, rank) = build_state_queries(simulator)


class Network(BaseNetwork):

    _PopulationClass = Population
    _ProjectionClass = Projection

    def __init__(self, filename, build_mode='lazy', timestep=None,
                 min_delay=None, max_delay=None, temperature=None,
                 silent_build=False, flags=[], solver_name='cvode', rng=None):
        # Sets the 'get_min_delay' function for use in the network init
        self.get_min_delay = get_min_delay
        self.temperature = None
        BaseNetwork.__init__(
            self, filename, build_mode=build_mode, timestep=timestep,
            min_delay=min_delay, max_delay=max_delay, temperature=temperature,
            silent_build=silent_build, flags=flags, solver_name=solver_name,
            rng=rng)

    def _set_simulation_params(self, **params):
        """
        Sets the simulation parameters either from the passed parameters or
        from the nineml description

        @param params[**kwargs]: Parameters that are either passed to the pyNN
                                 setup method or set explicitly
        """
        p = self._get_simulation_params(**params)
        try:
            setup(p['timestep'], p['min_delay'], p['max_delay'])
        except NESTError as e:
            raise Exception("There was an error setting the min_delay of the "
                            "simulation, try changing the values for timestep "
                            "({time}) and min_delay ({delay}). (Message - {e})"
                            .format(time=p['timestep'], delay=p['min_delay'],
                                    e=e))
        self.temperature = p['temperature']
