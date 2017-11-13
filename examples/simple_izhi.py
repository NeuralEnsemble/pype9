import ninemlcatalog
from nineml import units as un
from pype9.simulate.nest import CellMetaClass, Simulation  # Alternatively load the neuron class from pype9.simulator.neuron import CellMetaClass, simulate @IgnorePep8
from pype9.plot import plot
import pype9.utils.print_logger  # @UnusedImport

# Compile and load cell class
Izhikevich = CellMetaClass(
    ninemlcatalog.load('//neuron/Izhikevich#IzhikevichFastSpiking'))

# Create and run the simulation
with Simulation(dt=0.01 * un.ms) as sim:
    izhi = Izhikevich(
        ninemlcatalog.load('//neuron/Izhikevich#SampleIzhikevichFastSpiking'),
        regime_='subthreshold')
    izhi.record('U')
    izhi.record('V')
    sim.run(100 * un.ms)

# Get recording and plot
plot(izhi.recordings())
