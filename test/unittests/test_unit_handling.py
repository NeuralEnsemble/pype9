if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport
import os.path
from sympy import sympify
from nineml import units as un
from pype9.base.units import UnitHandler as BaseUnitHandler
from nineml.abstraction import (
    Dynamics, AnalogReceivePort, Parameter, Regime, Expression)
import numpy
from nineml.user import Quantity


class TestUnitHandler(BaseUnitHandler):

    basis = [un.ms, un.mV, un.nA, un.mM, un.nF, un.um, un.uS, un.K, un.cd]
    compounds = [un.uF_per_cm2, un.S_per_cm2, un.pF_per_nA]
    unit_name_map = {un.ms: 'ms', un.mV: 'mV', un.nA: 'nA', un.mM: 'mM',
                     un.nF: 'nF', un.um: 'um', un.uS: 'uS', un.K: 'K',
                     un.cd: 'cd', un.uF_per_cm2: 'uF/cm2',
                     un.S_per_cm2: 'S/cm2', un.pF_per_nA: 'pF/nA'}

    A, cache, si_lengths = BaseUnitHandler._load_basis_matrices_and_cache(
        basis, os.path.dirname(__file__))

    def _units_for_code_gen(self, units):
        return self.compound_to_units_str(units, mult_symbol='*')


class TestUnitAssignment(TestCase):

    test_units = [un.mV / un.uF,
                  un.ms * un.C / un.um,
                  un.K ** 2 / (un.uF * un.mV ** 2),
                  un.uF ** 3 / un.um,
                  un.cd / un.A]

    def setUp(self):
        self.a = Dynamics(
            name='A',
            aliases=['A1 := P1 / P2', 'A2 := ARP2 + P3', 'A3 := P4 * P5',
                     'A4 := 1 / (P2 * P6) + ARP3', 'A5 := P7 * P8',
                     'A6 := 1 / (P6 * P9)'],
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
                        Parameter('P6', dimension=un.length ** 2),
                        Parameter('P7', dimension=un.current / un.capacitance),
                        Parameter('P8', dimension=un.time),
                        Parameter('P9',
                                  dimension=un.length ** 2 / un.capacitance)]
        )
        # Create an instance of the type
        self.handler = TestUnitHandler(self.a)

    def test_conversions(self):
        for unit in self.test_units:
            scale, compound = TestUnitHandler.dimension_to_units_compound(
                unit.dimension)
            new_scale = numpy.sum([p * u.power for u, p in compound])
            self.assertEquals(scale - new_scale, 0,
                              "Scale doesn't match in unit conversion of unit "
                              "'{}': orig={}, inverted={}".format(unit, scale,
                                                                  new_scale))
            x = numpy.sum(numpy.array([numpy.array(list(u.dimension)) * p
                                       for u, p in compound]), axis=0)
            self.assertEquals(list(unit.dimension), list(x),
                              "Dimensions do not match original conversion of "
                              "unit '{}'".format(unit))

    def test_scaling(self):
        self.assertEquals(self.handler.scale_expression('A2'),
                          (Expression('ARP2 + P3'), 'ms*nA'))
        self.assertEquals(self.handler.scale_expression('A4'),
                          (Expression('ARP3 + 100/(P2*P6)'), 'S/cm2'))
        self.assertEquals(self.handler.scale_expression('A5'),
                          (Expression('1e-6 * P7 * P8'), 'mV'))
        self.assertEquals(self.handler.scale_expression('A6'),
                          (Expression('1/P9'), 'mV'))

    def test_assignment(self):
        self.assertEquals(self.handler.assign_units_to_variable('P2'), '1/uS')
        self.assertEquals(self.handler.assign_units_to_variable('P6'), 'um2')

    def test_pq_round_trip(self):
        for unit in self.test_units:
            qty = Quantity(1.0, unit)
            pq_qty = TestUnitHandler.to_pq_quantity(qty)
            new_qty = TestUnitHandler.from_pq_quantity(pq_qty)
            self.assertEquals(qty.units.dimension, new_qty.units.dimension,
                              "Python-quantities roundtrip of '{}' changed "
                              "dimension".format(unit.name))
            self.assertEquals(qty.value * 10 ** qty.units.power,
                              new_qty.value * 10 ** new_qty.units.power,
                              "Python-quantities roundtrip of '{}' changed "
                              "scale".format(unit.name))
