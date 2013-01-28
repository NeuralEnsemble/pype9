"""

  This package mirrors the one in pyNN

  @file __init__.py
  @author Tom Close

"""

#######################################################################################
#
#    Copyright 2012 Okinawa Institute of Science and Technology (OIST), Okinawa, Japan
#
#######################################################################################

import os
import numpy
import sys
# Remove any system arguments that may conflict with
if '--debug' in sys.argv:
    raise Exception("'--debug' argument passed to script conflicts with an argument to nest, "
                    "causing the import to stop at the NEST prompt")
import pyNN.nest.standardmodels.cells
import pyNN.nest.connectors
import ninemlp.common.brep
import ncml
from ninemlp import DEFAULT_BUILD_MODE
from pyNN.nest import setup, run, reset, end, get_time_step, get_current_time, get_min_delay, \
                        get_max_delay, rank, num_processes, StepCurrentSource, ACSource, DCSource, \
                        NoisyCurrentSource
from pyNN.common.control import build_state_queries
import pyNN.nest.simulator
from nest.hl_api import NESTError

get_current_time, get_time_step, get_min_delay, get_max_delay, num_processes, rank = build_state_queries(pyNN.nest.simulator)

RELATIVE_BREP_BUILD_DIR = './build'

def build_pyNN(build_mode=DEFAULT_BUILD_MODE, silent=True):
    pass # Not required as of yet (this is needed for the neuron module though

class Population(pyNN.nest.Population):

    def __init__(self, label, size, cell_type, params={}, build_mode=DEFAULT_BUILD_MODE):
        """
        Initialises the population after reading the population parameters from file
        """
        if build_mode == 'build_only':
            print "Warning! '--compile' option was set to 'build_only', meaning the population '%s' was not constructed and only the NMODL files were compiled."
        else:
            pyNN.nest.Population.__init__(self, size, cell_type,
                                                  params, structure=None, label=label)

    def set_param(self, cell_id, param, value, component=None, section=None):
        raise NotImplementedError('set_param has not been implemented for Population class yet')


class Projection(pyNN.nest.Projection):

    def __init__(self, pre, dest, label, connector, source=None, target=None, build_mode=DEFAULT_BUILD_MODE):
        self.label = label
        if build_mode == 'build_only':
            print "Warning! '--compile' option was set to 'build_only', meaning the projection '%s' was not constructed." % label
        else:
            pyNN.nest.Projection.__init__(self, pre, dest, connector, label=label, source=source,
                                                                                      target=target)

class Network(ninemlp.common.Network):

    def __init__(self, filename, build_mode=DEFAULT_BUILD_MODE, timestep=None,
                 min_delay=None, max_delay=None, temperature=None, silent_build=False, flags=[]):
        self._pyNN_module = pyNN.nest
        self._ncml_module = ncml
        self._Population_class = Population
        self._Projection_class = Projection
        self._ElectricalSynapseProjection_class = None
        self.get_min_delay = get_min_delay # Sets the 'get_min_delay' function for use in the network init
        self.temperature = None
        ninemlp.common.Network.__init__(self, filename, build_mode=build_mode,
                                        timestep=timestep, min_delay=min_delay, max_delay=max_delay,
                                    temperature=temperature, silent_build=silent_build, flags=flags)

    def _get_target_str(self, synapse, segment=None):
        return synapse

    def _convert_units(self, value_str, units=None):
        if ' ' in value_str:
            if units:
                raise Exception("Units defined in both argument ('%s') and value string ('%s')" % (units, value_str))
            (value, units) = value_str.split()
        else:
            value = value_str
            units = None
        try:
            value = float(value)
        except:
            raise Exception("Incorrectly formatted value string '%s', should be a number optionally followed by a space and units (eg. '1.5 Hz')" % value_str)

        raise Exception("Unrecognised units '%s'" % units)

    def _set_simulation_params(self, **params):
        """
        Sets the simulation parameters either from the passed parameters or from the networkML
        description
        
        @param params[**kwargs]: Parameters that are either passed to the pyNN setup method or set explicitly
        """
        p = self._get_simulation_params(**params)
        try:
            setup(p['timestep'], p['min_delay'], p['max_delay'])
        except NESTError as e:
            raise Exception("There was an error setting the min_delay of the simulation, \
try changing the values for timestep ({time}) and min_delay ({delay}). (Message - {e})".format(
                                                                              time=p['timestep'],
                                                                              delay=p['min_delay'],
                                                                              e=e))
        self.temperature = p['temperature']

if __name__ == "__main__":
    print "loaded"

