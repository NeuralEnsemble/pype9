from __future__ import absolute_import
from itertools import chain

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
        # Return all the parameter names plus the "raw" names used in the NeMo generated models
        raw_names = list(chain.from_iterable([[param[0] for param in comp.values()]
                                              for comp in cls.component_translations.values()]))
        return cls.parameter_names + raw_names


class NinePyNNCellMetaClass(type):
    """
    Metaclass for building NineMLCellType subclasses
    Called by nineml_celltype_from_model
    """

    def __new__(cls, celltype_id, bases, dct):  # @NoSelf
        # Retrieved parsed model (it is placed in dct to conform with
        # with the standard structure for the "__new__" function of metaclasses).
        dct["default_parameters"] = cls._construct_default_parameters(dct['model'].nineml_model)
        dct["default_initial_values"] = cls._construct_initial_values()
        dct["receptor_types"] = cls._construct_receptor_types(dct['model'].nineml_model)
        # FIXME: This requires instantiating a model and taking the keys to its recordable
        # dictionary, which doesn't feel right but seems to be how PyNN is organised at the present.
        dct["injectable"] = True
        dct["conductance_based"] = True
        dct["model_name"] = celltype_id
        dct["weight_variables"] = cls._construct_weight_variables()
        dct["parameter_names"] = dct['default_parameters'].keys()
        return super(NinePyNNCellMetaClass, cls).__new__(cls, celltype_id + 'PyNN', bases, dct)

    def __init__(self, celltype_name, nineml_model, build_mode='lazy', silent=False, 
                 solver_name=None):
        """
        Not required, but since I have changed the signature of the new method it otherwise 
        complains
        """
        pass

    @classmethod
    def _construct_default_parameters(cls, nineml_model):  # @UnusedVariable
        """
        Constructs the default parameters of the 9ML class from the nineml model
        """
        default_params = {}
        for p in nineml_model.parameters:
            if p.component == 'Geometry':
                if p.reference == 'Diameter':
                    default_value = nineml_model.biophysics.components['__GEOMETRY__'].\
                                                            parameters['diam'].value
                else:
                    default_value = 1.0
            elif p.component == 'InitialState':
                if p.reference == 'Voltage':
                    default_value = -65
                else:
                    default_value = 0.0
            else:
                default_value = nineml_model.biophysics.components[p.component].\
                                                            parameters[p.reference].value
            default_params[p.name] = default_value
        return default_params

    @classmethod
    def _construct_initial_values(cls):  # @UnusedVariable
        """
        Constructs the default initial values dictionary of the cell class from the NCML model
        """
        initial_values = {'v':-65.0}
        # Here initial values are read from the parsed model
        # to populate the intial_values dictionary.
        # FIXME: Should be read from the NCML model (will need to check with Ivan the best way to do
        # this
        return initial_values

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
                    clsfctn = nineml_model.morphology.classifications[mapping.segments.classification]
                    for seg_cls in mapping.segments:
                        for member in clsfctn[seg_cls].members:
                            receptors.append('{' + str(member) + '}' + component.name)
        return receptors      
                    
    @classmethod
    def _construct_recordable(cls):
        """
        Constructs the dictionary of recordable parameters from the NCML model
        """
        raise NotImplementedError("'_construct_recordable' should be implemented by derived class")

    @classmethod
    def _construct_weight_variables(cls):
        """
        Constructs the dictionary of weight variables from the NCML model
        """
        # FIXME: When weights are included into the NCML model, they should be added to the list here
        return {}
