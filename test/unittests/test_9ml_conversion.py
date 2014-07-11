try:
    import unittest2 as unittest
except ImportError:
    import unittest
import os.path
from lxml import etree
import nineml.extensions.biophysical_cells
from nineline.cells import Tree

nineml_in = os.path.join(os.path.dirname(__file__), '..', 'data', '9ml',
                         'Golgi_Solinas08.9ml')
nineml_out = os.path.join(os.path.dirname(__file__), '..', 'data', '9ml',
                         'Golgi_Solinas08-out.9ml')


class Test9mlConversion(unittest.TestCase):

    def test_9ml_convertion(self):
        models = nineml.extensions.biophysical_cells.parse(nineml_in)
        model = next(models.itervalues())
        tree = Tree.from_9ml(model)
        etree.ElementTree(tree.to_9ml().to_xml()).write(
                 nineml_out,
                 encoding="UTF-8",
                 pretty_print=True,
                 xml_declaration=True)
