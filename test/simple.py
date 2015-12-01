import os.path
from nineml import units as un
from nineml.user.multi import MultiDynamicsProperties
from pype9.neuron import CellMetaClass
import neo
import ninemlcatalog
from pype9.neuron.cells.controller import simulation_controller
from matplotlib import pyplot as plt
import quantities as pq


liaf = ninemlcatalog.load(
    '/neurons/LeakyIntegrateAndFire/LeakyIntegrateAndFire')
liaf_props = ninemlcatalog.load(
    '/neurons/LeakyIntegrateAndFire/SampleLeakyIntegrateAndFire')

alpha = ninemlcatalog.load(
    'postsynapticresponses/Alpha/Alpha')
alpha_props = ninemlcatalog.load(
    'postsynapticresponses/Alpha/SampleAlpha')

dyn_props = MultiDynamicsProperties(
    'LiafAlpha',
    {'cell': liaf_props, 'psr': alpha_props},
    port_connections=[('psr', 'iSyn', 'cell', 'iExt')],
    port_exposures=[('input_spike', 'psr', 'spike'),
                    ('weight', 'psr', 'q')])

Cell = CellMetaClass(dyn_props.component_class,
                     build_dir=os.path.dirname(os.path.realpath(__file__)),
                     initial_regime='subthreshold___sole',
                     build_mode='force',
                     connection_weight='weight')
cell = Cell(dyn_props)

cell.record('v__cell')
cell.record('a__psr')
cell.record('b__psr')
cell.record_transitions()
cell.update_state({'end_refractory__cell': 0 * un.ms,
                   'v__cell': -65.0 * un.mV, 'a__psr': 0, 'b__psr': 0})

cell.play('input_spike', neo.SpikeTrain([20, 40, 60, 80], units='ms',
                                        t_stop=100.0 * pq.ms),
          weight=10)

simulation_controller.run(100)

v = cell.recording('v__cell')
a = cell.recording('a__psr')
b = cell.recording('b__psr')
print cell.transitions()

plt.plot(v.times, v)
plt.plot(a.times, a)
plt.plot(b.times, b)
plt.show()
