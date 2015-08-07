if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport
import os.path
import math
from nineml import units as un
from pype9.base.units import UnitHandler as BaseUnitHandler
from nineml.abstraction import (
    Dynamics, AnalogReceivePort, Parameter, Regime, Expression)
import numpy
from nineml.user import Quantity


class TestUnitHandler(BaseUnitHandler):

    basis = [un.ms, un.mV, un.nA, un.mM, un.nF, un.um, un.uS, un.K, un.cd]
    compounds = [un.uF_per_cm2, un.S_per_cm2]
    unit_name_map = {un.ms: 'ms', un.mV: 'mV', un.nA: 'nA', un.mM: 'mM',
                     un.nF: 'nF', un.um: 'um', un.uS: 'uS', un.K: 'K',
                     un.cd: 'cd', un.uF_per_cm2: 'uF/cm2',
                     un.S_per_cm2: 'S/cm2'}

    (A, cache,
     cache_path, si_lengths) = BaseUnitHandler._load_basis_matrices_and_cache(
        basis, compounds, os.path.dirname(__file__))

    def _units_for_code_gen(self, units):
        return self.compound_to_units_str(units, mult_symbol='*',
                                          pow_symbol='^')


class TestUnitAssignment(TestCase):

    test_units = [un.mV / un.uF,
                  un.ms * un.C / un.um,
                  un.K ** 2 / (un.uF * un.mV ** 2),
                  un.uF ** 3 / un.um,
                  un.cd / un.A]

    test_unit_mapped = [un.mV / un.uF,
                        un.ms * un.C / un.um,
                        un.K ** 2 / (un.uF * un.mV ** 2),
                        un.uF ** 3 / un.um,
                        un.cd / un.A]

    def setUp(self):
        self.a = Dynamics(
            name='A',
            aliases=['A1 := P1 / P2', 'A2 := ARP2 + P3', 'A3 := P4 * P5',
                     'A4 := 1 / (P2 * P6) + ARP3', 'A5 := P7 * P8',
                     'A6 := P9/P10'],
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
                                  dimension=un.capacitance / un.length ** 2),
                        Parameter('P10',
                                  dimension=un.conductance / un.length ** 2)]
        )

    def test_dimension_to_units(self):
        test_units = {un.mV / un.uF: un.mV / un.nF,
                      un.mV / un.ms: un.mV / un.ms,
                      un.nA / un.pF: un.mV / un.ms,
                      un.cd / un.A: un.cd / un.nA,
                      un.A / un.uF: un.nA / un.nF,
                      un.nF / (un.m ** 2 * un.s): un.S / un.cm ** 2}
        TestUnitHandler.clear_cache()
        for unit, unit_mapped in test_units.iteritems():
            new_unit = TestUnitHandler.dimension_to_units(unit.dimension)
            self.assertEqual(new_unit, unit_mapped,
                             "New unit mapped incorrectly {}->{} ({})"
                             .format(unit, new_unit, unit_mapped))

    def test_conversions(self):
        test_units = [un.mV / un.uF,
                      un.ms * un.C / un.um,
                      un.K ** 2 / (un.uF * un.mV ** 2),
                      un.uF ** 3 / un.um,
                      un.cd / un.A]
        for unit in test_units:
            scale, compound = TestUnitHandler.dimension_to_units_compound(
                unit.dimension)
            new_scale = numpy.sum([p * u.power for u, p in compound])
            self.assertEqual(scale - new_scale, 0,
                              "Scale doesn't match in unit conversion of unit "
                              "'{}': orig={}, inverted={}".format(unit, scale,
                                                                  new_scale))
            x = numpy.sum(numpy.array([numpy.array(list(u.dimension)) * p
                                       for u, p in compound]), axis=0)
            self.assertEqual(list(unit.dimension), list(x),
                             "Dimensions do not match original conversion of "
                             "unit '{}'".format(unit))

    def test_scaling_and_assignment(self):
        handler = TestUnitHandler(self.a)
        self.assertEqual(handler.scale_expression('A2'),
                         (Expression('ARP2 + P3'), 'ms*nA'))
        self.assertEqual(handler.scale_expression('A4'),
                         (Expression('ARP3 + 100/(P2*P6)'), 'S/cm2'))
        self.assertEqual(handler.scale_expression('A5'),
                         (Expression('P7 * P8'), 'mV'))
        self.assertEqual(handler.scale_expression('A6'),
                         (Expression('1e-3 * P9/P10'), 'ms'))
        self.assertEqual(handler.assign_units_to_variable('P2'), '1/uS')
        self.assertEqual(handler.assign_units_to_variable('P6'), 'um^2')

    def test_pq_round_trip(self):
        for unit in self.test_units:
            qty = Quantity(1.0, unit)
            pq_qty = TestUnitHandler.to_pq_quantity(qty)
            new_qty = TestUnitHandler.from_pq_quantity(pq_qty)
            self.assertEqual(qty.units.dimension, new_qty.units.dimension,
                             "Python-quantities roundtrip of '{}' changed "
                             "dimension".format(unit.name))
            new_power = int(math.log10(new_qty.value) + new_qty.units.power)
            self.assertEqual(unit.power, new_power,
                             "Python-quantities roundtrip of '{}' changed "
                             "scale ({} -> {})".format(unit.name, unit.power,
                                                       new_power))

if __name__ == '__main__':
    tester = TestUnitAssignment()
    tester.test_dimension_to_units()
