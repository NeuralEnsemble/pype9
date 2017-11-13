import ninemlcatalog
from nineml import units as un
# Load the NEST metaclass and simulation
from pype9.simulate.nest import CellMetaClass, Simulation
from pype9.plot import plot
import pype9.utils.print_logger  # @UnusedImport
# Alternatively load the neuron class
# from pype9.simulator.neuron import CellMetaClass, Simulation

# Compile and load cell class
HH = CellMetaClass(ninemlcatalog.load('neuron/HodgkinHuxley#HodgkinHuxley'))

# Create and run the simulation
with Simulation(dt=0.01 * un.ms) as sim:
    hh = HH(ninemlcatalog.load('neuron/HodgkinHuxley#SampleHodgkinHuxley'),
            V=-65 * un.mV)
    hh.record('V')
    sim.run(100 * un.ms)

# Plot recordings
plot(hh.recordings())
