"""

  This package mirrors the one in pyNN

  @file __init__.py
  @author Tom Close

"""

##########################################################################
#
#  Copyright 2012 Okinawa Institute of Science and Technology (OIST), Okinawa, Japan
#
##########################################################################
from __future__ import absolute_import
import sys
# Remove any system arguments that may conflict with
if '--debug' in sys.argv:
    raise Exception("'--debug' argument passed to script conflicts with an "
                    "argument to nest, causing the import to stop at the "
                    "NEST prompt")
from collections import defaultdict
import pyNN.nest.standardmodels
import pyNN.standardmodels
from pyNN.nest import (setup, run, reset, end, get_time_step, get_current_time,
                       get_min_delay, get_max_delay, rank, num_processes,
                       StepCurrentSource, ACSource, DCSource)
from pyNN.common.control import build_state_queries
import pyNN.nest.simulator as simulator
import nest
from nest.hl_api import NESTError
import nineline.pyNN.common
from . import synapses as synapses_module
from pyNN.random import NumpyRNG
from nineline.pyNN.nest.cells import NinePyNNCellMetaClass
from nineline.cells.nest import NineCell

(get_current_time, get_time_step,
 get_min_delay, get_max_delay,
 num_processes, rank) = build_state_queries(simulator)

RELATIVE_BREP_BUILD_DIR = './build'


class Population(nineline.pyNN.common.Population, pyNN.nest.Population):

    _pyNN_standard_celltypes = dict([(cellname,
                                      getattr(pyNN.nest.standardmodels.cells,
                                              cellname))
                                     for cellname in
                                             pyNN.nest.list_standard_models()])
    _NineCellMetaClass = NinePyNNCellMetaClass

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
        super(Population, self).record(variable, to_file)

    def _get_cell_initial_value(self, id, variable):
        """Get the initial value of a state variable of the cell."""
        return super(Population, self)._get_cell_initial_value(
                                            id,
                                            self._translate_variable(variable))

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
        super(Population, self).initialize(**translated_initial_values)


class Projection(nineline.pyNN.common.Projection, pyNN.nest.Projection):

    _synapses_module = synapses_module

    @classmethod
    def get_min_delay(self):
        return get_min_delay()

    @classmethod
    def _convert_units(cls, value_str, units=None):
        if ' ' in value_str:
            if units:
                raise Exception("Units defined in both argument ('{}') and "
                                "value string ('{}')".format(units, value_str))
            (value, units) = value_str.split()
        else:
            value = value_str
            units = None
        try:
            value = float(value)
        except:
            raise Exception("Incorrectly formatted value string '{}', should "
                            "be a number optionally followed by a space and "
                            "units (eg. '1.5 Hz')".format(value_str))

        if not units:
            return value
        elif units == "Hz":
            return value
        elif units == "um":
            return value
        elif units == "ms":
            return value
        elif units == "us":
            return value * 1e-3
        elif units == "us/um":
            return value * 1e-3
        elif units == 'uS':
            return value
        elif units == 'mS':
            return value * 1e+3
        elif units == 'nS':
            return value * 1e-3
        elif units == 'pS':
            return value * 1e-6
        elif units == 'MOhm':
            return value
        elif units == 'Ohm/cm':
            return value
        elif units == 'S/cm2':
            return value
        raise Exception("Unrecognised units '%s'" % units)


class Network(nineline.pyNN.common.Network):

    _PopulationClass = Population
    _ProjectionClass = Projection

    def __init__(self, filename, build_mode='lazy', timestep=None,
                 min_delay=None, max_delay=None, temperature=None,
                 silent_build=False, flags=[], solver_name='cvode', rng=None):
        # Sets the 'get_min_delay' function for use in the network init
        self.get_min_delay = get_min_delay
        self.temperature = None
        nineline.pyNN.common.Network.__init__(self, filename,
                                              build_mode=build_mode,
                                              timestep=timestep,
                                              min_delay=min_delay,
                                              max_delay=max_delay,
                                              temperature=temperature,
                                              silent_build=silent_build,
                                              flags=flags,
                                              solver_name=solver_name, rng=rng)

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


def create_singleton_population(prototype_path, parameters, build_mode='lazy',
                                silent_build=False, solver_name='cvode'):
    pop_9ml = nineline.pyNN.common.populations.create_singleton_9ml(
        prototype_path, parameters)
    pop = Population(pop_9ml, NumpyRNG(), build_mode,
                     silent_build=silent_build,
                     solver_name=solver_name)
    return pop, pop[0]
