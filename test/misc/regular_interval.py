from nineml import units as un
from pype9.nest import CellMetaClass, simulation_controller
import ninemlcatalog
import numpy
from matplotlib import pyplot as plt


Cell = CellMetaClass(ninemlcatalog.load(
    'input/RegularInterval', 'RegularInterval'))
rate = 100.0 * un.Hz
cell = Cell(rate=rate)
cell.record('t_next')
cell.record('spike_output')
cell.update_state({'t_next': (1 * un.unitless) / rate})
simulation_controller.run(100.0)

t_next = cell.recording('t_next')
plt.plot(t_next.times, t_next)
spikes = cell.recording('spike_output')
plt.figure()
plt.scatter(spikes, numpy.ones(len(spikes)))
plt.show()
