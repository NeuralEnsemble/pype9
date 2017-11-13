"""
Run all examples in the examples directory to check that they run without
error
"""
from __future__ import division
from __future__ import print_function
import sys
import os.path
import subprocess as sp
from unittest import TestCase  # @Reimport
import pype9.utils.print_logger  # @UnusedImport


examples_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'examples'))

api_path = os.path.join(examples_path, 'api')
bash_path = os.path.join(examples_path, 'bash')


class TestExamples(TestCase):

    def test_brunel(self):
        self.run_api('brunel')

    def test_izhikevich(self):
        self.run_api('izhikevich')

    def test_liaf_with_alpha(self):
        self.run_api('liaf_with_alpha')

    def test_simple_hh(self):
        self.run_api('simple_hh')
        self.run_bash('simple_hh')

    def run_api(self, fname, args=[]):
        all_args = [sys.executable,
                    os.path.join(api_path, fname) + '.py'] + args
        process = sp.Popen(
            all_args, stdout=sp.PIPE, stderr=sp.PIPE, env=os.environ.copy())
        stdout, stderr = process.communicate()
        self.assertEqual(process.returncode, 0,
                         "Command '{}' exited with failure:{}\n\n{}".format(
                             ' '.join(all_args), str(stdout), str(stderr)))

    def run_bash(self, fname, args=[]):
        all_args = ['bash', os.path.join(bash_path, fname) + '.sh'] + args
        process = sp.Popen(
            all_args, stdout=sp.PIPE, stderr=sp.PIPE, env=os.environ.copy(),
            shell=True)
        stdout, stderr = process.communicate()
        self.assertEqual(process.returncode, 0,
                         "Command '{}' exited with failure:{}\n\n{}".format(
                             ' '.join(all_args), str(stdout), str(stderr)))
