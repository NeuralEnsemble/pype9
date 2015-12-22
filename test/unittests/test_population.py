#!/usr/bin/env python
from pype9.neuron.network import PyNNCellWrapperMetaClass
import ninemlcatalog
if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport


class TestPopulation(TestCase):

    def test_neuron(self):
        exc = ninemlcatalog.load('/network/Brunel2000/AI', 'Exc')
