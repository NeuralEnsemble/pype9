if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport
from nineml import units as un
from pype9.neuron.utils import (
    unit_mapper as neuron_unit_mapper, ExpressionUnitScaler)
from nineml.abstraction import (
    Dynamics, AnalogReceivePort, Parameter, Regime)
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


class TestUnitScaler(TestCase):

    def setUp(self):
        a = Dynamics(
            name='A',
            aliases=['A1:=P1 / P2', 'A2 := ARP2 + P3', 'A3 := P4 * P5'],
            regimes=[
                Regime('dSV1/dt = -A1 / A2',
                       name='R1')],
            analog_ports=[AnalogReceivePort('ARP1', dimension=un.resistance),
                          AnalogReceivePort('ARP2', dimension=un.charge)],
            parameters=[Parameter('P1', dimension=un.voltage),
                        Parameter('P2', dimension=un.resistance),
                        Parameter('P3', dimension=un.charge),
                        Parameter('P4', dimension=un.length / un.current ** 2),
                        Parameter('P5', dimension=un.current ** 2 / un.length)]
        )
        self.scaler = ExpressionUnitScaler(a)

    def test_scaling(self):
        print self.scaler.scale_expression('A2')
