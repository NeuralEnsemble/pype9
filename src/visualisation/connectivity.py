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
import numpy as np
import matplotlib.pyplot as plt
import argparse
from mpl_toolkits.mplot3d import Axes3D #@UnusedImport
from common import tube_mesh, ellipse_tube_mesh
from copy import copy

PROJ_TUPLE_LENGTH = 5

PROJECT_PATH = os.path.normpath(os.path.join(os.path.realpath(__file__), '..', '..', '..'))
EXPORT_POPULATIONS_PATH = os.path.join(PROJECT_PATH, 'xml/cerebellum', 'brep', 'build', 'populations')
EXPORT_PROJECTIONS_PATH = os.path.join(PROJECT_PATH, 'xml/cerebellum', 'brep', 'build', 'projections_pynn')

parser = argparse.ArgumentParser(description='A script to ')
parser.add_argument('--include', type=str, nargs='+', default=['MossyFibers', 'ParallelFibers', 'Golgis', 'AscendingFibers'],
                                           help="A list of populations to include in the plot (if passed 'all', all populations in the directory will be plotted)")
parser.add_argument('--projection', type=str, nargs='+', default=None, help="A list of 5-tuples, each containing the pre population label, the post population label, the pre cell id, the radius, and optionally the synpase type")
parser.add_argument('--transparency', type=float, default=0.3, help="The transparency of the projection barrier surfaces")
parser.add_argument('--save', type=str, help="The path to save the figure to")
parser.add_argument('--preset', type=str, default=None, help="Switch between preset figures, for CNS poster")
args = parser.parse_args()

args.preset = 'Gr-Go'

if args.preset == 'Go-Gr':
    args.include = ['Golgis', 'Granules']
    args.projection = ['Golgis Granules 75:26:150 None Ellipse 200 58.35']
elif args.preset == 'MF-Gr':
    args.include = ['MossyFibers', 'Granules']
    args.projection = ['MossyFibers Granules 50:87:410 AMPA Circle 19.44']
elif args.preset == 'Gr-Go':
    args.include = ['Golgis', 'Granules']
    args.projection = ['Granules Golgis 75:966:5795']
elif args.preset == 'MF-Go':
    args.include = ['MossyFibers', 'Golgis']
    args.projection = ['MossyFibers Golgis 50:137:410 AMPA Circle 291']

#  ['Granules Granules 200 NMDA Circle 19.44'] # ['Granules Golgis 0:250:6001 None Circle 2']  

projections = []
required_pops = []

load_include = copy(args.include)

# Add default radius and synapse option of None if it isn't present
if args.projection:
    for proj in args.projection:
        proj_list = proj.split()
        if len(proj_list) < 3:
            raise Exception("At least three elements, pre-popluation-label, post-population-label and cell ID are required for connection")
        pre = proj_list[0]
        post = proj_list[1]
        ids = proj_list[2]
        if ':' in ids:
            rnge = ids.split(':')
            rnge = [ int(i) for i in rnge]
            try:
                ids = range(rnge[0], rnge[2], rnge[1])
            except IndexError:
                ids = range(rnge[0], rnge[1])
        else:
            ids = [int(ids)]
        if len(proj_list) < 4 or proj_list[3] == 'None':
            synapse = None
        else:
            synapse = proj_list[3]
        if len(proj_list) > 4 :
            dist_args = proj_list[4:]
        else:
            dist_args = None
        projections.append((pre, post, ids, synapse, dist_args))
        load_include.extend([pre, post])
else:
    projections = []

# Load positions from file into dictionary and record limits on z axis
pop_positions = {}
max_z = -float('inf')
min_z = float('inf')
for pop_label in os.listdir(EXPORT_POPULATIONS_PATH):
    if '~' not in pop_label:
        if args.include == ['all'] or pop_label in load_include:
            pop = np.loadtxt(os.path.join(EXPORT_POPULATIONS_PATH, pop_label)) #@UndefinedVariable
            pop_max_z = pop[:, 2].max()
            pop_min_z = pop[:, 2].min()
            if pop_max_z > max_z:
                max_z = pop_max_z
            if pop_min_z < min_z:
                min_z = pop_min_z
            pop_positions[pop_label] = pop

