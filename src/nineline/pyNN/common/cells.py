from __future__ import absolute_import
import math
from itertools import chain
from nineline.cells import NineCell

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

    def __new__(cls, celltype_id, bases, dct): #@NoSelf
        # Retrieved parsed model (it is placed in dct to conform with
        # with the standard structure for the "__new__" function of metaclasses).
        dct["default_parameters"] = cls._construct_default_parameters(dct['model'].memb_model, 
                                                                      dct['model'].morph_model,
                                                                      dct['model'].component_translations)
        dct["default_initial_values"] = cls._construct_initial_values()
        dct["receptor_types"] = cls._construct_receptor_types(dct['model'].memb_model, 
                                                              dct['model'].morph_model)
        # FIXME: This requires instantiating a model and taking the keys to its recordable 
        # dictionary, which doesn't feel right but seems to be how PyNN is organised at the present.
        dct["injectable"] = True
        dct["conductance_based"] = True
        dct["model_name"] = celltype_id
        dct["weight_variables"] = cls._construct_weight_variables()
        dct["parameter_names"] = dct['default_parameters'].keys()
        return super(NinePyNNCellMetaClass, cls).__new__(cls, celltype_id + 'PyNN', bases, dct)
    
    def __init__(self, nineml_model, build_mode='lazy', silent=False, solver_name=None):
        """
        Not required, but since I have changed the signature of the new method it otherwise 
        complains
        """
        pass

    @classmethod
    def _construct_default_parameters(cls, memb_model, morph_model, component_translations): #@UnusedVariable
        """
        Reads the default parameters in the NCML components and appends them to the parameters
        of the model class
        """
        default_params = {}
        # Add current and synapse mechanisms parameters
        for mech in memb_model.mechanisms:
            if component_translations.has_key(mech.id):
                default_params.update([(NineCell.group_varname(mech.group_id) + "." + str(mech.id) +
                                        "." + varname, mapping[1])
                                       for varname, mapping in \
                                                component_translations[mech.id].iteritems()])
            else:
                for param in mech.params:
                    default_params[NineCell.group_varname(mech.group_id) + "." + str(mech.id) + "." +
                                   param.name] = param.value
        # Add basic electrical property parameters
        for cm in memb_model.capacitances:
            default_params[NineCell.group_varname(cm.group_id) + "." + "cm"] = cm.value
        for ra in memb_model.axial_resistances:
            default_params[NineCell.group_varname(ra.group_id) + "." + "Ra"] = ra.value
        # Check each group for consistent morphology parameters and if so create a variable
        # parameter for them
        #FIXME: This should really part of the XML parser
        for seg_group in morph_model.groups:
            diameter = 'NotFound'
            length = 'NotFound'
            for seg in morph_model.segments:
                if seg.id in seg_group:
                    new_diameter = seg.distal.diam
                    if seg.proximal: # This is a bit of a hack until I rework the new XML parser
                        new_length = math.sqrt((seg.distal[0] - seg.proximal[0])**2 + 
                                               (seg.distal[1] - seg.proximal[1])**2 +
                                               (seg.distal[2] - seg.proximal[2])**2)
                    else:
                        new_length = 'NotConstant'
                    if diameter == 'NotFound':
                        diameter = new_diameter
                    elif diameter != new_diameter:
                        diameter = 'NotConstant'
                    if length == 'NotFound':
                        length = new_length
                    elif length != new_length:
                        length = 'NotConstant'
            if type(diameter) == float:
                default_params[NineCell.group_varname(seg_group.id) + ".diam"] = diameter
            if type(length) == float:
                default_params[NineCell.group_varname(seg_group.id) + ".L"] = length
        return default_params

    @classmethod
    def _construct_initial_values(cls): #@UnusedVariable
        """
        Constructs the default initial values dictionary of the cell class from the NCML model
        """
        initial_values = {'v': -65.0}
        # Here initial values are read from the parsed model
        # to populate the intial_values dictionary.
        # FIXME: Should be read from the NCML model (will need to check with Ivan the best way to do
        # this
        return initial_values

    @classmethod
    def _construct_receptor_types(cls, memb_model, morph_model):
        """
        Constructs the dictionary of recordable parameters from the NCML model
        """
        receptors = []
        for rec in memb_model.synapses:
            if rec.group_id is None:
                members = [seg.id for seg in morph_model.segments]
            else:
                group = [group for group in morph_model.groups if group.id == rec.group_id]
                if len(group) != 1:
                    raise Exception("Error parsing xml ({} groups found matching id '{}')"
                                    .format(len(group), rec.group_id))
                members = group[0].members
            for seg in members:
                receptors.append(seg + '_seg.' + rec.id)
        # Append all segments as potential gap junctions 
        for seg in morph_model.segments:
            receptors.append(seg.id + '_seg.gap')
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
        #FIXME: When weights are included into the NCML model, they should be added to the list here
        return {}
