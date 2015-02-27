"""
    A module contain unit tests for the nine cells package
"""
if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport
import os.path
from utils import test_data_dir
# import os
# from mock import Mock
# from numpy.testing import assert_array_equal, assert_array_almost_equal
import pype9.cells.nest
import pype9.cells.neuron


class TestCell(TestCase):

    def _test_load_describe(self, loader):
        CellType = loader(os.path.join(test_data_dir, 'xml',
                                       'HodgkinHuxley.xml'))
        cell = CellType()
        cell.describe()

    def test_neuron_load_describe(self):
        self._test_load_describe(pype9.cells.neuron.load_celltype)

    def test_nest_load_describe(self):
        self._test_load_describe(pype9.cells.nest.load_celltype)
