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

import os.path
import argparse
import numpy
import matplotlib.pyplot as plt
import NeuroTools.signals as sig #@UnresolvedImport

PROJECT_PATH = os.path.normpath(os.path.join(os.path.realpath(__file__), '..', '..', '..'))
ACTIVITY_PATH = os.path.join(PROJECT_PATH, 'activity')

parser = argparse.ArgumentParser(description='A script to ')
parser.add_argument('cell', help='The name of the cell to plot.')
parser.add_argument('run', help='Name of the run to load the data from')
parser.add_argument('variable', default='spikes', help='The name of variable to plot.')
parser.add_argument('--time_start', type=float, default=0.0, help='The start of the plot')
parser.add_argument('--time_stop', type=float, default=100.0, help='The stop of the plot')
args = parser.parse_args()

length = args.time_stop - args.time_start

if args.variable == 'spikes':
    filename = os.path.join(ACTIVITY_PATH, args.run, 'fabios_network.out.' + args.cell + '.' + args.variable)
    spikes_n_ids = numpy.loadtxt(filename)
    spikes = spikes_n_ids[:, 0]
    ids = spikes_n_ids[:, 1]
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.scatter(spikes, ids)
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Neuron #")
    max_id = numpy.max(ids)
    ax.set_xlim(args.time_start - 0.05 * length, args.time_stop + 0.05 * length)
    ax.set_ylim(-2, max_id + 2)

    plt.show()
else:
    raise Exception ("Unrecognised variable '%s'" % args.variable)
