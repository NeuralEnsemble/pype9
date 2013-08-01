

class Population(object):

    def __init__(self):
        self.morphologies = None

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
        if self.get_cell_type().__name__ != 'SpikeSourceArray':
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
                                           math.exp(-estimated_num_spikes / 10.0) * 10.0)
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
        if self.get_cell_type().__name__ != 'SpikeSourceArray':
            raise Exception("'set_poisson_spikes' method can only be used for 'SpikeSourceArray' " 
                            "populations.")
        self.tset('spike_times', spike_times)
        
    def set_spatially_dependent_spikes(self):
        pass 

    def get_cell_type(self):
        """
        Returns the cell type of the population
        """
        return type(self.celltype)

    def _set_positions(self, positions, morphologies=None):
        super(Population, self)._set_positions(positions)
        self.morphologies = morphologies