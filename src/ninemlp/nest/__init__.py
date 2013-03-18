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
        pyNN.nest.Population.initialize(self, self._translate_param_name(param, component,
                                                                         seg_group),
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

    def __init__(self, pre, dest, label, connector, source=None, target=None, build_mode=DEFAULT_BUILD_MODE):
        self.label = label
        if build_mode == 'build_only':
            print "Warning! '--build' option was set to 'build_only', meaning the projection '%s' was not constructed." % label
        else:
            pyNN.nest.Projection.__init__(self, pre, dest, connector, label=label, source=source,
                                                                                      target=target)

#    def _divergent_connect(self, source, targets, weights, delays):
#        """
#        Connect a neuron to one or more other neurons.
#        
#        `source`  -- the ID of the pre-synaptic cell.
#        `targets` -- a list/1D array of post-synaptic cell IDs, or a single ID.
#        `weight`  -- a list/1D array of connection weights, or a single weight.
#                     Must have the same length as `targets`.
#        `delays`  -- a list/1D array of connection delays, or a single delay.
#                     Must have the same length as `targets`.
#        """
#        # are we sure the targets are all on the current node?
#        if pyNN.core.is_listlike(source):
#            assert len(source) == 1
#            source = source[0]
#        if not pyNN.core.is_listlike(targets):
#            targets = [targets]
#        assert len(targets) > 0
#
#        if self.synapse_type not in targets[0].celltype.synapse_types:
#            raise pyNN.errors.ConnectionError("User gave synapse_type=%s, synapse_type must be one "
#                    "of: {}".format(self.synapse_type, "'" + 
#                    "', '".join(st for st in targets[0].celltype.synapse_types or
#                                ['*No connections supported*'])) + "'")
#        # Weights should be in nA or uS, but iaf_neuron uses pA and iaf_cond_neuron uses nS.
#        # Using convention in this way is not ideal. We should
#        # be able to look up the units used by each model somewhere.            
#        weights = numpy.array(weights) * 1000.0 
#        if self.synapse_type == 'inhibitory' and pyNN.common.is_conductance(targets[0]):
#            weights *= -1 # NEST wants negative values for inhibitory weights, even if these are conductances
#        if isinstance(weights, numpy.ndarray):
#            weights = weights.tolist()
#        elif isinstance(weights, float):
#            weights = [weights]
#        if isinstance(delays, numpy.ndarray):
#            delays = delays.tolist()
#        elif isinstance(delays, float):
#            delays = [delays]
#
#        if targets[0].celltype.standard_receptor_type:
#            try:
#                nest.DivergentConnect([source], targets, weights, delays, self.synapse_model)
#            except NESTError, e:
#                raise pyNN.errors.ConnectionError("%s. source=%s, targets=%s, weights=%s, delays=%s, "
#                                             "synapse model='%s'" % (e, source, targets, weights,
#                                                                     delays, self.synapse_model))
#        else:
#            for target, w, d in zip(targets, weights, delays):
#                nest.Connect([source], [target], {'weight': w, 'delay': d,
#                                                       'receptor_type': target.celltype.get_receptor_type(self.synapse_type)})
#        self._connections = None # reset the caching of the connection list, since this will have to be recalculated
#        self._sources.append(source)
#
#
#        def _convergent_connect(self, sources, target, weights, delays):
#            """
#            Connect one or more neurons to a single post-synaptic neuron.
#            `sources` -- a list/1D array of pre-synaptic cell IDs, or a single ID.
#            `target`  -- the ID of the post-synaptic cell.
#            `weight`  -- a list/1D array of connection weights, or a single weight.
#                         Must have the same length as `targets`.
#            `delays`  -- a list/1D array of connection delays, or a single delay.
#                         Must have the same length as `targets`.
#            """
#        # are we sure the targets are all on the current node?
#        if pyNN.core.is_listlike(target):
#            assert len(target) == 1
#            target = target[0]
#        if not pyNN.core.is_listlike(sources):
#            sources = [sources]
#        assert len(sources) > 0, sources
#        if self.synapse_type not in ('excitatory', 'inhibitory', None):
#            raise errors.ConnectionError("synapse_type must be 'excitatory', 'inhibitory', or None (equivalent to 'excitatory')")
#        weights = numpy.array(weights)*1000.0# weights should be in nA or uS, but iaf_neuron uses pA and iaf_cond_neuron uses nS.
#                                 # Using convention in this way is not ideal. We should
#                                 # be able to look up the units used by each model somewhere.
#        if self.synapse_type == 'inhibitory' and common.is_conductance(target):
#            weights = -1*weights # NEST wants negative values for inhibitory weights, even if these are conductances
#        if isinstance(weights, numpy.ndarray):
#            weights = weights.tolist()
#        elif isinstance(weights, float):
#            weights = [weights]
#        if isinstance(delays, numpy.ndarray):
#            delays = delays.tolist()
#        elif isinstance(delays, float):
#            delays = [delays]
#               
#        try:
#            nest.ConvergentConnect(sources, [target], weights, delays, self.synapse_model)            
#        except nest.NESTError, e:
#            raise errors.ConnectionError("%s. sources=%s, target=%s, weights=%s, delays=%s, synapse model='%s'" % (
#                                         e, sources, target, weights, delays, self.synapse_model))
#        self._connections = None # reset the caching of the connection list, since this will have to be recalculated
#        self._sources.extend(sources)            

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

