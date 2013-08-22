from __future__ import absolute_import
import numpy
from quantities import Quantity
from quantities.dimensionality import Dimensionality

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


def _create_unit_conversions():
    basic_conversions = {}
    for SI_unit, pyNN_unit in _basic_SI_to_pyNN_conversions:
        # The units are simplified (converted into from the unit strings into SI "quantity" units,
        # which may)
        basic_conversions[Quantity(1, SI_unit).simplified._dimensionality] = Quantity(1, pyNN_unit)
    compound_conversions = {}
    for SI_unit_tple, nl_unit_tple in _compound_SI_to_pyNN_conversions:
        simplified_SI = []
        nl_unit = 1.0
        for SI_cmp, nl_cmp in zip(SI_unit_tple, nl_unit_tple):
            simplified_SI.append((Quantity(1, SI_cmp[0]).simplified._dimensionality,
                                   SI_cmp[1]))
            nl_unit *= pow(Quantity(1, nl_cmp[0]), nl_cmp[1])
        compound_conversions[tuple(simplified_SI)] = nl_unit
    return basic_conversions, compound_conversions

_basic_unit_conversions, _compound_unit_conversions = _create_unit_conversions()


def convert_to_pyNN_units(value, unit_str):
    # Convert to a quantity with units
    quantity = Quantity(value, unit_str)
    # Check to see if the units are basic units (i.e. dimensionality == 1)
    if len(quantity._dimensionality) == 1:
        try:
            units = _basic_unit_conversions[quantity.simplified._dimensionality]
        except KeyError:
            raise Exception("No PyNN conversion for '{}' units".format(quantity.units))
    else:
        # Convert compound units into their simplified forms
        simplified_units = []
        for unit_comp, exponent in quantity._dimensionality.iteritems():
            simplified_units.append((unit_comp.simplified._dimensionality, exponent))
        try:
            units = _compound_unit_conversions[tuple(simplified_units)]
        except KeyError: # If there isn't an explicit compound conversion, try to use combination of basic conversions
            units = 1.0
            for unit_dim, exponent in simplified_units:
                try:
                    conv_units = _basic_unit_conversions[unit_dim]
                except KeyError:
                    raise Exception("No PyNN conversion for '{}' units".format(quantity.units))
                units *= pow(conv_units, exponent)
    quantity.units = units
    # Check to see if is a proper array (with multiple dimensions) or just a 0-d array created by 
    # the quantity conversion.
    if quantity.shape:
        converted_quantity = numpy.asarray(quantity)
    else:
        converted_quantity = float(quantity)
    return converted_quantity, quantity.units

