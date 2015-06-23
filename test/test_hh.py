simulator = 'neuron'
import nineml
if simulator == 'neuron':
    from pype9.cells.neuron import CellMetaClass  # @UnusedImport
else:
    from pype9.cells.nest import CellMetaClass  # @Reimport
import os.path
import quantities as pq
from matplotlib import pyplot as plt
import neo
import numpy


hh = nineml.read(os.path.join(
    os.environ['HOME'], 'git',
    'nineml_catalog', 'neurons', 'HodgkinHuxley.xml'))['HodgkinHuxley']


HH = CellMetaClass(hh, build_mode='force')#, ion_species={
#    'ik': 'k', 'ina': 'na', 'il': None, 'ena': 'na', 'ek': 'k'})

hh = HH()
hh.record('v')
hh.update_state({'v': -65.0 * pq.ms})
current = neo.AnalogSignal(numpy.random.random(1000) * 10.0, units=pq.nA,
                           sampling_period=1.0 * pq.ms)
hh.play('iExt', current)
hh.run(1000 * pq.ms)
v = hh.recording('v')
plt.plot(v.times, v)
plt.show()
