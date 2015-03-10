if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport
from pype9.cells.neuron import CellMetaClass
from os import path
from utils import test_data_dir
import pylab as plt
from neo import AnalogSignal
import quantities as pq


class TestNeuronLoad(TestCase):

    def test_neuron_load(self):
        component_file = path.join(test_data_dir, 'xml', 'Izhikevich.xml')
        Izhikevich = CellMetaClass(component_file, name="Izhikevich1",
                                        build_mode='lazy', verbose=True,
                                        membrane_voltage='V',
                                        membrane_capacitance='Cm')
        izhi = Izhikevich()
        izhi.U = -40
        print izhi.U
        izhi.record('v')
        izhi.record('U')
        izhi.record('i')
        izhi.inject_current(
            AnalogSignal([0.0, 100.0, 0.0], sampling_period=1000 * pq.ms,
                         units='nA'))
        print "Running for 2000 ms"
        izhi.run(2000)
        print "Finished run"
        v = izhi.recording('v')
        u = izhi.recording('U')
        i = izhi.recording('i')
#         plt.plot(v.times, v)
        plt.plot(i.times, i)
#         plt.plot(u.times, u)
        plt.show()


if __name__ == '__main__':
    t = TestNeuronLoad()
    t.test_neuron_load()
