#!/usr/bin/env python
import ninemlcatalog
from nineml import units as un
from pype9.simulate.nest import CellMetaClass, Simulation  # Alternatively load the neuron class, from pype9.simulator.neuron import CellMetaClass, Simulation @IgnorePep8
from pype9.plot import plot
import pype9.utils.print_logger  # @UnusedImport

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
plot(hh.recordings(), title='Simple Hodgkin-Huxley Example')
