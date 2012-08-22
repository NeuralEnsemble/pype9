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
parser.add_argument('--label', type=str, default='', help='Additional label information')
args = parser.parse_args()

file_header = {}
f = open(args.filename)
for line in f:
    if line[0] != '#': # Check to see if the line is a comment
        break
    split_line = line.split()
    key = split_line[1]
    value = split_line[3]
    # Try to convert to numeric value
    try:
        value = float(value)
    except ValueError:
        try:
            value = int(value)
        except ValueError:
            pass
    file_header[key] = value   

if not file_header:
    raise Exception("Did not load a header from the passed file '%s', is it a pyNN output file?" % args.filename)

if not file_header.has_key('label'):
    raise Exception("Required header field 'label' was not found in file header.")

# Get the type of variable recorded via the file's extension
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
    plt.title(file_header['label'] + ' ' + args.label + '- Spike Times')
    max_id = numpy.max(ids)
    ax.set_xlim(time_start - 0.05 * length, time_stop + 0.05 * length)
    ax.set_ylim(-2, max_id + 2)
    # Show the spikes
    plt.show()
elif variable == 'v':
    if not file_header.has_key('dt'):
        raise Exception("Required header field 'dt' was not found in file header.")
    f = open(args.filename)
    prev_ID = None
    voltages = []
    times = []
    IDs = []
    for line in f:
        if line[0] != '#': # Check to see if the line is a comment
            v, ID = line[:-1].split()
            v = float(v)
            # If the ID signifies the start of a new cell reset the time index
            if ID != prev_ID:          
                time_i = 0
                prev_v = v - 2.0 * args.v_incr
                prev_ID = ID
                voltages.append([])
                times.append([])
                IDs.append(int(float(ID)))
            # If the voltage change is greater than the specified v_incr add it to the vector
            if abs(v - prev_v) > args.v_incr:
                voltages[-1].append(v)
                times[-1].append(time_i * file_header['dt'])
                prev_v = v
            time_i += 1              
    if not voltages:
        print "No trace was loaded from file"
        sys.exit(0)
    for t, v in zip(times, voltages):
        plt.plot(t,v)
    plt.legend(IDs)
    plt.title(file_header['label'] + ' ' + args.label + ' - Voltage v Time')
    plt.xlabel('Time (ms)')
    plt.ylabel('Soma Voltage (V)')
    plt.show()
else:
    raise Exception ("Unrecognised variable '%s' (from the file extension)" % variable)
