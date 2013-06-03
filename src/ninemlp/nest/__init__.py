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
import pyNN.core
import pyNN.errors
import pyNN.common
import ninemlp.common
import ninemlp.common.brep
import ncml
from ninemlp import DEFAULT_BUILD_MODE
from pyNN.nest import setup, run, reset, end, get_time_step, get_current_time, get_min_delay, \
                        get_max_delay, rank, num_processes, StepCurrentSource, ACSource, DCSource, \
                        NoisyCurrentSource
from pyNN.common.control import build_state_queries
import pyNN.nest.simulator
import nest
from nest.hl_api import NESTError

get_current_time, get_time_step, get_min_delay, get_max_delay, num_processes, rank = build_state_queries(pyNN.nest.simulator)

RELATIVE_BREP_BUILD_DIR = './build'

def build_pyNN(build_mode=DEFAULT_BUILD_MODE, silent=True):
    pass # Not required as of yet (this is needed for the neuron module though

class Population(ninemlp.common.Population, pyNN.nest.Population):

    def __init__(self, label, size, cell_type, params={}, build_mode=DEFAULT_BUILD_MODE):
        """
        Initialises the population after reading the population parameters from file
        """
        if build_mode == 'build_only':
            print "Warning! '--build' option was set to 'build_only', meaning the population '%s' was not constructed and only the NMODL files were compiled."
        else:
            pyNN.nest.Population.__init__(self, size, cell_type,
                                          params, structure=None, label=label)

    def set_param(self, cell_id, param, value, component=None, section=None):
        raise NotImplementedError('set_param has not been implemented for Population class yet')

    def rset(self, param, rand_distr, component=None, seg_group=None):
        pyNN.nest.Population.rset(self, self._translate_param_name(param, component, seg_group),
                                  rand_distr)

    def initialize(self, param, rand_distr, component=None, seg_group=None):
        pyNN.nest.Population.initialize(self, self._translate_param_name(param, component, seg_group),
                                        rand_distr)

    def _translate_param_name(self, param, component, seg_group):
        if seg_group and seg_group != 'source_section' and seg_group != 'soma':
            raise NotImplementedError("Segment groups are not currently supported for NEST")
        if component:
            try:
                translation = self.get_cell_type().component_parameters
            except AttributeError:
                raise Exception("Attempting to set component or segment group parameter on non-"
                                "ninemlp cell type")
            try:
                comp_translation = translation[component]
            except KeyError:
                raise Exception("Cell type '{}' does not have a component '{}'"
                                .format(self.get_cell_type().name, component))
            try:
                param = comp_translation[param][0]
            except KeyError:
                raise Exception("Component '{}' does not have a parameter '{}'"
                                .format(component, param))
        return param

class Projection(pyNN.nest.Projection):

    def __init__(self, pre, dest, label, connector, source=None, target=None, 
                 build_mode=DEFAULT_BUILD_MODE, rng=None):
        self.label = label
        if build_mode == 'build_only':
            print "Warning! '--build' option was set to 'build_only', meaning the projection '%s' was not constructed." % label
        else:
            pyNN.nest.Projection.__init__(self, pre, dest, connector, label=label, source=source,
                                          target=target, rng=rng)
            

class Network(ninemlp.common.Network):

    def __init__(self, filename, build_mode=DEFAULT_BUILD_MODE, timestep=None,
                 min_delay=None, max_delay=None, temperature=None, silent_build=False, flags=[],
                 solver_name='cvode', rng=None):
        self._pyNN_module = pyNN.nest
        self._ncml_module = ncml
        self._Population_class = Population
        self._Projection_class = Projection
        self._GapJunctionProjection_class = None
        self.get_min_delay = get_min_delay # Sets the 'get_min_delay' function for use in the network init
        self.temperature = None
        ninemlp.common.Network.__init__(self, filename, build_mode=build_mode,
                                        timestep=timestep, min_delay=min_delay, max_delay=max_delay,
                                    temperature=temperature, silent_build=silent_build, flags=flags,
                                    solver_name=solver_name, rng=rng)

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

