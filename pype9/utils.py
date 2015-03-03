"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
import os
import errno
import nineml
import quantities as pq
from pype9.exceptions import Pype9RuntimeError


def remove_ignore_missing(path):
    try:
        os.remove(path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def ensure_camel_case(name):
    if len(name) < 2:
        raise Exception("The name ('{}') needs to be at least 2 letters long"
                        "to enable the capitalized version to be different "
                        "from upper case version".format(name))
    if name == name.lower() or name == name.upper():
        name = name.title()
    return name


class abstractclassmethod(classmethod):

    __isabstractmethod__ = True

    def __init__(self, callable_method):
        callable_method.__isabstractmethod__ = True
        super(abstractclassmethod, self).__init__(callable_method)


def convert_to_property(name, qty):
    if isinstance(qty, (int, float)):
        units = nineml.abstraction_layer.units.unitless
    elif isinstance(qty, pq.Quantity):
        unit_name = str(qty.units).split()[1]
        powers = {}
        for si_unit, power in qty.units.simplified._dimensionality.iteritems():
            if isinstance(si_unit, pq.UnitMass):
                powers['m'] = power
            elif isinstance(si_unit, pq.UnitLength):
                powers['l'] = power
            elif isinstance(si_unit, pq.UnitTime):
                powers['t'] = power
            elif isinstance(si_unit, pq.UnitCurrent):
                powers['i'] = power
            elif isinstance(si_unit, pq.UnitLuminousIntensity):
                powers['j'] = power
            elif isinstance(si_unit, pq.UnitSubstance):
                powers['n'] = power
            elif isinstance(si_unit, pq.UnitTemperature):
                powers['k'] = power
            else:
                assert False, "Unrecognised units '{}'".format(si_unit)
        units = nineml.Unit(unit_name, **powers)
    else:
        raise Pype9RuntimeError(
            "Cannot '{}' to nineml.Property (can only convert "
            "quantities.Quantity and numeric objects)"
            .format(qty))
    return nineml.Property(name, float(qty), units)


def convert_to_quantity(prop):
    units = prop.units
    return prop.value * (pq.s ** units.t *
                         pq.kg ** units.m *
                         pq.m ** units.l *
                         pq.mole ** units.n *
                         pq.K ** units.k *
                         pq.cd ** units.j *
                         pq.A ** units.i)
