import os.path
import numpy
import pyNN.parameters
import nineline.pyNN.structure
from pyNN.random import RandomDistribution


class Population(object):            

    @classmethod
    def factory(cls, nineml_model, dirname, pop_dir, rng, verbose=False, 
                build_mode='lazy', silent_build=False, solver_name='cvode'):
        
        # This is a temporary hack until the cell models are fully converted to the 9ml format
        if nineml_model.prototype.definition:
            celltype_name = os.path.splitext(os.path.basename(nineml_model.prototype.definition.url))[0]
            if '_' in celltype_name:
                name_parts = celltype_name.split('_')
                for i, p in enumerate(name_parts):
                    name_parts[i] = p.capitalize()
                celltype_name = ''.join(name_parts)
            
            celltype = cls._pyNN_standard_celltypes[celltype_name]
        else:
            celltype_name = nineml_model.prototype.name
            try:
                celltype = cls._NineCellMetaClass(
                                        celltype_name,
                                        os.path.join(dirname, '..', 'neurons', celltype_name + '.xml'), 
                                        morph_id=None,
                                        build_mode=build_mode,
                                        silent=silent_build,
                                        solver_name=solver_name)
            except IOError:
                raise Exception("Cell_type_name '{}' was not found or in standard models"
                                .format(celltype_name))
        if build_mode not in ('build_only', 'compile_only'):
            # Set default for populations without morphologies
            structure = nineml_model.positions.structure
            if structure:
                StructureClass = getattr(nineline.pyNN.structure, 
                                         structure.definition.component.name)
                structure = StructureClass(structure.parameters, rng)
            pop = cls(nineml_model.number, celltype, cellparams={}, structure=structure, 
                      label=nineml_model.name)
            return pop
        
    def _randomly_distribute_params(self, cell_param_distrs, rng):
        # Set distributed parameters
        distributed_params = []
        for param, distr_type, units, seg_group, component, args in cell_param_distrs: #@UnusedVariable: Can't work out how to use units effectively at the moment because args may include parameters that don't have units, so ignoring it for now but will hopefully come back to it
            if param in distributed_params:
                raise Exception("Parameter '{}' has two (or more) distributions specified for it " 
                                "in {} population".format(param, self.id))
            # Create random distribution object
            rand_distr = RandomDistribution(distribution=distr_type, parameters=args, rng=rng)
            self.rset(param, rand_distr, component=component, seg_group=seg_group)
            # Add param to list of completed param distributions to check for duplicates
            distributed_params.append(param)

    def _randomly_distribute_initial_conditions(self, initial_conditions, rng):
        # Set distributed parameters
        distributed_conditions = []
        for variable, distr_type, units, seg_group, component, args in initial_conditions: #@UnusedVariable: Can't work out how to use units effectively at the moment because args may include variables that don't have units, so ignoring it for now but will hopefully come back to it
            if variable in distributed_conditions:
                raise Exception("Parameter '{}' has two (or more) distributions specified for it " 
                                "in {} population".format(variable, self.id))
            # Create random distribution object
            rand_distr = RandomDistribution(distribution=distr_type, parameters=args, rng=rng)
            self.initialize_variable(variable, rand_distr, component=component, seg_group=seg_group)
            # Add variable to list of completed variable distributions to check for duplicates
            distributed_conditions.append(variable)

    def set_poisson_spikes(self, rate, start_time, end_time, rng):
        """
        Sets up a train of poisson spike times for a SpikeSourceArray population
        
        @param rate: Rate of the poisson spike train (Hz)
        @param start_time: Start time of the stimulation (ms)
        @param end_time: The end time of the stimulation (ms)
        @param rng: A numpy random state
        """
        if self.get_celltype().__name__ != 'SpikeSourceArray':
            raise Exception("'set_poisson_spikes' method can only be used for 'SpikeSourceArray' " 
                            "populations.")
        # If rate is set to zero do nothing
        if rate:
            mean_interval = 1000.0 / rate
            stim_range = end_time - start_time
            if stim_range >= 0.0:
                estimated_num_spikes = stim_range / mean_interval
                # Add extra spikes to make sure spike train doesn't stop short
                estimated_num_spikes = int(estimated_num_spikes + 
                                           numpy.exp(-estimated_num_spikes / 10.0) * 10.0)
                spike_intervals = rng.exponential(mean_interval,
                                                           size=(self.size, estimated_num_spikes))
                spike_times = numpy.cumsum(spike_intervals, axis=1) + start_time
                # FIXME: Should ensure that spike times don't exceed 'end_time' and make it at least until then.
                self.set(spike_times=[pyNN.parameters.Sequence(train) for train in spike_times])
            else:
                print ("Warning, stimulation start time ({}) is after stimulation end time ({})"
                      .format(start_time, end_time))

    def set_spikes(self, spike_times):
        """
        Sets up a train of poisson spike times for a SpikeSourceArray population
        
        @param rate: Rate of the poisson spike train
        @param start_time: Start time of the stimulation
        @param end_time: The end time of the stimulation.
        """
        if self.get_celltype().__name__ != 'SpikeSourceArray':
            raise Exception("'set_poisson_spikes' method can only be used for 'SpikeSourceArray' " 
                            "populations.")
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