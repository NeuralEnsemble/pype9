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

    def tearDown(self):
        if not self.cached:
            shutil.rmtree(self.work_dir)

    def test_single_cell_plot(self):
        # Generate test signal
        signal_path = os.path.join(self.work_dir, 'v.neo.pkl')
        if not os.path.exists(signal_path):
            argv = (
                "//neuron/Izhikevich#SampleIzhikevichFastSpiking "
                "nest 200.0 0.01 "
                "--record V  {}"
                "--init_value U 1.625 pA "
                "--init_value V -65.0 mV "
                "--init_regime subVb".format(signal_path))
            simulate.run(argv.split())
        # Run plotting command
        out_path = '{}/single_cell.png'.format(self.work_dir)
        argv = ("{in_path} --name {name} --save {out_path} --hide"
                .format(in_path=signal_path, out_path=out_path, name='v'))
        print argv
        plot.run(argv.split())
        image = img.imread(out_path)
        ref_image = img.imread(self.ref_single_cell_path)
        self.assertTrue(
            all(image == ref_image),
            "Ploted single cell data using 'plot' command did not match "
            "loaded image from '{}'".format(self.ref_single_cell_path))

    def test_network_plot(self):
        signal_path = os.path.join(self.work_dir, 'brunel.neo.pkl')
        if not os.path.exists(signal_path):
            # Generate test signal
            brunel_ai = ninemlcatalog.load(
                '//network/Brunel2000/AI.xml').as_network('Brunel2000AI')
            scaled_brunel_ai_path = os.path.join(self.work_dir,
                                                 'brunel_scaled.xml')
            brunel_ai.scale(0.01).write(scaled_brunel_ai_path)
            argv = ("{} nest 100.0 0.1 "
                    "--record Exc.spike_output {}/brunel.neo.pkl "
                    .format(scaled_brunel_ai_path, self.work_dir))
            print argv
            simulate.run(argv.split())
        # Run plotting command
        for pop_name in self.recorded_pops:
            out_path = '{}/{}.png'.format(self.work_dir, pop_name)
            argv = ("{in_path} --name {name} --save {out_path} --hide"
                    .format(in_path=signal_path, out_path=out_path, name='v'))
            print argv
            plot.run(argv.split())
            image = img.imread(out_path)
            ref_image = img.imread(self.ref_single_cell_path)
            self.assertTrue(
                all(image == ref_image),
                "Ploted spike data from '{name}' using 'plot' command did not "
                "match loaded image from '{ref_dir}/{name}'"
                .format(name=pop_name, ref_dir=self.data_dir))

    def _ref_single_cell_plot(self):
        legend = []
        plt.sca(axes[-1] if num_subplots > 1 else axes)
        units = set(s.units.dimensionality.string for s in seg.analogsignals)
        for i, signal in enumerate(seg.analogsignals):
            if args.name is None or spiketrain.name in args.name:
                plt.plot(signal.times, signal)
                un_str = (signal.units.dimensionality.string
                          if len(units) > 1 else '')
                legend.append(signal.name + un_str if signal.name else str(i))
        plt.xlim((seg.analogsignals[0].t_start, seg.analogsignals[0].t_stop))
        plt.xlabel('Time (ms)')
        un_str = (' ({})'.format(next(iter(units)))
                  if len(units) == 1 else '')
        plt.ylabel('Analog signals{}'.format(un_str))
        plt.title("{}Analog Signals".format(plt_name), fontsize=12)
        plt.legend(legend)

    def _ref_network_plot(self):
        plt.subplot(num_subplots, 1, 1)
        spike_times = []
        ids = []
        for i, spiketrain in enumerate(seg.spiketrains):
            if args.name is None or spiketrain.name in args.name:
                spike_times.extend(spiketrain)
                ids.extend([i] * len(spiketrain))
        plt.sca(axes[0] if num_subplots > 1 else axes)
        plt.scatter(spike_times, ids)
        plt.xlim((seg.spiketrains[0].t_start, seg.spiketrains[0].t_stop))
        plt.ylim((-1, len(seg.spiketrains)))
        plt.xlabel('Times (ms)')
        plt.ylabel('Cell Indices')
        plt.title("{}Spike Trains".format(plt_name), fontsize=12)
