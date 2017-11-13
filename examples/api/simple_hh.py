#!/usr/bin/env python
from argparse import ArgumentParser
import ninemlcatalog
from nineml import units as un
from pype9.simulate.nest import CellMetaClass, Simulation  # Alternatively load the neuron class, from pype9.simulator.neuron import CellMetaClass, Simulation @IgnorePep8
from pype9.plot import plot
import pype9.utils.print_logger  # @UnusedImport

parser = ArgumentParser()
parser.add_argument('--save_fig', type=str, default=None,
                    help=("Location to save the generated figures"))
args = parser.parse_args()

# Compile and load cell class
HH = CellMetaClass(
    ninemlcatalog.load('neuron/HodgkinHuxley#PyNNHodgkinHuxley'))

# Create and run the simulation
with Simulation(dt=0.01 * un.ms) as sim:
    hh = HH(
        ninemlcatalog.load('neuron/HodgkinHuxley#PyNNHodgkinHuxleyProperties'),
        v=-65 * un.mV, m=0.0, h=1.0, n=0.0)
    hh.record('v')
    sim.run(500 * un.ms)

# Plot recordings
plot(hh.recordings(), title='Simple Hodgkin-Huxley Example',
     save=args.save_fig, show=(not args.save_fig))
