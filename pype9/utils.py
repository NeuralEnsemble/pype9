"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
import os
import errno
import quantities as pq
from pype9.exceptions import Pype9RuntimeError
import numpy
import nineml
from quantities import Quantity
from nineml import (
    Unit, Dynamics, ConnectionRule, RandomDistribution,
    DynamicsProperties, ConnectionRuleProperties,
    RandomDistributionProperties, Definition)
from nineml.user import Property
from copy import copy
from nineml.exceptions import NineMLMissingElementError
import math


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


def convert_to_property(name, qty_pq):
    qty9 = pq29_quantity(qty_pq)
    return nineml.Property(name, qty9.name, qty9.value)


def pq29_quantity(qty):
    if isinstance(qty, (int, float)):
        units = nineml.units.unitless
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
        dimension = nineml.Dimension(unit_name + 'Dimension', **powers)
        units = nineml.Unit(unit_name, dimension=dimension,
                            power=float(math.log10(qty.units.simplified)))
    else:
        raise Pype9RuntimeError(
            "Cannot '{}' to nineml.Property (can only convert "
            "quantities.Quantity and numeric objects)"
            .format(qty))
    return nineml.user.component.Quantity(float(qty), units)


def convert_to_quantity(prop):
    units = prop.units
    dim = units.dimension
    return prop.value * 10 ** units.power * (pq.s ** dim.t *
                                             pq.kg ** dim.m *
                                             pq.m ** dim.l *
                                             pq.mole ** dim.n *
                                             pq.K ** dim.k *
                                             pq.cd ** dim.j *
                                             pq.A ** dim.i)


def load_9ml_prototype(url_or_comp, default_value=0.0, override_name=None,
                       saved_name=None, **kwargs):  # @UnusedVariable
    """
    Reads a component from file, checking to see if there is only one
    component or component class in the file (or not reading from file at
    all if component is already a component or component class).
    """
    if isinstance(url_or_comp, str):
        # Interpret the given prototype as a URL of a NineML prototype
        url = url_or_comp
        # Read NineML description
        document = nineml.read(url)
        if saved_name is not None:
            try:
                prototype = document[saved_name]
            except NineMLMissingElementError:
                raise Pype9RuntimeError(
                    "Could not find a component named '{}' at the url '{}' "
                    "(found '{}')."
                    .format(saved_name, url,
                            "', '".join(nineml.read(url).iterkeys())))
        else:
            components = list(document.components)
            if len(components) == 1:
                prototype = components[0]
            else:
                if len(components) > 1:
                    componentclasses = set((c.component_class
                                            for c in components))
                else:
                    componentclasses = list(document.componentclasses)
                if len(componentclasses) == 1:
                    prototype = componentclasses[0]
                elif len(componentclasses) > 1:
                    raise Pype9RuntimeError(
                        "Multiple component and or classes ('{}') loaded "
                        "from nineml path '{}'"
                        .format("', '".join(
                            c.name for c in document.components), url))
                else:
                    raise Pype9RuntimeError(
                        "No components or component classes loaded from "
                        "nineml" " path '{}'".format(url))
    elif isinstance(url_or_comp, nineml.abstraction.Dynamics):
        componentclass = url_or_comp
        definition = Definition(componentclass)
        properties = []
        for param in componentclass.parameters:
            properties.append(Property(
                name=param.name, value=default_value,
                units=Unit(
                    ('unit' + param.dimension.name),
                    dimension=param.dimension, power=0)))
        if isinstance(componentclass, Dynamics):
            ComponentType = DynamicsProperties
        elif isinstance(componentclass, ConnectionRule):
            ComponentType = ConnectionRuleProperties
        elif isinstance(componentclass, RandomDistribution):
            ComponentType = RandomDistributionProperties
        prototype = ComponentType(name=componentclass.name + 'Properties',
                                  definition=definition,
                                  properties=properties)
    elif isinstance(url_or_comp, nineml.user.Component):
        prototype = copy(url_or_comp)
    else:
        raise Pype9RuntimeError(
            "Can't load 9ML prototype from '{}' object".format(url_or_comp))
    if override_name is not None:
        prototype.name = override_name
    return prototype

