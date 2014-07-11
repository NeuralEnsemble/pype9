"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
import numpy
import pyNN.parameters
from nineline.pyNN.structure import Structure
import nineline.pyNN.random
from pyNN.random import RandomDistribution
from nineml.abstraction_layer.component import BaseComponentClass
import nineml.extensions.biophysical_cells
import nineml.user_layer
import os.path

_pyNN_standard_class_translations = {}


class Population(object):

    def __init__(self, nineml_model, rng, build_mode='lazy',
                 silent_build=False, solver_name='cvode'):
        celltype_model = nineml_model.prototype.definition.component
        celltype_name = (nineml_model.prototype.name
                         if nineml_model.prototype.name else
                         celltype_model.name)
        # Store the definition url inside the cell type for use when checking
        # reloading of cell model
        celltype_model.url = nineml_model.prototype.definition.url
        if isinstance(celltype_model, BaseComponentClass):
            celltype = self._pyNN_standard_celltypes[celltype_model.name]
        elif isinstance(celltype_model,
                        nineml.extensions.biophysical_cells.ComponentClass):
            celltype = self._NineCellMetaClass(celltype_model,
                                               celltype_name,
                                               build_mode=build_mode,
                                               silent=silent_build,
                                               solver_name=solver_name)
        else:
            raise Exception("'{}' component type is not supported yet"
                            .format(type(celltype_model)))
        if build_mode not in ('build_only', 'compile_only'):
            # Set default for populations without morphologies
            self.structures = {}
            for struct_model in nineml_model.structures:
                if struct_model.name:
                    struct_name = struct_model.name
                else:
                    struct_name = 'structure_' + len(self.structures)
                self.structures[struct_name] = Structure(struct_name,
                                                         nineml_model.number,
                                                         struct_model, rng)
            cellparams = {}
            initial_values = {}
            for param_definition in nineml_model.prototype.definition.\
                                                          component.parameters:
                p = nineml_model.prototype.parameters[param_definition.name]
                if isinstance(p.value, float):
                    param = p.value
                elif isinstance(p.value, nineml.user_layer.RandomDistribution):
                    RandomDistributionClass = getattr(nineline.pyNN.random,
                                                      p.value.definition.\
                                                                component.name)
                    param = RandomDistributionClass(
                        p.value.parameters, rng, use_units=False)
                elif isinstance(p.value, nineml.user_layer.Sequence):
                    param = pyNN.parameters.Sequence(p.value)
                else:
                    raise Exception("Unrecognised parameter type '{}'"
                                    .format(type(p.value)))
                if (hasattr(param_definition, 'type') and
                    param_definition.type == 'initialState'):
                    initial_values[p.name] = param
                else:
                    cellparams[p.name] = param
            # Sorry if this feels a bit hacky (i.e. relying on the pyNN class
            # being the third class in the MRO), I thought of a few ways to do
            # this but none were completely satisfactory.
            PyNNClass = self.__class__.__mro__[2]
            assert PyNNClass.__module__.startswith(
                'pyNN') and PyNNClass.__name__ == 'Population'
            PyNNClass.__init__(self, nineml_model.number, celltype,
                               cellparams=cellparams,
                               initial_values=initial_values, structure=None,
                               label=nineml_model.name)

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

    def _set_positions(self, positions, morphologies=None):
        super(Population, self)._set_positions(positions)
        self.morphologies = morphologies


def create_singleton_9ml(prototype_path, parameters):
    """
    Create a singleton population model given a path to a SpikingNode prototype
    """

    layout_def = os.path.join(os.path.dirname(prototype_path), '..',
                              'nineml_catalog',
                              'networkstructures', 'line.xml')
    layout_params = {'dx': (1, 'dimensionless'), 'x0': (0, 'dimensionless'),
                     'y': (0, 'dimensionless'),
                     'z': (0, 'dimensionless')}
    structlist = nineml.user_layer.StructureList(
                        [nineml.user_layer.Structure('none',
                                nineml.user_layer.Layout('line',
                                        definition=layout_def,
                                        parameters=layout_params), None)])
    definition = nineml.user_layer.Definition(prototype_path, '')
    prototype_name = next(
        nineml.extensions.biophysical_cells.parse(prototype_path).iterkeys())
    prototype = nineml.user_layer.SpikingNodeType(
        prototype_name, definition, parameters)
    return nineml.user_layer.Population('Singleton', 1, prototype, structlist)