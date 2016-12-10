import os.path
import tempfile
import shutil
from pype9.cmd import plot
import matplotlib.image as img
if __name__ == '__main__':
    from pype9.utils.testing import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport


class TestPlot(TestCase):

    data_dir = os.path.join(os.path.dirname(__file__), '..', 'ref_data')
    ref_single_cell_path = os.path.join(data_dir, 'ref_single_cell.png')
    recorded_pops = ('Exc', 'Inh')

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_single_cell_plot(self):
        in_path = os.path.join(self.data_dir, 'v.neo.pkl')
        out_path = '{}/single_cell.png'.format(self.tmpdir)
        argv = ("{data_file} --name {name} --save {out_path} --hide"
                .format(data_file=in_path, out_path=out_path, name='v'))
        plot.run(argv.split())
        image = img.imread(out_path)
        ref_image = img.imread(self.ref_single_cell_path)
        self.assertTrue(
            all(image == ref_image),
            "Ploted single cell data using 'plot' command did not match "
            "loaded image from '{}'".format(self.ref_single_cell_path))

    def test_network_plot(self):
        in_path = os.path.join(self.data_dir, 'brunel.neo.pkl')
        for pop_name in self.recorded_pops:
            out_path = '{}/{}.png'.format(self.tmpdir)
            argv = ("{data_file} --name {name} --save {out_path} --hide"
                    .format(in_path=in_path, out_path=out_path, name='v'))
            plot.run(argv.split())
            image = img.imread(out_path)
            ref_image = img.imread(self.ref_single_cell_path)
            self.assertTrue(
                all(image == ref_image),
                "Ploted spike data from '{name}' using 'plot' command did not "
                "match loaded image from '{ref_dir}/{name}'"
                .format(name=pop_name, ref_dir=self.data_dir))
