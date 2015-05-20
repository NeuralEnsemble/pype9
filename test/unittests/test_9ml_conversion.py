

if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport

import os.path
from copy import deepcopy
import nineml.extensions.biophysical_cells
from pype9.cells import Tree

nineml_file = os.path.join(os.path.dirname(__file__), '..', 'data', '9ml',
                           'Golgi_Solinas08.9ml')


class Test9mlConversion(TestCase):

    def test_9ml_conversion(self):
        models = nineml.extensions.biophysical_cells.parse(nineml_file)
        model9ml = next(models.itervalues())
        tree = Tree.from_9ml(model9ml)
        tree2 = deepcopy(tree)
        needs_tuning = tree2.merge_leaves()
        new_model9ml = tree.to_9ml()
        self.assertEqual(model9ml, new_model9ml)


if __name__ == '__main__':
    test = Test9mlConversion()
    test.test_9ml_conversion()
    print "done"