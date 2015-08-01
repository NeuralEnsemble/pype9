if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport
from pype9.neuron.cells.code_gen import CodeGenerator
from os import path
from utils import test_data_dir
from pype9.utils import load_9ml_prototype


class TestNeuronBuild(TestCase):

    izhikevich_file = path.join(test_data_dir, 'xml', 'Izhikevich2003.xml')
    izhikevich_name = 'Izhikevich9ML'

    def setUp(self):
        self.code_generator = CodeGenerator()

    def test_neuron_build(self):
        prototype = load_9ml_prototype(self.izhikevich_file)
        build_prototype = self.code_generator.transform_for_build(prototype)
        build_dir = self.code_generator.get_build_dir(self.izhikevich_file,
                                                      'Izhikevich')
        self.code_generator.generate(
            build_prototype, build_mode='force', build_dir=build_dir)

#     def test_kinetics_build(self):
#         component_file = path.join(test_data_dir, 'xml',
#                                    'kinetic_mechanism.xml')
#         self.code_generator.generate(component_file,
#                                      build_mode='force',
#                                      ode_solver='derivimplicit')

if __name__ == '__main__':
    t = TestNeuronBuild()
#    t.test_kinetics_build()
    t.test_neuron_build()
