if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport
from pype9.cells.code_gen.neuron import CodeGenerator
from os import path
from utils import test_data_dir


class TestNeuronBuild(TestCase):

    izhikevich_file = path.join(test_data_dir, 'xml', 'Izhikevich2003.xml')
    izhikevich_name = 'Izhikevich9ML'

    def setUp(self):
        self.code_generator = CodeGenerator()

    def test_neuron_build(self):
        self.code_generator.generate(self.izhikevich_file,
                                     name=self.izhikevich_name,
                                     build_mode='force',
                                     ode_solver='derivimplicit',
                                     membrane_voltage='V',
                                     membrane_capacitance='Cm')

if __name__ == '__main__':
    t = TestNeuronBuild()
#    t.test_kinetics_build()
    t.test_neuron_build()