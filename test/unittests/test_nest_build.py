if __name__ == '__main__':
    from . import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport
from pype9.cells.code_gen.nest import CodeGenerator
from os import path
from . import test_data_dir


class TestNestBuild(TestCase):

    def test_nest_build(self):
        component_file = path.join(test_data_dir, 'xml', 'HodgkinHuxley.xml')
        code_generator = CodeGenerator()
        code_generator.generate(component_file, 0.0,
                                build_mode='build_only',
                                ode_solver='ida', v_threshold=None)

if __name__ == '__main__':
    t = TestNestBuild()
    t.test_nest_build()
