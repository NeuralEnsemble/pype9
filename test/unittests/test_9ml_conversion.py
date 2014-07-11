try:
    import unittest2 as unittest
except ImportError:
    import unittest
import os.path
import nineml.extensions.biophysical_cells
from nineline.cells import Tree

nineml = os.path.join(os.path.dirname(__file__), '..', 'data', '9ml',
                         'Golgi_Solinas08.9ml')


class Test9mlConversion(unittest.TestCase):

    def test_9ml_convertion(self):
        models = nineml.extensions.biophysical_cells.parse(nineml)
        model9ml = next(models.itervalues())
        tree = Tree.from_9ml(model9ml)
        new_model9ml = tree.to_9ml()
        self.assertEqual(model9ml, new_model9ml)
