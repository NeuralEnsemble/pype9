#!/usr/bin/env python
import os.path
import math
from nineml import units as un
from pype9.simulate.common.units import UnitHandler as BaseUnitHandler
from pype9.simulate.nest.units import UnitHandler as NestUnitHandler
from nineml.abstraction import (
    Dynamics, AnalogReceivePort, Parameter, Regime, Expression, Constant,
    StateVariable)
import numpy
from nineml.units import Quantity
if __name__ == '__main__':
    from pype9.utils.testing import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport


class TestUnitHandler1(BaseUnitHandler):

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


class TestUnitHandler2(BaseUnitHandler):

    basis = [un.ms, un.mV, un.pA, un.mM, un.uF, un.um, un.uS, un.K, un.cd]
    compounds = []

    unit_name_map = {un.ms: 'ms', un.mV: 'mV', un.pA: 'pA', un.mM: 'mM',
                     un.uF: 'nF', un.um: 'um', un.uS: 'uS', un.K: 'K',
                     un.cd: 'cd'}

    (A, cache,
     cache_path, si_lengths) = BaseUnitHandler._load_basis_matrices_and_cache(
        basis, compounds, os.path.dirname(__file__))

    def _units_for_code_gen(self, units):
        return self.compound_to_units_str(
            units, mult_symbol='*', pow_symbol='^', use_parentheses=False)


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
                       ('dSV2/dt = C1 * SV2 ** 2 + C2 * SV2 + C3 + SV3 + '
                        'ARP4 / P11'),
                       'dSV3/dt = P12*(SV2*P13 - SV3)',
                       name='R1')],
            state_variables=[StateVariable('SV1', dimension=un.dimensionless),
                             StateVariable('SV2', dimension=un.voltage),
                             StateVariable('SV3',
                                           dimension=un.voltage / un.time)],
            analog_ports=[AnalogReceivePort('ARP1', dimension=un.resistance),
                          AnalogReceivePort('ARP2', dimension=un.charge),
                          AnalogReceivePort('ARP3',
                                            dimension=un.conductanceDensity),
                          AnalogReceivePort('ARP4', dimension=un.current)],
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
                                  dimension=un.conductance / un.length ** 2),
                        Parameter('P11', dimension=un.capacitance),
                        Parameter('P12', dimension=un.per_time),
                        Parameter('P13', dimension=un.per_time)],
            constants=[Constant('C1', 0.04, units=(un.unitless /
                                                   (un.mV * un.ms))),
                       Constant('C2', 5.0, units=un.unitless / un.ms),
                       Constant('C3', 140.0, units=un.mV / un.ms)]
        )

    def test_dimension_to_units(self):
        test_units = {un.mV / un.uF: un.mV / un.nF,
                      un.mV / un.ms: un.mV / un.ms,
                      un.nA / un.pF: un.mV / un.ms,
                      un.cd / un.A: un.cd / un.nA,
                      un.A / un.uF: un.nA / un.nF,
                      un.nF / (un.m ** 2 * un.s): un.S / un.cm ** 2}
        TestUnitHandler1.clear_cache()
        for unit, unit_mapped in test_units.iteritems():
            new_unit = TestUnitHandler1.dimension_to_units(unit.dimension)
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
            scale, compound = TestUnitHandler1.dimension_to_units_compound(
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
        handler1 = TestUnitHandler1(self.a)
        handler2 = NestUnitHandler(self.a)
        self.assertEqual(handler1.scale_alias('A2'),
                         (Expression('ARP2 + P3'), 'ms*nA'))
        self.assertEqual(handler1.scale_alias('A4'),
                         (Expression('ARP3 + 100/(P2*P6)'), 'S/cm2'))
        self.assertEqual(handler1.scale_alias('A5'),
                         (Expression('P7 * P8'), 'mV'))
        self.assertEqual(handler1.scale_alias('A6'),
                         (Expression('1e-3 * P9/P10'), 'ms'))
        self.assertEqual(
            handler2.scale_time_derivative(self.a.regime('R1').element('SV2')),
            (Expression('C1 * SV2 ** 2 + C2 * SV2 + C3 + SV3 + '
                        'ARP4 / P11'), 'mV/ms'))
        self.assertEqual(
            handler2.scale_time_derivative(self.a.regime('R1').element('SV3')),
            (Expression('P12*(SV2*P13 - SV3)'), 'mV/ms^2'))
        self.assertEqual(handler1.assign_units_to_variable('P2'), '1/uS')
        self.assertEqual(handler1.assign_units_to_variable('P6'), 'um^2')

    def test_pq_round_trip(self):
        for unit in self.test_units:
            qty = Quantity(1.0, unit)
            pq_qty = TestUnitHandler1.to_pq_quantity(qty)
            new_qty = TestUnitHandler1.from_pq_quantity(pq_qty)
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
    tester.test_scaling_and_assignment()
