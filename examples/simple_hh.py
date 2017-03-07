import ninemlcatalog
from nineml import units as un
import matplotlib.pyplot as plt
# Load the NEST metaclass and simulation
from pype9.simulator.nest import CellMetaClass, simulation
# Alternatively load the neuron class
# from pype9.simulator.neuron import CellMetaClass, simulate

# Compile and load cell class
HH = CellMetaClass(
    ninemlcatalog.load('//neuron/HodgkinHuxley#HodgkinHuxley'),
    build_mode='force')

# Create and run the simulation
with simulation(dt=0.01 * un.ms) as sim:
    hh = HH(ninemlcatalog.load('//neuron/HodgkinHuxley#SampleHodgkinHuxley'))
    hh.record('v')
    sim.run(100 * un.ms)

# Get recording and plot
v = hh.recording('v')
plt.plot(v.times, v)
plt.show()
