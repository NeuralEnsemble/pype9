if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport
from sympy import sympify
from nineml import units as un
from pype9.neuron.utils import UnitAssigner
from nineml.abstraction import (
    Dynamics, AnalogReceivePort, Parameter, Regime)
import numpy


class TestUnitAssignment(TestCase):

    def setUp(self):
        a = Dynamics(
            name='A',
            aliases=['A1 := P1 / P2', 'A2 := ARP2 + P3', 'A3 := P4 * P5',
                     'A4 := 1 / (P2 * P6) + ARP3'],
            regimes=[
                Regime('dSV1/dt = -A1 / A2',
                       name='R1')],
            analog_ports=[AnalogReceivePort('ARP1', dimension=un.resistance),
                          AnalogReceivePort('ARP2', dimension=un.charge),
                          AnalogReceivePort('ARP3',
                                            dimension=un.conductanceDensity)],
            parameters=[Parameter('P1', dimension=un.voltage),
                        Parameter('P2', dimension=un.resistance),
                        Parameter('P3', dimension=un.charge),
                        Parameter('P4', dimension=un.length / un.current ** 2),
                        Parameter('P5', dimension=un.current ** 2 / un.length),
                        Parameter('P6', dimension=un.length ** 2)]
        )
        self.assigner = UnitAssigner(a)

    def test_conversions(self):
        for unit in [un.mV / un.uF,
                     un.ms * un.C / un.um,
                     un.K ** 2 / (un.uF * un.mV ** 2),
                     un.uF ** 3 / un.um,
                     un.cd / un.A]:
            scale, compound = UnitAssigner.dimension_to_units(unit.dimension)
            inv_scale = numpy.sum([p * u.power for u, p in compound])
            self.assertEquals(scale + inv_scale, 0,
                              "Scale doesn't match in unit conversion")
            x = numpy.sum(numpy.array([numpy.array(list(u.dimension)) * p
                                       for u, p in compound]), axis=0)
            self.assertEquals(list(unit.dimension), list(x),
                              "Dimensions do not match original conversion")

    def test_scaling(self):
        self.assertEquals(self.assigner.assign_units_to_element('A2'),
                          (sympify('ARP2 + P3'), 'ms nA'))
        self.assertEquals(self.assigner.assign_units_to_element('P2'),
                          (sympify('P2'), '/uS'))
        self.assertEquals(self.assigner.assign_units_to_element('P6'),
                          (sympify('P6'), 'um2'))
        self.assertEquals(self.assigner.assign_units_to_element('A4'),
                          (sympify('ARP3 + 100/(P2*P6)'), 'S/cm2'))
