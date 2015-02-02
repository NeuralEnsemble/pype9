if __name__ == '__main__':
    from . import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport
from pype9.cells.code_gen.neuron import CodeGenerator
from os import path
from . import test_data_dir


class TestNeuronBuild(TestCase):

    def test_neuron_build(self):
        component_file = path.join(test_data_dir, 'xml', 'Izhikevich.xml')
        code_generator = CodeGenerator()
        code_generator.generate(component_file, 0.0,
                                build_mode='force',
                                ode_solver='derivimplicit', v_threshold=None)

if __name__ == '__main__':
    t = TestNeuronBuild()
    t.test_neuron_build()
