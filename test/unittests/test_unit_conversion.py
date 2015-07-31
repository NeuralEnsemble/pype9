if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport
from nineml import units as un
from pype9.nest.utils import unit_mapper as nest_unit_mapper
from pype9.neuron.utils import unit_mapper as neuron_unit_mapper
import numpy


class TestUnitConversion(TestCase):

    def test_conversions(self):
        for unit in [un.mV / un.uF,
                     un.ms * un.C / un.um,
                     un.K ** 2 / (un.uF * un.mV ** 2),
                     un.uF ** 3 / un.um,
                     un.cd / un.A]:
            scale, compound = neuron_unit_mapper.map_to_units(unit.dimension)
            inv_scale = numpy.sum([p * u.power for u, p in compound])
            self.assertEquals(scale + inv_scale, 0,
                              "Scale doesn't match in unit conversion")
            x = numpy.sum(numpy.array([numpy.array(list(u.dimension)) * p
                                       for u, p in compound]), axis=0)
            self.assertEquals(list(unit.dimension), list(x),
                              "Dimensions do not match original conversion")
