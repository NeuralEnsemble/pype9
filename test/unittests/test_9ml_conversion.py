if __name__ == '__main__':

    class unittest(object):

        class TestCase(object):

            def __init__(self):
                try:
                    self.setUp()
                except AttributeError:
                    pass

            def assertEqual(self, first, second):
                print 'are{} equal'.format(' not' if first != second else '')
else:
    try:
        import unittest2 as unittest
    except ImportError:
        import unittest
import os.path
from copy import deepcopy
import nineml.extensions.biophysical_cells
from pype9.cells import Tree

nineml_file = os.path.join(os.path.dirname(__file__), '..', 'data', '9ml',
                           'Golgi_Solinas08.9ml')


class Test9mlConversion(unittest.TestCase):

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