"""
Run all examples in the examples directory to check that they run without
error
"""
from __future__ import division
from __future__ import print_function
from future.utils import PY3
import sys
import os.path
import shutil
import subprocess as sp
from unittest import TestCase  # @Reimport
from pype9.simulate.common.code_gen import BASE_BUILD_DIR
import pype9.utils.print_logger  # @UnusedImport


fig_path = os.path.join(BASE_BUILD_DIR, 'examples')

examples_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'examples'))

api_path = os.path.join(examples_path, 'api')
bash_path = os.path.join(examples_path, 'bash')


class TestExamples(TestCase):

    def setUp(self):
        os.makedirs(fig_path)

    def tearDown(self):
        shutil.rmtree(fig_path)

    def test_brunel(self):
        self.run_api('brunel', ['--save_fig', os.path.join(fig_path,
                                                           'brunel.pdf')])

    def test_izhikevich(self):
        self.run_api('izhikevich',
                     ['--save_fig', os.path.join(fig_path, 'izhikevich.pdf')])
        self.run_api('izhikevich',
                     ['--fast_spiking',
                      '--save_fig', os.path.join(fig_path,
                                                 'izhikevich-fs.pdf')])

    def test_liaf_with_alpha(self):
        self.run_api('liaf_with_alpha',
                     ['--simulator', 'nest',
                      '--save_fig', os.path.join(fig_path, 'liaf-nest.pdf')])
        self.run_api('liaf_with_alpha',
                     ['--simulator', 'neuron',
                      '--save_fig', os.path.join(fig_path, 'liaf-neuron.pdf')])

    def test_simple_hh(self):
        self.run_api('simple_hh',
                     ['--save_fig', os.path.join(fig_path,
                                                 'simple_hh-api.pdf')])
        self.run_bash('simple_hh',
                      [os.path.join(fig_path, 'simple_hh-bash.pdf')])

    def run_api(self, fname, args=[], **kwargs):
        self.run_cmd([sys.executable,
                      os.path.join(api_path, fname) + '.py'] + args,
                     **kwargs)

    def run_bash(self, fname, args=[]):
        self.run_cmd(['bash', os.path.join(bash_path, fname) + '.sh'] + args,
                     shell=True)

    def run_cmd(self, cmd, **kwargs):
        env = os.environ.copy()
        process = sp.Popen(
            cmd, stdout=sp.PIPE, stderr=sp.PIPE, env=env, **kwargs)
        stdout, stderr = process.communicate()
        if PY3:
            stdout = str(stdout.decode('utf-8'))
            stderr = str(stderr.decode('utf-8'))
        self.assertEqual(process.returncode, 0,
                         "Command '{}' exited with failure:{}\n\n{}".format(
                             ' '.join(cmd), str(stdout), str(stderr)))
