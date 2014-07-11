"""
    A module contain unit tests for the nine cells package
"""
try:
    import unittest2 as unittest
except ImportError:
    import unittest

import os
from mock import Mock
from numpy.testing import assert_array_equal, assert_array_almost_equal
import nineline.cells.nest
import nineline.cells.neuron


class TestCell(unittest.TestCase):

    def _test_load_describe(self, loader):
        CellType = loader('Granule_DeSouza10',
                          '/home/tclose/git/kbrain/xml/cerebellum/ncml/Granule_DeSouza10.xml')
        cell = CellType()
        cell.describe()

    def test_neuron_load_describe(self):
        self._test_load_describe(nineline.cells.neuron.load_celltype)

    def test_nest_load_describe(self):
        self._test_load_describe(nineline.cells.nest.load_celltype)
