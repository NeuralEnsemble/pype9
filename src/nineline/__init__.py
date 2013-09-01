"""

  This package aims to contain all extensions to the pyNN package required for interpreting 
  networks specified in NINEML+. It is possible that some changes will need to be made in the 
  pyNN package itself (although as of 13/6/2012 this hasn't been necessary).
  
  @file ncml.py
  @author Tom Close

"""

#######################################################################################
#
#    Copyright 2012 Okinawa Institute of Science and Technology (OIST), Okinawa, Japan
#
#######################################################################################
import os
import xml.sax
import time
import numpy
import nineml.user_layer
from quantities import Quantity
from quantities.dimensionality import Dimensionality

__version__ = "0.0.1"  

def create_unit_conversions(basic_conversions, compound_conversions):
    basic_dict = {}
    for SI_unit, pyNN_unit in basic_conversions:
        # The units are simplified (converted into from the unit strings into SI "quantity" units,
        # which may)
        basic_dict[Quantity(1, SI_unit).simplified._dimensionality] = Quantity(1, pyNN_unit)
    compound_dict = {}
    for SI_unit_tple, nl_unit_tple in compound_conversions:
        simplified_SI = []
        nl_unit = 1.0
        for SI_cmp, nl_cmp in zip(SI_unit_tple, nl_unit_tple):
            simplified_SI.append((Quantity(1, SI_cmp[0]).simplified._dimensionality,
                                   SI_cmp[1]))
            nl_unit *= pow(Quantity(1, nl_cmp[0]), nl_cmp[1])
        compound_dict[tuple(simplified_SI)] = nl_unit
    return basic_dict, compound_dict


def convert_units(value, unit_str, basic_dict, compound_dict):
    #FIXME a little hack until Ivan tidies up the units in NeMo to be more standardised.
    if unit_str == 'uf/cm2':
        unit_str = 'uF/cm^2' 
    # Convert to a quantity with units
    quantity = Quantity(value, unit_str)
    # Check to see if the units are basic units (i.e. dimensionality == 1)
    if len(quantity._dimensionality) == 1:
        try:
            units = basic_dict[quantity.simplified._dimensionality]
        except KeyError:
            raise Exception("No PyNN conversion for '{}' units".format(quantity.units))
    else:
        # Convert compound units into their simplified forms
        simplified_units = []
        for unit_comp, exponent in quantity._dimensionality.iteritems():
            simplified_units.append((unit_comp.simplified._dimensionality, exponent))
        try:
            units = compound_dict[tuple(simplified_units)]
        except KeyError: # If there isn't an explicit compound conversion, try to use combination of basic conversions
            units = 1.0
            for unit_dim, exponent in simplified_units:
                try:
                    conv_units = basic_dict[unit_dim]
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

# class XMLHandler(xml.sax.handler.ContentHandler):
# 
#     def __init__(self):
#         self._open_components = []
#         self._required_attrs = []
# 
#     def characters(self, data):
#         pass
# 
#     def endElement(self, name):
#         """
#         Closes a component, removing its name from the _open_components list. 
#         
#         WARNING! Will break if there are two tags with the same name, with one inside the other and 
#         only the outer tag is opened and the inside tag is differentiated by its parents
#         and attributes (this would seem an unlikely scenario though). The solution in this case is 
#         to open the inside tag and do nothing. Otherwise opening and closing all components 
#         explicitly is an option.
#         """
#         if self._open_components and name == self._open_components[-1]:
#             self._open_components.pop()
#             self._required_attrs.pop()
# 
#     def _opening(self, tag_name, attr, ref_name, parents=[], required_attrs=[]):
#         if tag_name == ref_name and self._parents_match(parents, self._open_components) and \
#                 all([(attr[key] == val or val == None) for key, val in required_attrs]):
#             self._open_components.append(ref_name)
#             self._required_attrs.append(required_attrs)
#             return True
#         else:
#             return False
# 
#     def _closing(self, tag_name, ref_name, parents=[], required_attrs=[]):
#         if tag_name == ref_name and self._parents_match(parents, self._open_components[:-1]) and \
#                 self._required_attrs[-1] == required_attrs:
#             return True
#         else:
#             return False
# 
#     def _parents_match(self, required_parents, open_parents):
#         if len(required_parents) > len(open_parents):
#             return False
#         for required, open in zip(reversed(required_parents), reversed(open_parents)):
#             if isinstance(required, str):
#                 if required != open:
#                     return False
#             else:
#                 try:
#                     if not any([ open == r for r in required]):
#                         return False
#                 except TypeError:
#                     raise Exception("Elements of the 'required_parents' argument need to be " \
#                                     "either strings or lists/tuples of strings")
#         return True
