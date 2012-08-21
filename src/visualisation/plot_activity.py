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
else:
    raise Exception ("Unrecognised variable '%s'" % variable)
