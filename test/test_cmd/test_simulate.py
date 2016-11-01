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
        args = ("//neuron/Izhikevich#SampleIzhikevich neuron 10.0 "
                "--record V {out_dir}/v.neo.pkl "
                "--initial_value U -14.0 mV/ms "
                "--initial_value V -65.0 mV "
                "--play Isyn //input/StepCurrent#StepCurrent current_output "
                "--play_prop Isyn amplitude 0.02 nA "
                "--play_prop Isyn onset 50 ms "
                "--play_initial_value Isyn current_output 0.0 A")
