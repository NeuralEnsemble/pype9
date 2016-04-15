#!/usr/bin/env python

from argparse import ArgumentParser
import numpy as np
from matplotlib import pyplot as plt
from collections import defaultdict

parser = ArgumentParser()
parser.add_argument('recorded_data_paths', type=str, nargs='+', help="The data file for the master")
args = parser.parse_args()

header = None
all_data = defaultdict(list)

# Collate data into like variables
for pth in args.recorded_data_paths:
    with open(pth, 'r') as f:
        line = f.readline().strip()
        new_header = set(line[2:].split(' '))
    if header is None:
        header = new_header
    elif new_header != header:
        raise Exception("Mismatching headers, {} and {}".format(header, new_header))
    data = np.loadtxt(pth)
    for i, var in enumerate(header):
        all_data[var].append(data[:,i])
# Plot figures
for var in header:
    data = np.concatenate(all_data[var])
    plt.figure()
    plt.plot(data)
    plt.title(var)
plt.show()
