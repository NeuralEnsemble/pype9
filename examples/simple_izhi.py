import sys
import logging
import ninemlcatalog
from nineml import units as un
import matplotlib.pyplot as plt
# Load the NEST metaclass and simulation
from pype9.simulate.nest import CellMetaClass, Simulation
# Alternatively load the neuron class
# from pype9.simulator.neuron import CellMetaClass, simulate


logger = logging.getLogger('PyPe9')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


# Compile and load cell class
Izhikevich = CellMetaClass(
    ninemlcatalog.load('//neuron/Izhikevich#Izhikevich'))

# Create and run the simulation
with Simulation(dt=0.01 * un.ms) as sim:
    izhi = Izhikevich(
        ninemlcatalog.load('//neuron/Izhikevich#SampleIzhikevich'))
    izhi.set_state({'U': -14.0 * un.mV / un.ms, 'V': -65 * un.mV})
    izhi.record('U')
    izhi.record('V')
    sim.run(100 * un.ms)

# Get recording and plot
v = izhi.recording('V')
u = izhi.recording('U')
plt.plot(v.times, v)
plt.figure()
plt.plot(u.times, u)
plt.show()