if args.preset == 'Go-Gr':
    colors = ['magenta', 'green', 'red', 'orange', 'purple', 'magenta', 'cyan', 'blue', 'green']
    markers = ['^', '+', 'o', '^', 'x', '+', '*', 'o']
elif args.preset == 'MF-Gr':
    colors = ['cyan', 'green', 'red', 'orange', 'purple', 'magenta', 'yellow', 'blue', 'green']
    markers = [ 'o', '+', 'o', '^', 'x', '+', '*', 'o']
elif args.preset == 'MF-Go':
    colors = ['cyan', 'magenta', 'red', 'orange', 'purple', 'magenta', 'cyan', 'blue', 'green']
    markers = [ 'o', '^', '+', '^', 'x', '+', '*', 'o']
elif args.preset == 'Gr-Go':
    colors = ['magenta', 'green', 'red', 'orange', 'purple', 'magenta', 'cyan', 'blue', 'green']
    markers = ['^', '+', 'o', '^', 'x', '+', '*', 'o']


proxies = {}

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

min_bound = float('inf')
max_bound = float('-inf')

color_count = 0
for (label, pop) in pop_positions.items():
    if args.include == ['all'] or label in args.include:
        ax.scatter(xs=pop[:, 0], ys=pop[:, 1], zs=pop[:, 2], c=colors[color_count], marker=markers[color_count])
        minimum = pop.min()
        if minimum < min_bound:
            min_bound = minimum
        maximum = pop.max()
        if maximum > max_bound:
            max_bound = maximum
        proxies[label] = plt.Rectangle((0, 0), 1, 1, fc=colors[color_count])
        print "Added the '%s' population (%s %s)" % (label, colors[color_count], markers[color_count])
        color_count += 1

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.legend(proxies.values(), proxies.keys())

if args.projection:

    for pre_label, post_label, cell_ids, synapse, dist_args in projections:
        #Plot bounding cylinder
        for cell_i in cell_ids:
            cell_pos = pop_positions[pre_label][cell_i, :]
            if dist_args:
                if dist_args[0] == 'Circle':
                    radius = float(dist_args[1])
                    tube_core = np.array((cell_pos, cell_pos, cell_pos))
                    tube_core[0, 2] = min_z
                    tube_core[2, 2] = max_z
                    (X, Y, Z) = tube_mesh(tube_core, radius, num_edges=80)
                elif dist_args[0] == 'Ellipse':
                    x_scale = float(dist_args[1])
                    y_scale = float(dist_args[2])
                    tube_core = np.array((cell_pos, cell_pos, cell_pos))
                    tube_core[0, 2] = min_z
                    tube_core[2, 2] = max_z
                    (X, Y, Z) = ellipse_tube_mesh(tube_core, x_scale, y_scale, num_edges=80)
                else:
                    raise Exception ("Unrecognised distance pattern % s" % dist_args[0])
                surf = ax.plot_surface(X, Y, Z, alpha=args.transparency)
                surf.set_edgecolor('none')
            #Plot connections
            proj_name = pre_label + '_' + post_label
            if synapse:
                proj_name += '_' + synapse
            proj = np.loadtxt(os.path.join(EXPORT_PROJECTIONS_PATH, proj_name))
            cell_proj = proj[proj[:, 0] == cell_i, :]
            post_positions = pop_positions[post_label][cell_proj[:, 1].astype(int), :]
            # Basically adds another dimension to the front of the post_positions array
            for i in xrange(post_positions.shape[0]):
                ax.plot((cell_pos[0], post_positions[i, 0]),
                        (cell_pos[1], post_positions[i, 1]),
                        (cell_pos[2], post_positions[i, 2]),
                        c=colors[color_count % len(colors)])
            print "Plotted %d projections" % post_positions.shape[0]
            color_count += 1

# Hack for poster
x_range = max_bound - min_bound
ax.set_xlim(-x_range / 2, x_range / 2)

if args.save:
    fig.savefig(args.save, dpi=600, transparent=True)
    print "Saved figure to %s" % args.save
else:
    plt.show()

