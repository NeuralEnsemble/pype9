import ninemlcatalog
from nineml import units as un
import matplotlib.pyplot as plt
# Load the NEST metaclass and simulation
from pype9.simulator.nest import CellMetaClass, simulate
# Alternatively load the neuron class
# from pype9.simulator.neuron import CellMetaClass, simulate

# Compile and load cell class
HH = CellMetaClass(
    ninemlcatalog.load('//neuron/HodgkinHuxley#HodgkinHuxley'),
    build_mode='force')

# Create and run the simulation
with simulate(t_stop=100 * un.ms, dt=0.01 * un.ms):
    hh = HH(ninemlcatalog.load('//neuron/HodgkinHuxley#SampleHodgkinHuxley'))
    hh.record('v')

# Get recording and plot
v = hh.recording('v')
plt.plot(v.times, v)
plt.show()
