"""
Contains a method for plotting spike trains for debugging (could be moved somewhere else if appropriate)

@author Tom Close

"""

#######################################################################################
#
#    Copyright 2011 Okinawa Institute of Science and Technology (OIST), Okinawa, Japan
#
#######################################################################################

import numpy as np
try:
  import matplotlib.pyplot as plt
except:
  pass

def plot_spikes(spike_trains, dt=10, min_time= -1, max_time= -1, num_ticks=10):
  """
  Plots a series of spikes over several sources in a image
  
  @param spike_trains [list(np.array)]: List of spike trains in numpy arrays
  @param dt [float]: time interval to discretise the time period
  @param min_time [float]: Start time of the plot
  @param max_time [float]: End time of the plot
  @num_ticks [int]: Number of ticks to place on the plot
  """

  for spike_train in spike_trains:
    spike_train.sort()

  if min_time < 0:
    min_time = float('inf')
    for spike_train in spike_trains:
      if len(spike_train) and spike_train[0] < min_time:
          min_time = spike_train[0]

  if max_time < 0:
    max_time = 0
    for spike_train in spike_trains:
      if len(spike_train) and spike_train[-1] > max_time:
        max_time = spike_train[-1]

  time_range = max_time - min_time

  num_bins = int(round((max_time - min_time) / dt)) + 1

  img = np.zeros((len(spike_trains), num_bins))

  train_i = 0
  for spike_train in spike_trains:
    for spike in spike_train:
      bin_index = int(round((spike - min_time) / dt))
      if bin_index > 0 and bin_index < num_bins:
        img[train_i, bin_index] = 1.0

    train_i = train_i + 1

  plt.imshow(img, interpolation='nearest', cmap=plt.cm.gray) #@UndefinedVariable 
  plt.xlabel("Time (ms)")
  plt.ylabel('Input sources')
  plt.xticks(np.arange(0, num_bins + 1, num_bins / num_ticks))
  time_incr = time_range / num_ticks
  plt.gca().set_xticklabels([int(round(x)) for x in np.arange(min_time, max_time + time_incr, time_incr)])
  plt.show()

if __name__ == '__main__':

  print "doing nothing"




