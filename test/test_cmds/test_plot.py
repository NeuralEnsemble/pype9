import os.path
import tempfile
import shutil
from pype9.cmd import plot, simulate
import neo
import ninemlcatalog
if __name__ == '__main__':
    from pype9.utils.testing import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport
    import matplotlib
    matplotlib.use('Agg')  # So DISPLAY environment variable doesn't need to be
import matplotlib.pyplot as plt  # @IgnorePep8
import matplotlib.image as img  # @IgnorePep8
import matplotlib.patches as mp  # @IgnorePep8


class TestPlot(TestCase):

    recorded_pops = ('Exc', 'Inh')

    isyn_amp = (100.0, 'pA')
    isyn_onset = (50.0, 'ms')
    isyn_init = (0.0, 'pA')
    t_stop = 100.0
    dt = 0.001

    subVb_colour = '#ff7f0e'

    def setUp(self):
        try:
            # Try to make a cache dir so the signals don't need to be
            # regenerated each time
            self.work_dir = os.path.join(os.path.dirname(__file__), '.cache')
            self.cached = True
        except OSError:
            self.work_dir = tempfile.mkdtemp()
            self.cached = False
        if not os.path.exists(self.work_dir):
            os.makedirs(self.work_dir)
        self.ref_single_cell_path = os.path.join(self.work_dir,
                                                 'single_cell_ref.png')
        self.ref_network_path = os.path.join(self.work_dir,
                                             'network_ref.png')
        self.cell_input_path = os.path.join(self.work_dir, 'plot_i.neo.pkl')
        self.cell_signal_path = os.path.join(self.work_dir, 'plot_v.neo.pkl')
        self.network_signal_path = os.path.join(self.work_dir, 'exc.neo.pkl')

    def tearDown(self):
        if not self.cached:
            shutil.rmtree(self.work_dir)

    def test_single_cell_plot(self, show=False):
        if not os.path.exists(self.cell_signal_path):
            # Generate test signal
            if not os.path.exists(self.cell_input_path):
                # First simulate input signal to have something to play into
                # izhikevich cell
                argv = ("//input/StepCurrent#StepCurrent nest {t_stop} {dt} "
                        "--record current_output {out_path} "
                        "--prop amplitude {amp} "
                        "--prop onset {onset} "
                        "--init_value current_output {init} "
                        "--build_mode force"
                        .format(out_path=self.cell_input_path,
                                t_stop=self.t_stop, dt=self.dt,
                                amp='{} {}'.format(*self.isyn_amp),
                                onset='{} {}'.format(*self.isyn_onset),
                                init='{} {}'.format(*self.isyn_init)))
                # Run input signal simulation
                simulate.run(argv.split())
            argv = (
                "//neuron/Izhikevich#SampleIzhikevichFastSpiking "
                "nest {} 0.01 "
                "--record V {} "
                "--init_value U 1.625 pA "
                "--init_value V -65.0 mV "
                "--play iSyn {in_path} "
                "--init_regime subVb "
                "--build_name IzhikevichFastSpikingPlotVersion ".format(
                    self.t_stop, self.cell_signal_path,
                    in_path=self.cell_input_path))
            simulate.run(argv.split())
        # Run plotting command
        out_path = '{}/single_cell.png'.format(self.work_dir)
        argv = ("{in_path} --save {out_path} --dims 5 5 "
                "--resolution 100.0 {hide}"
                .format(in_path=self.cell_signal_path, out_path=out_path,
                        name='v', hide=('' if show else '--hide')))
        plot.run(argv.split())
        image = img.imread(out_path)
        self._ref_single_cell_plot()
        ref_image = img.imread(self.ref_single_cell_path)
        self.assertEqual(image.shape, ref_image.shape)
        self.assertTrue(
            (image == ref_image).all(),
            "Ploted single cell data using 'plot' command (saved to '{}') did "
            "not match loaded image from '{}'"
            .format(out_path, self.ref_single_cell_path))

    def test_network_plot(self):
        if not os.path.exists(self.network_signal_path):
            # Generate test signal
            brunel_ai = ninemlcatalog.load(
                '//network/Brunel2000/AI.xml').as_network('Brunel2000AI')
            scaled_brunel_ai_path = os.path.join(self.work_dir,
                                                 'brunel_scaled.xml')
            brunel_ai.scale(0.01).write(scaled_brunel_ai_path)
            argv = ("{} nest 100.0 0.1 "
                    "--record Exc.spike_output {}"
                    .format(scaled_brunel_ai_path, self.network_signal_path))
            simulate.run(argv.split())
        # Run plotting command
        for pop_name in self.recorded_pops:
            out_path = '{}/{}.png'.format(self.work_dir, pop_name)
            argv = ("{in_path} --save {out_path} --hide --dims 5 5 "
                    "--resolution 100.0"
                    .format(in_path=self.network_signal_path,
                            out_path=out_path, name='v'))
            plot.run(argv.split())
            image = img.imread(out_path)
            self._ref_network_plot()
            ref_image = img.imread(self.ref_network_path)
            self.assertEqual(
                image.shape, ref_image.shape)
            self.assertTrue(
                (image == ref_image).all(),
                "Plotted spike data using 'plot' command (saved to '{}') "
                "did not match loaded image from '{}'"
                .format(out_path, self.ref_network_path))

    def _ref_single_cell_plot(self):
        seg = neo.PickleIO(self.cell_signal_path).read()[0]
        signal = seg.analogsignals[0]
        plt.figure()
        v_line, = plt.plot(signal.times, signal)
        for label, start, duration in zip(seg.epochs[0].labels,
                                          seg.epochs[0].times,
                                          seg.epochs[0].durations):
            if label == 'subVb':
                end = start + duration
                plt.axvspan(start, end, facecolor=self.subVb_colour,
                            alpha=0.05)
                plt.axvline(start, linestyle=':', color='gray', linewidth=0.5)
                plt.axvline(end, linestyle=':', color='gray', linewidth=0.5)
        fig = plt.gcf()
        fig.set_figheight(5)
        fig.set_figwidth(5)
        fig.suptitle('PyPe9 Simulation Output')
        plt.xlim((seg.analogsignals[0].t_start, seg.analogsignals[0].t_stop))
        plt.xlabel('Time (ms)')
        plt.ylabel('Analog signals (mV)')
        plt.title("Analog Signals", fontsize=12)
        plt.legend(handles=[
            v_line,
            mp.Patch(facecolor=self.subVb_colour, edgecolor='grey',
                     label='subVb regime', linewidth=0.5, linestyle=':'),
            mp.Patch(facecolor='white', edgecolor='grey',
                     label='subthreshold regime', linewidth=0.5,
                     linestyle=':')])
        plt.savefig(self.ref_single_cell_path, dpi=100.0)

    def _ref_network_plot(self):
        seg = neo.PickleIO(self.network_signal_path).read()[0]
        spike_times = []
        ids = []
        for i, spiketrain in enumerate(seg.spiketrains):
            spike_times.extend(spiketrain)
            ids.extend([i] * len(spiketrain))
        plt.figure()
        plt.scatter(spike_times, ids)
        fig = plt.gcf()
        fig.set_figheight(5)
        fig.set_figwidth(5)
        fig.suptitle('PyPe9 Simulation Output')
        plt.xlim((seg.spiketrains[0].t_start, seg.spiketrains[0].t_stop))
        plt.ylim((-1, len(seg.spiketrains)))
        plt.xlabel('Times (ms)')
        plt.ylabel('Cell Indices')
        plt.title("Spike Trains", fontsize=12)
        plt.savefig(self.ref_network_path, dpi=100.0)


if __name__ == '__main__':
    tester = TestPlot()
    tester.test_single_cell_plot(show=True)
