from __future__ import absolute_import
import numpy
from .. import create_unit_conversions, convert_units


_basic_SI_to_pyNN_conversions = (('s', 'ms'),
                                 ('V', 'mV'),
                                 ('A', 'nA'),
                                 ('S', 'uS'),
                                 ('F', 'nF'),
                                 ('m', 'um'),
                                 ('Hz', 'Hz'),
                                 ('Ohm', 'MOhm'),
                                 ('M', 'mM'))

_compound_SI_to_pyNN_conversions = (((('A', 1), ('m', -2)), (('mA', 1), ('cm', -2))),
                                    ((('F', 1), ('m', -2)), (('uF', 1), ('cm', -2))),
                                    ((('S', 1), ('m', -2)), (('S', 1), ('cm', -2))))


_basic_unit_dict, _compound_unit_dict = create_unit_conversions(_basic_SI_to_pyNN_conversions,
                                                                _compound_SI_to_pyNN_conversions)


def convert_to_pyNN_units(value, unit_str):
    return convert_units(value, unit_str, _basic_unit_dict, _compound_unit_dict)
