if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport
from pype9.cells.neuron import Pype9CellMetaClass
from os import path
from utils import test_data_dir


class TestNeuronLoad(TestCase):

    def test_neuron_load(self):
        component_file = path.join(test_data_dir, 'xml', 'Izhikevich.xml')
        Izhikevich = Pype9CellMetaClass(component_file, name="Izhikevich1",
                                        build_mode='force', verbose=True,
                                        membrane_voltage='V',
                                        membrane_capacitance='Cm')
        izhi = Izhikevich()
        print dir(izhi)


if __name__ == '__main__':
    t = TestNeuronLoad()
    t.test_neuron_load()
