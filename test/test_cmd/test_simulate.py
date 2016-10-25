import tempfile
import shutil
from pype9.cmd.simulate import run
if __name__ == '__main__':
    from pype9.utils.testing import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport


class TestSimulate(TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_single_cell(self):
        args = ("//neuron/Izhikevich neuron 10.0 --name Izhikevich "
                "--record v {out_dir}/v.pkl --play )
