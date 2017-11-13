import ninemlcatalog
from nineml import units as un
from pype9.simulate.nest import CellMetaClass, Simulation
from pype9.plot import plot
import pype9.utils.print_logger  # @UnusedImport
# Alternatively load the neuron class
# from pype9.simulator.neuron import CellMetaClass, simulate


# Compile and load cell class
Izhikevich = CellMetaClass(
    ninemlcatalog.load('//neuron/Izhikevich#Izhikevich'))

# Create and run the simulation
with Simulation(dt=0.01 * un.ms) as sim:
    izhi = Izhikevich(
        ninemlcatalog.load('//neuron/Izhikevich#SampleIzhikevich'),
        U=-14.0 * un.mV / un.ms, V=-65 * un.mV)
    izhi.record('U')
    izhi.record('V')
    sim.run(100 * un.ms)

# Get recording and plot
plot(izhi.recordings())
