if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport
from pype9.cells.neuron import CellMetaClass
from os import path
from utils import test_data_dir
import pylab as plt


class TestNeuronLoad(TestCase):

    def test_neuron_load(self):
        component_file = path.join(test_data_dir, 'xml', 'Izhikevich.xml')
        Izhikevich = CellMetaClass(component_file, name="Izhikevich1",
                                        build_mode='force', verbose=True,
                                        membrane_voltage='V',
                                        membrane_capacitance='Cm')
        izhi = Izhikevich()
        izhi.record('v')
        print "Running for 2000 ms"
        izhi.run(2000)
        print "Finished run"
        v = izhi.recording('v')
        plt.plot(v.times, v)
        plt.show()


if __name__ == '__main__':
    t = TestNeuronLoad()
    t.test_neuron_load()
