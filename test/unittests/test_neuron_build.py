if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport
from pype9.cells.code_gen.neuron import CodeGenerator
from os import path
from utils import test_data_dir


class TestNeuronBuild(TestCase):

    def setUp(self):
        self.code_generator = CodeGenerator()

    def test_neuron_build(self):
        component_file = path.join(test_data_dir, 'xml', 'Izhikevich.xml')
        self.code_generator.generate(component_file,
                                     build_mode='force',
                                     ode_solver='derivimplicit',
                                     membrane_voltage='V',
                                     membrane_capacitance='Cm')

    def test_kinetics_build(self):
        component_file = path.join(test_data_dir, 'xml', 'kinetic_mechanism.xml')
        self.code_generator.generate(component_file,
                                     build_mode='force',
                                     ode_solver='derivimplicit')

if __name__ == '__main__':
    t = TestNeuronBuild()
    t.test_neuron_build()
