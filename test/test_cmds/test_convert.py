import os.path
import tempfile
import shutil
from pype9.cmd import convert
import ninemlcatalog
if __name__ == '__main__':
    from pype9.utils.testing import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport


class TestConvert(TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_convert(self):
        izhi_path = os.path.join(os.path.relpath(ninemlcatalog.root),
                                 'neuron', 'Izhikevich.xml')
        out_path = os.path.join(self.tmpdir, 'Izhikevich.xml')
        args = '--nineml_version 2 {} {}'.format(izhi_path, out_path)
        convert.run(args.split())
        # FIXME: Need a better test
        self.assertTrue(os.path.exists(out_path),
                        "Call to 'pype9 convert' failed to produce converted "
                        "file '{}'".format(out_path))
