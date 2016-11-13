import tempfile
import shutil
import neo.io
from pype9.cmd.simulate import run
import ninemlcatalog
from pype9.neuron import (
    CellMetaClass as CellMetaClassNEURON,
    simulation_controller as simulatorNEURON,
    Network as NetworkNEURON)
from pype9.nest import (
    CellMetaClass as CellMetaClassNEST,
    simulation_controller as simulatorNEST,
    Network as NetworkNEST)
if __name__ == '__main__':
    from pype9.utils.testing import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport


class TestSimulateAndPlot(TestCase):

    ref_path = ''

    # Izhikevich simulation params
    t_stop = 100.0
    dt = 0.001
    U = (-14.0, 'mV/ms')
    V = (-65.0, 'mV')
    Isyn = ((20.0, 'pA'), (50.0, 'ms'), (0.0, 'pA'))
    izhi_path = '//neuron/Izhikevich#SampleIzhikevich'

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_single_cell(self):
        out_path = '{}/v.pkl'.format(self.tmpdir)
        for simulator in ('nest', 'neuron'):
            argv = (
                "{nineml_model} {sim} {t_stop} {dt} "
                "--record V {out_path} v "
                "--init_value U {U} "
                "--init_value V {V} "
                "--play Isyn //input/StepCurrent#StepCurrent current_output "
                "--play_prop Isyn amplitude {isyn_amp} "
                "--play_prop Isyn onset {isyn_onset} "
                "--play_init_value Isyn current_output {isyn_init} "
                "--build_mode force"
                .format(nineml_model=self.izhi_path, sim=simulator,
                        out_path=out_path, t_stop=self.t_stop, dt=self.dt,
                        U='{} {}'.format(*self.U), V='{} {}'.format(*self.V),
                        isyn_amp='{} {}'.format(*self.Isyn[0]),
                        isyn_onset='{} {}'.format(*self.Isyn[1]),
                        isyn_init='{} {}'.format(*self.Isyn[2])))
            run(argv.split())
            v = neo.io.PickleIO(out_path).read().segments[0].analogsignals[0]
            ref_v = self._ref_single_cell(simulator)
            self.assertTrue(all(v == ref_v),
                             "'simulate' command produced different results to"
                             " to api reference for izhikevich model using "
                             "'{}' simulator".format(simulator))

    def _ref_single_cell(self, simulator):
        if simulator == 'neuron':
            metaclass = CellMetaClassNEURON
            simulation_controller = simulatorNEURON
        else:
            metaclass = CellMetaClassNEST
            simulation_controller = simulatorNEST
        nineml_model = ninemlcatalog.load(self.izhi_path)
        cell = metaclass(nineml_model, name='izhikevichAPI')()
        cell.record('V')
        simulation_controller.run(self.t_stop)
        return cell.recording('V')
