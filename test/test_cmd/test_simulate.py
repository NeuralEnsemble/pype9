import tempfile
import shutil
import neo.io
from pype9.cmd.simulate import run
if __name__ == '__main__':
    from pype9.utils.testing import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport


class TestSimulate(TestCase):

    ref_path = ''

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_single_cell(self):
        out_path = '{out_dir}/v.neo.pkl'.format(self.tmpdir)
        run("//neuron/Izhikevich#SampleIzhikevich neuron 100.0 0.001"
            "--record V {out_path} "
            "--init_value U -14.0 mV/ms "
            "--init_value V -65.0 mV "
            "--play Isyn //input/StepCurrent#StepCurrent current_output "
            "--play_prop Isyn amplitude 0.02 nA "
            "--play_prop Isyn onset 50 ms "
            "--play_init_value Isyn current_output 0.0 A"
            .format(out_path=out_path))
        v = neo.io.PickleIO(out_path).read().segments[0].analogsignals[0]
        ref_v = neo.io.PickleIO(
            self.ref_path).read().segments[0].analogsignals[0]
        self.assertEqual(v, ref_v)
