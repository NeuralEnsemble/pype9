#!/usr/bin/env python
"""
Contains a method for plotting cell positions loaded from BRep export files

@author Tom Close

"""

#######################################################################################
#
#    Copyright 2011 Okinawa Institute of Science and Technology (OIST), Okinawa, Japan
#
#######################################################################################

import sys
import os.path
import argparse
import numpy
import matplotlib.pyplot as plt

PROJECT_PATH = os.path.normpath(os.path.join(os.path.realpath(__file__), '..', '..', '..'))
ACTIVITY_PATH = os.path.join(PROJECT_PATH, 'activity')

parser = argparse.ArgumentParser(description='A script to plot spike activity')
parser.add_argument('filename', help='The file to plot the spikes from')
parser.add_argument('--time_start', type=float, default=None, help='The start of the plot')
parser.add_argument('--time_stop', type=float, default=None, help='The stop of the plot')
parser.add_argument('--v_incr', type=float, default=0.1, help='The minimum increment required before the next step in the voltage trace is plotted')
args = parser.parse_args()


variable = args.filename.split('.')[-1]

if variable == 'spikes':
    # Load spikes
    spikes_n_ids = numpy.loadtxt(args.filename)
    if not spikes_n_ids.shape[0]:
        print "No spikes were generated for selected population"
        sys.exit(0)
    spikes = spikes_n_ids[:, 0]
    ids = spikes_n_ids[:, 1]
    if args.time_start:
        time_start = args.time_start
    else:
        time_start = spikes.min()
    if args.time_stop:
        time_stop = args.time_stop
    else:
        time_stop = spikes.max()
    length = time_stop - time_start
    # Plot spikes
    # Plot spikes
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.scatter(spikes, ids)
    # Set axis labels and limits
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Neuron #")
    max_id = numpy.max(ids)
    ax.set_xlim(time_start - 0.05 * length, time_stop + 0.05 * length)
    ax.set_ylim(-2, max_id + 2)
    # Show the spikes
    plt.show()
elif variable == 'v':
    v_trace = numpy.loadtxt(args.filename)
    if not v_trace.shape[0]:
        print "No trace was loaded from file"
        sys.exit(0)
    v = v_trace[:,0]
    ids = numpy.unique(v_trace[:,1])
    num_ids = len(ids)
    num_times = v.shape[0] / num_ids
    if not num_times:
        print "No times loaded from voltage trace file"
        sys.exit(0)
    voltages = numpy.reshape(v, (num_times, num_ids))
    times = numpy.arange(0, num_times)
    for ID in ids:
        indices_to_plot = [0]
        prev_v = voltages[0, ID]
        for i, v in enumerate(voltages[1:, ID]):
            if abs(v - prev_v) > args.v_incr:
                indices_to_plot.append(i)
                prev_v = v
        voltages_to_plot = voltages[indices_to_plot, ID]
        times_to_plot = times[indices_to_plot]
        plt.plot(times_to_plot, voltages_to_plot)
    plt.show()
else:
    raise Exception ("Unrecognised variable '%s'" % variable)
