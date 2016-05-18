"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
from itertools import chain

_REQUIRED_SIM_PARAMS = ['timestep', 'min_delay', 'max_delay', 'temperature']


class PyNNCellWrapper(object):

    """
    A base cell object for PyNNCellWrapper cell classes.
    """

    @classmethod
    def get_parameter_names(cls):
        """
        Returns a list of parameters that can be set for the Cell class.

        @return [list(str)]: The list of parameter names in the class
        """
        return cls.parameter_names


class PyNNCellWrapperMetaClass(type):

    """
    Metaclass for building NineMLCellType subclasses
    Called by nineml_celltype_from_model
    """

    def __new__(cls, celltype_id, bases, dct):  # @NoSelf
        # Retrieved parsed model (it is placed in dct to conform with
        # with the standard structure for the "__new__" function of
        # metaclasses).
        component_class = dct['model'].component_class
        default_properties = dct['default_properties']  # @UnusedVariable
        initial_state = dct['initial_state']  # @UnusedVariable
        dct['model_name'] = celltype_id
        dct['parameter_names'] = tuple(component_class.parameter_names)
        dct['recordable'] = tuple(chain(('spikes',),
                                        component_class.send_port_names,
                                        component_class.state_variable_names))
        dct['receptor_types'] = tuple(component_class.event_receive_port_names)
        dct["default_parameters"] = dict(
            (p.name, (
                cls.UnitHandler.scale_value(p.quantity)
                if p.value.nineml_type == 'SingleValue' else float('nan')))
            for p in default_properties)
        dct["default_initial_values"] = dict(
            (i.name, (
                cls.UnitHandler.scale_value(i.quantity)
                if i.value.nineml_type == 'SingleValue' else float('nan')))
            for i in initial_state)
        dct["weight_variables"] = (
            component_class.all_connection_parameter_names())
        # FIXME: Need to determine whether cell is "injectable" and/or
        #        conductance-based
        dct["injectable"] = True
        dct["conductance_based"] = True
        return super(PyNNCellWrapperMetaClass, cls).__new__(
            cls, celltype_id + 'PyNN', bases, dct)

    def __init__(cls, *args, **kwargs):
        """
        Not required, but since I have changed the signature of the new method
        in the derived simulator-specific classes Python complains otherwise
        """
        pass
