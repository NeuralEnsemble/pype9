"""
Run all examples in the examples directory to check that they run without
error
"""
from __future__ import division
from __future__ import print_function
from future.utils import PY3
import sys
import errno
import os.path
import stat
import shutil
import subprocess as sp
from unittest import TestCase  # @Reimport
from pype9.simulate.common.code_gen import BASE_BUILD_DIR
import pype9.utils.print_logger  # @UnusedImport


OUT_PATH = os.path.join(BASE_BUILD_DIR, 'examples')
FIG_PATH = os.path.join(OUT_PATH, 'fig')
PACKAGE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
EXAMPLES_PATH = os.path.join(PACKAGE_ROOT, 'examples')
SCRIPTS_SRC_PATH = os.path.join(PACKAGE_ROOT, 'scripts')
SCRIPTS_DEST_PATH = os.path.join(OUT_PATH, 'scripts')

api_path = os.path.join(EXAMPLES_PATH, 'api')
bash_path = os.path.join(EXAMPLES_PATH, 'bash')


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
        self.run_api('brunel', ['--save_fig',
                                os.path.join(FIG_PATH, 'brunel.pdf')])

    def test_izhikevich(self):
        self.run_api('izhikevich',
                     ['--save_fig', os.path.join(FIG_PATH, 'izhikevich.pdf')])
        self.run_api('izhikevich',
                     ['--fast_spiking',
                      '--save_fig',
                      os.path.join(FIG_PATH, 'izhikevich-fs.pdf')])

    def test_liaf_with_alpha(self):
        self.run_api('liaf_with_alpha',
                     ['--simulator', 'nest',
                      '--save_fig', os.path.join(FIG_PATH, 'liaf-nest.pdf')])
        self.run_api('liaf_with_alpha',
                     ['--simulator', 'neuron',
                      '--save_fig', os.path.join(FIG_PATH, 'liaf-neuron.pdf')])

    def test_simple_hh(self):
        self.run_api('simple_hh',
                     ['--save_fig', os.path.join(FIG_PATH,
                                                 'simple_hh-api.pdf')])
        self.run_bash('simple_hh',
                      [FIG_PATH, os.path.join(FIG_PATH, 'simple_hh-bash.pdf')])

    def run_api(self, fname, args=[], **kwargs):
        self.run_cmd([sys.executable,
                      os.path.join(api_path, fname) + '.py'] + args,
                     **kwargs)

    def run_bash(self, fname, args=[]):
        env = os.environ.copy()
        env['PATH'] = os.path.pathsep.join((SCRIPTS_DEST_PATH, env['PATH']))
        cmd = ['bash', os.path.join(bash_path, fname) + '.sh'] + args
        stdout, stderr = self.run_cmd(cmd, env=env)
        self.assertEqual(stderr, '',
                         "Command '{}' exited with stderr:{}\n\n--{}".format(
                             ' '.join(cmd), str(stdout), str(stderr)))

    def run_cmd(self, cmd, env=None, **kwargs):
        if env is None:
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
        return stdout, stderr
