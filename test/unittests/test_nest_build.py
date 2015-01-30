if __name__ == '__main__':
    from . import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport
from pype9.cells.code_gen.nest import CodeGenerator
import nineml
from os.path import dirname, join, abspath


class TestNestBuild(TestCase):

    test_dir = abspath(join(dirname(__file__), '..', 'data',
                            'xml'))
    component_file = join(test_dir, 'HodgkinHuxleyModified.xml')
    comp = nineml.read(component_file)['HodgkinHuxleyModified']

    def test_nest_build(self):
        # initial_state_file = join(
        #     dirname(__file__), '..', '..', 'examples',
        #     'HodgkinHuxleyInitialState.xml')
        code_generator = CodeGenerator()
        code_generator.generate(self.component_file, 0.0,  # initial_state_file
                                build_mode='generate_only',
                                ode_solver='ida', v_threshold=None)

if __name__ == '__main__':
    t = TestNestBuild()
    t.test_nest_build()
