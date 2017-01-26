import os.path
import tempfile
import shutil
from pype9.cmd import plot, simulate
import neo
import ninemlcatalog
import matplotlib.pyplot as plt
import matplotlib.image as img
if __name__ == '__main__':
    from pype9.utils.testing import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport


class TestPlot(TestCase):

    recorded_pops = ('Exc', 'Inh')

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
                                                 'single_cell.png')
        self.ref_network_path = os.path.join(self.work_dir,
                                             'network.png')
        self.cell_signal_path = os.path.join(self.work_dir, 'v.neo.pkl')
        self.network_signal_path = os.path.join(self.work_dir, 'exc.neo.pkl')

    def tearDown(self):
        if not self.cached:
            shutil.rmtree(self.work_dir)

    def test_single_cell_plot(self):
        # Generate test signal
        if not os.path.exists(self.cell_signal_path):
            argv = (
                "//neuron/Izhikevich#SampleIzhikevichFastSpiking "
                "nest 200.0 0.01 "
                "--record V {} "
                "--init_value U 1.625 pA "
                "--init_value V -65.0 mV "
                "--init_regime subVb ".format(self.cell_signal_path))
            simulate.run(argv.split())
        # Run plotting command
        out_path = '{}/single_cell.png'.format(self.work_dir)
        argv = ("{in_path} --save {out_path} --hide"
                .format(in_path=self.cell_signal_path, out_path=out_path,
                        name='v'))
        plot.run(argv.split())
        image = img.imread(out_path)
        self._ref_single_cell_plot()
        ref_image = img.imread(self.ref_single_cell_path)
        self.assertTrue(
            (image == ref_image).all(),
            "Ploted single cell data using 'plot' command did not match "
            "loaded image from '{}'".format(self.ref_single_cell_path))

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
            argv = ("{in_path} --save {out_path} --hide"
                    .format(in_path=self.network_signal_path,
                            out_path=out_path, name='v'))
            plot.run(argv.split())
            image = img.imread(out_path)
            self._ref_network_plot()
            ref_image = img.imread(self.ref_network_path)
            self.assertTrue(
                (image == ref_image).all(),
                "Plotted spike data using 'plot' command did not "
                "match loaded image from '{}'"
                .format(self.ref_network_path))

    def _ref_single_cell_plot(self):
        seg = neo.PickleIO(self.cell_signal_path).read()[0]
        signal = seg.analogsignals[0]
        plt.plot(signal.times, signal)
        plt.xlim((seg.analogsignals[0].t_start, seg.analogsignals[0].t_stop))
        plt.xlabel('Time (ms)')
        plt.ylabel('Analog signals')
        plt.title("Analog Signals", fontsize=12)
        plt.legend(['1'])
        plt.savefig(self.ref_single_cell_path)

    def _ref_network_plot(self):
        seg = neo.PickleIO(self.network_signal_path).read()[0]
        spike_times = []
        ids = []
        for i, spiketrain in enumerate(seg.spiketrains):
            spike_times.extend(spiketrain)
            ids.extend([i] * len(spiketrain))
        plt.scatter(spike_times, ids)
        plt.xlim((seg.spiketrains[0].t_start, seg.spiketrains[0].t_stop))
        plt.ylim((-1, len(seg.spiketrains)))
        plt.xlabel('Times (ms)')
        plt.ylabel('Cell Indices')
        plt.title("Spike Trains", fontsize=12)
        plt.savefig(self.ref_network_path)
