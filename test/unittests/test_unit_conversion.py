if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport
from nineml import units as un
from pype9.nest.utils import UnitConverter as NestUnitConverter
from pype9.neuron.utils import UnitConverter as NeuronUnitConverter


class TestUnitConversion(TestCase):

    def setUp(self):
        self.neuron = NeuronUnitConverter()
        self.nest = NestUnitConverter()

    def test_conversions(self):
        for unit in [un.mV / un.uF,
                     un.ms * un.C / un.um,
                     un.K ** 2 / (un.uF * un.mV ** 2),
                     un.uF ** 3 / un.um,
                     un.cd / un.A]:
            scale, units = self.neuron.scale(unit)
            print unit, units, scale

if __name__ == '__main__':
    test = TestUnitConversion()
    test.test_conversions()
