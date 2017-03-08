import sys
import logging
import ninemlcatalog
from nineml import units as un
import matplotlib.pyplot as plt
# Load the NEST metaclass and simulation
from pype9.simulator.nest import CellMetaClass, simulation
# Alternatively load the neuron class
# from pype9.simulator.neuron import CellMetaClass, simulate


logger = logging.getLogger('PyPe9')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


# Compile and load cell class
HH = CellMetaClass(ninemlcatalog.load('//neuron/HodgkinHuxley#HodgkinHuxley'))

# Create and run the simulation
with simulation(dt=0.01 * un.ms) as sim:
    hh = HH(ninemlcatalog.load('//neuron/HodgkinHuxley#SampleHodgkinHuxley'))
    hh.record('V')
    sim.run(100 * un.ms)

# Get recording and plot
v = hh.recording('V')
plt.plot(v.times, v)
plt.show()
