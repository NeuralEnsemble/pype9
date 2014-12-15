from nineline.cells.code_gen.nest import CodeGenerator
import nineml
from os.path import dirname, join, abspath
build_dir = join(dirname(__file__), 'build')
test_dir = abspath(join(dirname(__file__), '..', 'data',
                        'xml'))
component_file = join(test_dir, 'HodgkinHuxleyModified.xml')
comp = nineml.read(component_file)['HodgkinHuxleyModified']
# initial_state_file = join(
#     dirname(__file__), '..', '..', 'examples',
#     'HodgkinHuxleyInitialState.xml')
code_generator = CodeGenerator()
code_generator.generate(component_file, 0.0,  # initial_state_file,
                        build_mode='generate_only',
                        ode_solver='ida', v_threshold=None)
