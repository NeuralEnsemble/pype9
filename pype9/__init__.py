"""

  This package aims to contain all extensions to the pyNN package required for
  interpreting networks specified in NINEML+. It is possible that some changes
  will need to be made in the pyNN package itself (although as of 13/6/2012
  this hasn't been necessary).

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
import os
import xml.sax
import time
import numpy
import nineml.user_layer
from quantities import Quantity
from quantities.dimensionality import Dimensionality

version = "0.1"

DEFAULT_V_INIT = -65.0


def create_unit_conversions(basic_conversions, compound_conversions):
    basic_dict = {}
    for SI_unit, pyNN_unit in basic_conversions:
        # The units are simplified (converted into from the unit strings into
        # SI "quantity" units, which may)
        basic_dict[Quantity(
            1, SI_unit).simplified._dimensionality] = Quantity(1, pyNN_unit)
    compound_dict = {}
    for SI_unit_tple, nl_unit_tple in compound_conversions:
        simplified_SI = []
        nl_unit = 1.0
        for SI_cmp, nl_cmp in zip(SI_unit_tple, nl_unit_tple):
            simplified_SI.append(
                (Quantity(1, SI_cmp[0]).simplified._dimensionality, SI_cmp[1]))
            nl_unit *= pow(Quantity(1, nl_cmp[0]), nl_cmp[1])
        compound_dict[tuple(sorted(simplified_SI))] = nl_unit
    return basic_dict, compound_dict


def convert_units(value, unit_str, basic_dict, compound_dict):
    # FIXME a little hack until Ivan tidies up the units in NeMo to be more
    # standardised.
    if unit_str == 'uf/cm2':
        unit_str = 'uF/cm^2'
    if isinstance(value, Quantity):
        quantity = value
        assert unit_str is None
    else:
        # Convert to a quantity with units
        quantity = Quantity(value, unit_str)
    # Check to see if the units are basic units (i.e. dimensionality == 1)
    if len(quantity._dimensionality) == 1:
        try:
            units = basic_dict[quantity.simplified._dimensionality]
        except KeyError:
            raise Exception(
                "No PyNN conversion for '{}' units".format(quantity.units))
    else:
        # Convert compound units into their simplified forms
        simplified_units = []
        for unit_comp, exponent in quantity._dimensionality.iteritems():
            simplified_units.append(
                (unit_comp.simplified._dimensionality, exponent))
        try:
            units = compound_dict[tuple(sorted(simplified_units))]
        # If there isn't an explicit compound conversion, try to use
        # combination of basic conversions
        except KeyError:
            units = Quantity(1.0, 'dimensionless')
            for unit_dim, exponent in simplified_units:
                try:
                    conv_units = basic_dict[unit_dim]
                except KeyError:
                    raise Exception("No PyNN conversion for '{}' units"
                                    .format(quantity.units))
                units *= pow(conv_units, exponent)
    quantity.units = units
    # Check to see if is a proper array (with multiple dimensions) or just a
    # 0-d array created by the quantity conversion.
    if quantity.shape:
        converted_quantity = numpy.asarray(quantity)
    else:
        converted_quantity = float(quantity)
    return converted_quantity, quantity.units
