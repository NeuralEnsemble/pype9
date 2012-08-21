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
parser.add_argument('--time_start', type=float, default=0.0, help='The start of the plot')
parser.add_argument('--time_stop', type=float, default=100.0, help='The stop of the plot')
parser.add_argument('--time_incr', type=float, default=10.0, help='The time increment of the ticks')
args = parser.parse_args()

length = args.time_stop - args.time_start

variable = args.filename.split('.')[-1]

if variable == 'spikes':
    spikes_n_ids = numpy.loadtxt(args.filename)
    if not spikes_n_ids.shape[0]:
        print "No spikes were generated for selected population"
        sys.exit(0)
    spikes = spikes_n_ids[:, 0]
    ids = spikes_n_ids[:, 1]
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.scatter(spikes, ids)
    ax.set_xlabel("Time (ms)")
#    xticks = range(args.time_start, args.time_stop, args.time_incr)
#    ax.set_xticks(xticks)
#    ax.set_xtick_labels(
    ax.set_ylabel("Neuron #")
    max_id = numpy.max(ids)
    ax.set_xlim(args.time_start - 0.05 * length, args.time_stop + 0.05 * length)
    ax.set_ylim(-2, max_id + 2)
    plt.show()
else:
    raise Exception ("Unrecognised variable '%s'" % variable)
