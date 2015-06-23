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


izhi = nineml.read(os.path.join(
    os.environ['HOME'], 'git', 'nineml_catalog', 'pynn_nmodl_import',
    'neurons/Izhikevich.xml'))['IzhikevichProperties']


Izhikevich = CellMetaClass(izhi)

izhi = Izhikevich()
izhi.record('v')
izhi.update_state({'v': -65.0 * pq.ms})
izhi.run(1000 * pq.ms)
current = neo.AnalogSignal(numpy.random.random(1000) * 10.0, units=pq.nA,
                           sampling_period=1.0 * pq.ms)
plt.plot(current.times, current)
plt.show()
izhi.play('iExt', current)
v = izhi.recording('v')
plt.plot(v.times, v)
plt.show()
