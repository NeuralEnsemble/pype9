"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
from ... import DEFAULT_V_INIT


class NinePyNNCell(object):

    """
    A base cell object for NCML cell classes.
    """

    @classmethod
    def get_parameter_names(cls):
        """
        Returns a list of parameters that can be set for the Cell class.

        @return [list(str)]: The list of parameter names in the class
        """
        return cls.parameter_names


class NinePyNNCellMetaClass(type):

    """
    Metaclass for building NineMLCellType subclasses
    Called by nineml_celltype_from_model
    """

    def __new__(cls, celltype_id, bases, dct):  # @NoSelf
        # Retrieved parsed model (it is placed in dct to conform with
        # with the standard structure for the "__new__" function of
        # metaclasses).
        nineml_model = dct['model'].nineml_model
        (dct["default_parameters"],
         dct["default_initial_values"]) = cls._construct_default_parameters(
                                                                  nineml_model)
        dct["receptor_types"] = cls._construct_receptor_types(nineml_model)
        dct['recordable'] = cls._construct_recordable(nineml_model)
        dct["injectable"] = True
        dct["conductance_based"] = True
        dct["model_name"] = celltype_id
        dct["weight_variables"] = cls._construct_weight_variables()
        dct["parameter_names"] = dct['default_parameters'].keys()
        return super(NinePyNNCellMetaClass, cls).__new__(
            cls, celltype_id + 'PyNN', bases, dct)

    def __init__(self, celltype_name, nineml_model, build_mode='lazy',
                 silent=False, solver_name=None, standalone=False):
        """
        Not required, but since I have changed the signature of the new method
        it otherwise complains
        """
        pass

    @classmethod
    def _construct_default_parameters(cls, nineml_model):  # @UnusedVariable
        """
        Constructs the default parameters of the 9ML class from the nineml
        model
        """
        default_params = {}
        initial_values = {}
        for p in nineml_model.parameters:
            if p.componentclass:
                component = nineml_model.biophysics.components[p.componentclass]
            else:
                component = nineml_model.biophysics.components[
                    '__NO_COMPONENT__']
            try:
                reference = cls._basic_nineml_translations[p.reference]
            except KeyError:
                reference = p.reference
            if p.reference == 'Voltage':
                parameter = DEFAULT_V_INIT
            else:
                parameter = component.parameters[reference].value
            default_params[p.name] = parameter
            if p.type == 'initialState':
                initial_values[p.name] = parameter
        return default_params, initial_values

    @classmethod
    def _construct_receptor_types(cls, nineml_model):
        """
        Constructs the dictionary of recordable parameters from the NCML model
        """
        receptors = []
        for mapping in nineml_model.mappings:
            for comp_name in mapping.components:
                component = nineml_model.biophysics.components[comp_name]
                if component.type == 'post-synaptic-conductance':
                    clsfctn = nineml_model.morphology.classifications[
                        mapping.segments.classification]
                    for seg_cls in mapping.segments:
                        for member in clsfctn[seg_cls]:
                            receptors.append(
                                '{' + str(member) + '}' + component.name)
        return receptors

    @classmethod
    def _construct_recordable(cls, nineml_model):
        """
        Constructs the dictionary of recordable parameters from the NCML model
        """
        # TODO: Make selected componentclass variables also recordable
        return ['spikes', 'v'] + \
            ['{' +
             seg +
             '}v' for seg in nineml_model.morphology.segments.keys()]

    @classmethod
    def _construct_weight_variables(cls):
        """
        Constructs the dictionary of weight variables from the NCML model
        """
        # TODO: When weights are included into the NCML model, they should be
        # added to the list here
        return {}
