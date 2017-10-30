from __future__ import print_function
import os.path
import tempfile
import shutil
from pype9.cmd import convert
import ninemlcatalog
from nineml import read
from lxml import etree
import yaml
if __name__ == '__main__':
    from pype9.utils.testing import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport


class TestConvert(TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_convert_version(self):
        in_path = os.path.join(os.path.relpath(ninemlcatalog.root),
                                 'neuron', 'Izhikevich.xml')
        out_path = os.path.join(self.tmpdir, 'Izhikevich.xml')
        args = '--nineml_version 2 {} {}'.format(in_path, out_path)
        convert.run(args.split())
        # Check the document has been written in version 2 format
        with open(out_path) as f:
            xml = etree.parse(f)
            root = xml.getroot()
        self.assertEqual(root.tag, '{http://nineml.net/9ML/2.0}NineML')
        # Check the converted document is equivalent
        in_doc = read(in_path)
        out_doc = read(out_path)
        in_doc._url = None
        out_doc._url = None
        self.assertEqual(in_doc, out_doc)

    def test_convert_format(self):
        in_path = os.path.join(os.path.relpath(ninemlcatalog.root),
                                 'neuron', 'Izhikevich.xml')
        out_path = os.path.join(self.tmpdir, 'Izhikevich.yml')
        print(out_path)
        args = '{} {}'.format(in_path, out_path)
        convert.run(args.split())
        # Check the output file is yaml
        with open(out_path) as f:
            contents = yaml.load(f)
        self.assertEqual(list(contents.keys()), [b'NineML'])
        # Check the converted document is equivalent
        in_doc = read(in_path)
        out_doc = read(out_path)
        in_doc._url = None
        out_doc._url = None
        self.assertEqual(in_doc, out_doc)
