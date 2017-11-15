"""
Run all examples in the examples directory to check that they run without
error
"""
from __future__ import division
from __future__ import print_function
import matplotlib
from future.utils import PY3
import sys
import errno
import os.path
import stat
import shutil
import subprocess as sp
import ninemlcatalog
from unittest import TestCase  # @Reimport
matplotlib.use('Agg')
import logging  # @IgnorePep8
from pype9.simulate.common.code_gen import BASE_BUILD_DIR  # @IgnorePep8
import pype9.utils.logger_handlers.sysout_info  # @UnusedImport @IgnorePep8

logger = logging.getLogger('pype9')

OUT_PATH = os.path.join(BASE_BUILD_DIR, 'examples')
FIG_PATH = os.path.join(OUT_PATH, 'fig')
PACKAGE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..',
                                            '..'))
EXAMPLES_PATH = os.path.join(PACKAGE_ROOT, 'examples')
SCRIPTS_SRC_PATH = os.path.join(PACKAGE_ROOT, 'scripts')
SCRIPTS_DEST_PATH = os.path.join(OUT_PATH, 'scripts')

api_path = os.path.join(EXAMPLES_PATH, 'api')
bash_path = os.path.join(EXAMPLES_PATH, 'bash')

# Import example run methods
sys.path.insert(0, api_path)
logger.info("sys.path: {}".format(sys.path))
logger.info(os.listdir(api_path))
from brunel import run as brunel_run  # @UnresolvedImport @IgnorePep8
from izhikevich import run as izhikevich_run  # @UnresolvedImport @IgnorePep8
from liaf_with_alpha import run as liaf_with_alpha_run  # @UnresolvedImport @IgnorePep8
from simple_hh import run as simple_hh_run  # @UnresolvedImport @IgnorePep8
sys.path.pop(0)


class TestExamples(TestCase):

    def setUp(self):
        try:
            shutil.rmtree(OUT_PATH)
        except OSError as e:
            if e.errno != errno.ENOENT:  # Ignore if it is missing
                raise
        os.makedirs(FIG_PATH)
        os.makedirs(SCRIPTS_DEST_PATH)
        # Copy pype9 script and replace shebang with current executable
        with open(os.path.join(SCRIPTS_SRC_PATH, 'pype9')) as f:
            lines = f.readlines()
        lines[0] = '#!{}'.format(sys.executable)
        contents = '\n'.join(lines)
        if PY3:
            contents = contents.encode('utf-8')
        dst_path = os.path.join(SCRIPTS_DEST_PATH, 'pype9')
        with open(dst_path, 'wb') as f:
            f.write(contents)
        os.chmod(dst_path, (
            stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH | stat.S_IWUSR |
            stat.S_IXUSR))

    def tearDown(self):
        shutil.rmtree(OUT_PATH)

    def test_brunel(self):
        brunel_run(
            ['--reference',
             '--save_fig', os.path.join(FIG_PATH, 'brunel.png')])

    def test_izhikevich(self):
        izhikevich_run(
            ['--save_fig', os.path.join(FIG_PATH, 'izhikevich.png')])
        izhikevich_run(
            ['--fast_spiking',
             '--save_fig', os.path.join(FIG_PATH, 'izhikevich-fs.png')])

    def test_liaf_with_alpha(self):
        liaf_with_alpha_run(
            ['--simulator', 'nest',
             '--save_fig', os.path.join(FIG_PATH, 'liaf-nest.png')])
        liaf_with_alpha_run(
            ['--simulator', 'neuron',
             '--save_fig', os.path.join(FIG_PATH, 'liaf-neuron.png')])

    def test_simple_hh(self):
        simple_hh_run(
            ['--save_fig', os.path.join(FIG_PATH, 'simple_hh-api.png')])
        self.run_bash(
            'simple_hh',
            [FIG_PATH, os.path.join(FIG_PATH, 'simple_hh-bash.png')])

    def test_convert_xml_to_yml(self):
        self.run_bash(
            'convert_xml_to_yml',
            [ninemlcatalog.load('neuron/Izhikevich').url, FIG_PATH])

    def run_bash(self, script_name, args):
        # Ensure that the destination scripts dir is on the system path and
        # package root is on the python path
        env = os.environ.copy()
        env['PATH'] = os.pathsep.join([SCRIPTS_DEST_PATH, env['PATH']])
        env['PYTHONPATH'] = os.pathsep.join([PACKAGE_ROOT, env['PYTHONPATH']])
        sp.check_call([os.path.join(bash_path, script_name) + '.sh'] + args,
                      env=env)
