import ninemlcatalog
from nineml import units as un
from pype9.neuron import CellMetaClass, simulation_controller
import ctypes

nineml_model = ninemlcatalog.load('//input/Poisson#Poisson')
Cell = CellMetaClass(nineml_model, name='PoissonTest', build_mode='force')
cell = Cell(rate=1000.0 / un.s)
cell.set_state({'t_next': 10 * un.ms})
cell.record('spike_output')
libninemlnrn = ctypes.CDLL(
    '/Users/tclose/git/pype9/pype9/neuron/cells/code_gen/libninemlnrn/'
    'libninemlnrn.so')
libninemlnrn.nineml_seed_gsl_rng(12345678)
simulation_controller.run(100 * un.ms)
print len(cell.recording('spike_output'))
