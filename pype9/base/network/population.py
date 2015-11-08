"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
import numpy
from itertools import chain
from nineml.user import DynamicsArray, Initial
from pyNN.random import RandomDistribution
import pyNN.parameters
from pype9.exceptions import Pype9RuntimeError
from .values import nineml_qty_to_pyNN_value

_pyNN_standard_class_translations = {}


class Population(object):

    def __init__(self, dynamics_array, rng, build_mode='lazy', **kwargs):
        if not isinstance(dynamics_array, DynamicsArray):
            raise Pype9RuntimeError(
                "Expected a dynamics array, found {}".format(dynamics_array))
        # Store the definition url inside the cell type for use when checking
        # reloading of cell model
        dynamics = dynamics_array.dynamics
        celltype = self._PyNNCellWrapperMetaClass(
            dynamics, dynamics_array.name, build_mode=build_mode, **kwargs)
        if build_mode not in ('build_only', 'compile_only'):
            # Set default for populations without morphologies
            cellparams = {}
            initial_values = {}
            for prop in chain(dynamics.properties, dynamics.initial_values):
                val = nineml_qty_to_pyNN_value(prop, self._unit_handler, rng)
                if isinstance(prop, Initial):
                    initial_values[prop.name] = val
                else:
                    cellparams[prop.name] = val
            # Sorry if this feels a bit hacky (i.e. relying on the pyNN class
            # being the third class in the MRO), I thought of a few ways to do
            # this but none were completely satisfactory.
            PyNNClass = self.__class__.__mro__[2]
            assert PyNNClass.__module__.startswith(
                'pyNN') and PyNNClass.__name__ == 'Population'
            PyNNClass.__init__(self, dynamics_array.size, celltype,
                               cellparams=cellparams,
                               initial_values=initial_values, structure=None,
                               label=dynamics_array.name)

    @property
    def positions(self):
        try:
            return self.structures['soma'].positions
        except KeyError:
            return next(self.structures.itervalues()).positions.T

    def _randomly_distribute_params(self, cell_param_distrs, rng):
        # Set distributed parameters
        distributed_params = []
        # Can't work out how to use units effectively at the
        # moment because args may include parameters that don't have units, so
        # ignoring it for now but will hopefully come back to it
        for (param, distr_type, units,  # @UnusedVariable
             seg_group, component, args) in cell_param_distrs:
            if param in distributed_params:
                raise Exception("Parameter '{}' has two (or more) "
                                "distributions specified for it "
                                "in {} population".format(param, self.id))
            # Create random distribution object
            rand_distr = RandomDistribution(
                distribution=distr_type, parameters=args, rng=rng)
            self.rset(
                param, rand_distr, component=component, seg_group=seg_group)
            # Add param to list of completed param distributions to check for
            # duplicates
            distributed_params.append(param)

    def _randomly_distribute_initial_conditions(self, initial_conditions, rng):
        # Set distributed parameters
        distributed_conditions = []
        # Can't work out how to use units effectively at the moment because
        # args may include variables that don't have units, so ignoring it for
        # now but will hopefully come back to it
        for (variable, distr_type, units,  # @UnusedVariable
             seg_group, component, args) in initial_conditions:
            if variable in distributed_conditions:
                raise Exception("Parameter '{}' has two (or more) "
                                "distributions specified for it "
                                "in {} population".format(variable, self.id))
            # Create random distribution object
            rand_distr = RandomDistribution(
                distribution=distr_type, parameters=args, rng=rng)
            self.initialize_variable(
                variable, rand_distr, component=component, seg_group=seg_group)
            # Add variable to list of completed variable distributions to check
            # for duplicates
            distributed_conditions.append(variable)

    def set_poisson_spikes(self, rate, start_time, end_time, rng):
        """
        Sets up a train of poisson spike times for a SpikeSourceArray
        population

        @param rate: Rate of the poisson spike train (Hz)
        @param start_time: Start time of the stimulation (ms)
        @param end_time: The end time of the stimulation (ms)
        @param rng: A numpy random state
        """
        if self.get_celltype().__name__ != 'SpikeSourceArray':
            raise Exception("'set_poisson_spikes' method can only be used for "
                            "'SpikeSourceArray' populations.")
        # If rate is set to zero do nothing
        if rate:
            mean_interval = 1000.0 / rate
            stim_range = end_time - start_time
            if stim_range >= 0.0:
                estimated_num_spikes = stim_range / mean_interval
                # Add extra spikes to make sure spike train doesn't stop short
                estimated_num_spikes = int(estimated_num_spikes +
                                           numpy.exp(-estimated_num_spikes
                                                     / 10.0) * 10.0)
                spike_intervals = rng.exponential(mean_interval,
                                                  size=(self.size,
                                                        estimated_num_spikes))
                spike_times = numpy.cumsum(
                    spike_intervals, axis=1) + start_time
                self.set(
                    spike_times=[pyNN.parameters.Sequence(train)
                                 for train in spike_times])
            else:
                print ("Warning, stimulation start time ({}) is after "
                       "stimulation end time ({})"
                       .format(start_time, end_time))

    def set_spikes(self, spike_times):
        """
        Sets up a train of poisson spike times for a SpikeSourceArray
        population

        @param rate: Rate of the poisson spike train
        @param start_time: Start time of the stimulation
        @param end_time: The end time of the stimulation.
        """
        if self.get_celltype().__name__ != 'SpikeSourceArray':
            raise Exception("'set_poisson_spikes' method can only be used for "
                            "'SpikeSourceArray' populations.")
        self.tset('spike_times', spike_times)

    def set_spatially_dependent_spikes(self):
        pass

    def get_celltype(self):
        """
        Returns the cell type of the population
        """
        return type(self.celltype)
