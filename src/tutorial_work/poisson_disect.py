'''
Created on Feb 7, 2013

@author: Lisicovas
'''
#===============================================================================
# def set_poisson_spikes(self, rate, start_time, end_time):
#       """
#       Sets up a train of poisson spike times for a SpikeSourceArray population
#       
#       @param rate: Rate of the poisson spike train (Hz)
#       @param start_time: Start time of the stimulation (ms)
#       @param end_time: The end time of the stimulation (ms)
#       """
#       if self.get_cell_type().__name__ != 'SpikeSourceArray':
#           raise Exception("'set_poisson_spikes' method can only be used for 'SpikeSourceArray' " \
#                           "populations.")
#       mean_interval = 1000 / rate # Convert from Hz to ms
#       stim_range = end_time - start_time
#       if stim_range >= 0.0:
#           estimated_num_spikes = stim_range / mean_interval
#           # Add extra spikes to make sure spike train doesn't stop short
#           estimated_num_spikes = int(estimated_num_spikes + \
#                                      math.exp(-estimated_num_spikes / 10.0) * 10.0)
#           spike_intervals = numpy.random.exponential(mean_interval,
#                                                      size=(self.size, estimated_num_spikes))
#           spike_times = numpy.cumsum(spike_intervals, axis=1) + start_time
#           # FIXME: Should ensure that spike times don't exceed 'end_time' and make it at least until then.
#           self.tset('spike_times', spike_times)
#       else:
#           print "Warning, stimulation start time ({}) is after stimulation end time ({})".\
#                   format(start_time, end_time)
#                   
# 
# 
# granules = net.get_population("Granules") #selecting the granule cells
#   nmda_input = net.get_population("NMDAInput") #population of the nmda synapses?
#   nmda_input.set_poisson_spikes(args.input_rate, args.start_input, args.time)
#===============================================================================

#Experimenting with the output

import numpy
import math

class MyClass:
    
    def __init__(self, size):
        
        self.size = size
        
    def function(self):
        print self.size+ 12  
    
    def set_poisson_spikes(self, rate, start_time, end_time):
        mean_interval = 1000 / rate # Convert from Hz to ms
        stim_range = end_time - start_time
        if stim_range >= 0.0:
            estimated_num_spikes = stim_range / mean_interval
            # Add extra spikes to make sure spike train doesn't stop short
            estimated_num_spikes = int(estimated_num_spikes + \
                                          math.exp(-estimated_num_spikes / 10.0) * 10.0)
            spike_intervals = numpy.random.exponential(mean_interval,
                                                          size=(self.size, estimated_num_spikes))
            spike_times = numpy.cumsum(spike_intervals, axis=1) + start_time
            # FIXME: Should ensure that spike times don't exceed 'end_time' and make it at least until then.
            self.tset('spike_times', spike_times)
        else:
            print "Warning, stimulation start time ({}) is after stimulation end time ({})".\
                       format(start_time, end_time)
        array = []                  
        test_array = set_poisson_spikes(array,10,1,100)
        print test_array
        
if __name__ == '__main__':
    object = MyClass(10)
    object.size()