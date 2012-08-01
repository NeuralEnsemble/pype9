"""

  This package contains the XML handlers to read the NCML files and related functions/classes, 
  the NCML base meta-class (a meta-class is a factory that generates classes) to generate a class
  for each NCML cell description (eg. a 'Purkinje' class for an NCML containing a declaration of 
  a Purkinje cell), and the base class for each of the generated cell classes.

  @file ncml.py
  @author Tom Close

"""

#######################################################################################
#
#    Copyright 2012 Okinawa Institute of Science and Technology (OIST), Okinawa, Japan
#
#######################################################################################

import xml.sax
from backports import collections
from ninemlp.common import XMLHandler

class BaseNCMLCell(object):
    """
    A base cell object for NCML cell classes.
    """

    def __init__(self):
        """
        Currently unused but could be used in future to initialise simulator independent components
        of the NCML classes.
        """
        pass


    def memb_init(self):
        # Initialisation of member states goes here        
        raise NotImplementedError("'memb_init' should be implemented by the derived class.")


class MorphMLHandler(XMLHandler):
    """
    A XML handler to extract morphology specifications from MorphML (version 2), storing them within
    the handler object to be read when neuron model objects are initialised from a generated NCML
    class.
    """

    # Create named tuples (sort of light-weight classes with no methods, like a struct in C/C++) to
    # store the extracted MorphML data.
    Morphology = collections.namedtuple('Morphology', 'morph_id cell_type_id segments groups')

    ## The basic data required to create a segment. 'proximal' and 'distal' are 'Point3D' tuples specifying the location and diameter of the segment, and 'parent' is a 'Parent' tuple.
    Segment = collections.namedtuple('Segment', 'id proximal distal parent')

    ## A reference to the parent segment used in the 'Segment' tuple. Includes the location the along the parent segment that the child segment connects to.
    Parent = collections.namedtuple('Parent', 'id fractionAlong')

    ## A position along a segment. Used to specify the location and diameter of neuronal segments.
    Point3D = collections.namedtuple('Point3D', 'x y z diam')

    ## A segment group. Contains the group's id and a list of its members.
    SegmentGroup = collections.namedtuple('SegmentGroup', 'id members')

    def __init__(self, cell_type_id=None, morph_id=None):
        """
        Initialises the handler, saving the cell name and creating the lists to hold the segments 
        and segment groups.
        """
        XMLHandler.__init__(self)
        self.cell_type_id = cell_type_id
        self.morph_id = morph_id

    def startElement(self, tag_name, attrs):
        """
        Overrides function in xml.sax.handler to parse all MorphML tag openings. Creates corresponding
        segment and segment-group tuples in the handler object.
        """
        if self._opening(tag_name, attrs, 'cell', required_attrs=[('id', self.cell_type_id)]):
            self.cell_type_id = attrs['id']
        elif self._opening(tag_name, attrs, 'morphology', parents=['cell'], required_attrs=[('id', self.morph_id)]):
            self.morphology = self.Morphology(attrs['id'], self.cell_type_id, [], [])
        elif self._opening(tag_name, attrs, 'segment', parents=['morphology']):
            self.segment_id = attrs['id']
            self.proximal = None
            self.distal = None
            self.parent = None
        elif self._opening(tag_name, attrs, 'proximal', parents=['segment']):
            self.proximal = self.Point3D(float(attrs['x']),
                                         float(attrs['y']),
                                         float(attrs['z']),
                                         float(attrs['diameter']))
        elif self._opening(tag_name, attrs, 'distal', parents=['segment']):
            self.distal = self.Point3D(float(attrs['x']),
                                       float(attrs['y']),
                                       float(attrs['z']),
                                       float(attrs['diameter']))
        elif self._opening(tag_name, attrs, 'parent', parents=['segment']):
            self.parent = self.Parent(attrs['segment'],
                                                   attrs.get('fractionAlong', 1.0))
        elif self._opening(tag_name, attrs, 'segmentGroup', parents=['morphology']):
            self.morphology.groups.append(self.SegmentGroup(attrs['id'], []))
        elif self._opening(tag_name, attrs, 'member', parents=['segmentGroup']):
            self.morphology.groups[-1].members.append(attrs['segment'])


    def endElement(self, name):
        """
        Overrides function in xml.sax.handler to parse MorphML tag closings. Only required for data
        tuples that cannot create all nested tuples at the start of the element.
        """
        if self._closing(name, 'segment', parents=['morphology']):
            self.morphology.segments.append(self.Segment(self.segment_id,
                                                          self.proximal,
                                                          self.distal,
                                                          self.parent))

        XMLHandler.endElement(self, name)



class NCMLHandler(XMLHandler):
    """
    A XML handler to extract information required to generate python classes for conductanced-based 
    neuron models from NINEML-Conductance descriptions. Storing them within the handler object to be
    read when neuron model objects are initialised from the generated NCML class.
    """

    NCMLDescription = collections.namedtuple('NCMLDescription', 'cell_type_id \
                                                                 ncml_id \
                                                                 currents synapses \
                                                                 gap_junctions \
                                                                 capacitances \
                                                                 axial_resistances \
                                                                 reversal_potentials \
                                                                 passive_currents \
                                                                 action_potential_threshold')

    ## Axial resitivity of the segment group ('group_id').
    AxialResistivity = collections.namedtuple('AxialResistivity', 'value group_id')

    ## Ionic current of the segment group ('group_id').
    IonicCurrent = collections.namedtuple('IonicCurrent', 'id group_id params')
    IonicCurrentParam = collections.namedtuple('IonicCurrentParam', 'name value')
    PassiveCurrent = collections.namedtuple('PassiveCurrent', 'group_id cond_density')
    Synapse = collections.namedtuple('Synapse', 'id type group_id params')
    GapJunction = collections.namedtuple('GapJunction', 'id type group_id params')
    SynapseParam = collections.namedtuple('SynapseParam', 'name value')
    SpecificCapacitance = collections.namedtuple('SpecificCapacitance', 'value group_id')
    ReversePotential = collections.namedtuple('NCMLReversePotential', 'species value group_id')
    ActionPotentialThreshold = collections.namedtuple('ActionPotentialThreshold', 'v')

    def __init__(self, cell_type_id=None, ncml_id=None):
        XMLHandler.__init__(self)
        self.cell_type_id = cell_type_id
        self.ncml_id = ncml_id

    def startElement(self, tag_name, attrs):
        if self._opening(tag_name, attrs, 'cell', required_attrs=[('id', self.cell_type_id)]):
            self.cell_type_id = attrs['id']
        elif self._opening(tag_name, attrs, 'biophysicalProperties', parents=['cell'], required_attrs=[('id', self.ncml_id)]):
            self.ncml = self.NCMLDescription(attrs['id'], self.cell_type_id, [], [], [], [], [], [], [], {})
        elif self._opening(tag_name, attrs, 'membraneProperties',
                                                                parents=['biophysicalProperties']):
            pass
        elif self._opening(tag_name, attrs, 'intracellularProperties',
                                                                parents=['biophysicalProperties']):
            pass
        elif self._opening(tag_name, attrs, 'actionPotentialThreshold', parents=['biophysicalProperties']):
            if self.ncml.action_potential_threshold.has_key('v'):
                raise Exception("Action potential threshold is multiply specified.")
            self.ncml.action_potential_threshold['v'] = float(attrs['v'])
        elif self._opening(tag_name, attrs, 'ionicCurrent', parents=['membraneProperties']):
            self.ncml.currents.append(self.IonicCurrent(attrs['id'],
                                                   attrs.get('segmentGroup', None),
                                                   []))
        elif self._opening(tag_name, attrs, 'ncml:const', parents=['ionicCurrent']):
            self.ncml.currents[-1].params.append(self.IonicCurrentParam(attrs['name'],
                                                                    ValueWithUnits(attrs['value'],
                                                                                   attrs.get('units', None))))
        elif self._opening(tag_name, attrs, 'passiveCurrent', parents=['membraneProperties']):
            self.ncml.passive_currents.append(self.PassiveCurrent(attrs.get('segmentGroup', None),
                                                              ValueWithUnits(attrs['condDensity'],
                                                                             attrs.get('units', None))))
        elif self._opening(tag_name, attrs, 'conductanceSynapse', parents=['membraneProperties']):
            self.ncml.synapses.append(self.Synapse(attrs['id'],
                                              attrs['type'],
                                              attrs.get('segmentGroup', None),
                                                  []))
        elif self._opening(tag_name, attrs, 'gapJunction', parents=['membraneProperties']):
            self.ncml.synapses.append(self.GapJunction(attrs['id'],
                                                  attrs['type'],
                                                  attrs.get('segmentGroup', None),
                                                  []))
        elif self._opening(tag_name, attrs, 'ncml:const', parents=['conductanceSynapse']):
            self.ncml.synapses[-1].params.append(self.SynapseParam(attrs['name'],
                                                                    ValueWithUnits(attrs['value'],
                                                                                   attrs.get('units', None))))
        elif self._opening(tag_name, attrs, 'specificCapacitance', parents=['membraneProperties']):
            self.ncml.capacitances.append(self.SpecificCapacitance(ValueWithUnits(attrs['value'],
                                                                             attrs.get('units', None)),
                                                              attrs.get('segmentGroup', None)))
        elif self._opening(tag_name, attrs, 'reversalPotential', parents=['membraneProperties']):
            self.ncml.reversal_potentials.append(self.ReversePotential(attrs['species'],
                                                                  ValueWithUnits(attrs['value'],
                                                                                 attrs.get('units', None)),
                                                                  attrs.get('segmentGroup', None)))
        elif self._opening(tag_name, attrs, 'resistivity', parents=['intracellularProperties']):
            self.ncml.axial_resistances.append(self.AxialResistivity(ValueWithUnits(attrs['value'],
                                                                        attrs.get('units', None)),
                                                                attrs.get('segmentGroup', None)))


def read_MorphML(name, filename):
    parser = xml.sax.make_parser()
    handler = MorphMLHandler(name)
    parser.setContentHandler(handler)
    parser.parse(filename)
    return handler.morphology


def read_NCML(name, filename):
    parser = xml.sax.make_parser()
    handler = NCMLHandler(name)
    parser.setContentHandler(handler)
    parser.parse(filename)
    return handler.ncml


class ValueWithUnits(object):

    def __init__(self, value, units):
        self.value = float(eval(value))
        self.units = units

    def neuron(self):
        if self.units == None:
            return self.value
        elif self.units == 'ms':
            return self.value
        elif self.units == 'uF_per_cm2':
            return self.value
        elif self.units == 'mV':
            return self.value
        elif self.units == 'ohm_cm':
            return self.value
        elif self.units == 'S_per_m2':
            return self.value
        else:
            raise Exception("Unrecognised units '" + self.units + "' (A conversion from these units \
                            to the standard NEURON units needs to be added to \
                            'ninemlp.common.ncml.neuron_value' function).")



class BaseNCMLMetaClass(type):
    """
    Metaclass for building NineMLCellType subclasses
    Called by nineml_celltype_from_model
    """
    def __new__(cls, name, bases, dct):
        # Retrieved parsed model (it is placed in dct to conform with
        # with the standard structure for the "__new__" function of metaclasses).
        ncml_model = dct['ncml_model']
        dct["default_parameters"] = cls._construct_default_parameters(ncml_model)
        dct["default_initial_values"] = cls._construct_initial_values(ncml_model)
        dct["synapse_types"] = cls._construct_synapse_types(ncml_model)
        dct["standard_receptor_type"] = False
        dct["injectable"] = True
        dct["conductance_based"] = True
        dct["model_name"] = ncml_model.cell_type_id
        dct["recordable"] = cls._construct_recordable(ncml_model)
        dct["weight_variables"] = cls._construct_weight_variables(ncml_model)
        dct["parameter_names"] = cls._construct_parameter_names(ncml_model)
        return super(BaseNCMLMetaClass, cls).__new__(cls, name, bases, dct)

    @staticmethod
    def _construct_default_parameters(ncml_model): #@UnusedVariable
        """
        Reads the default parameters in the NCML components and appends them to the parameters
        of the model class
        """
        def _as_prefix(name):
            if name:
                return name + "."
            else:
                return ""
        # Uncomment this code to populate the default parameters with all the range variables
        # in the NCML file, but since they will already be the default in MOD files it is probably not
        # necessary. The only benefit is that it would allow the constructor of the created cell type
        # to set these parameters. However, this can always be done after the cell is 
        # created using the set_parameter function of BaseNCMLCell
        default_params = {}
#        for curr in ncml_model.currents:
#            for param in curr.params:
#                default_params[_as_prefix(curr.group_id) + curr.name + "." + param.name] = param.value
#        for syn in ncml_model.synapses:
#            for param in syn.params:
#                default_params[_as_prefix(syn.group_id) + syn.name + "." + param.name] = param.value
#        for cm in ncml_model.capacitances:
#            default_params[_as_prefix(cm.group_id) + "cm"] = cm.value
#        for ra in ncml_model.axial_resistances:
#            default_params[_as_prefix(ra.group_id) + "ra"] = ra.value
#        for e_v in ncml_model.reversal_potentials:
#            default_params[_as_prefix(e_v.group_id) + e_v.species] = e_v.value
        return default_params



    @staticmethod
    def _construct_initial_values(ncml_model): #@UnusedVariable
        """
        Constructs the default initial values dictionary of the cell class from the NCML model
        """
        initial_values = {}
        # Similar to _construct_initial_values, here initial values are read from the parsed model
        # to populate the intial_values dictionary.
        # FIXME: Should be read from the NCML model (will need to check with Ivan the best way to do
        # this
        return initial_values

    @staticmethod
    def _construct_parameter_names(ncml_model):
        """
        Constructs the parameter names list of the cell class from the NCML model
        """
        parameter_names = [] #TODO: implement this function
        return parameter_names

    @staticmethod
    def _construct_synapse_types(ncml_model):
        """
        Constructs the dictionary of recordable parameters from the NCML model
        """
        return [syn.id for syn in ncml_model.synapses]

    @staticmethod
    def _construct_recordable(ncml_model): #@UnusedVariable
        """
        Constructs the dictionary of recordable parameters from the NCML model
        """
        #FIXME: Should be read from the NCML file, the only problem being that the 
        #       current pyNN.neuron.Recording._native_record does not support the passing of 
        #       mechanism in the variable parameter.
        return ['v', 'spikes', 'gsyn']

    @staticmethod
    def _construct_weight_variables(ncml_model): #@UnusedVariable
        """
        Constructs the dictionary of weight variables from the NCML model
        """
        #FIXME: When weights are included into the NCML model, they should be added to the list here
        return {}


if __name__ == "__main__":

#    import re
#
#    recordable_pattern = re.compile(r'((?P<section>\w+)(\((?P<location>[-+]?[0-9]*\.?[0-9]+)\))?\.)?(?P<var>\w+)')
#
#    match = recordable_pattern.match('soma(0.5).esyn_i')
#    if match:
#        parts = match.groupdict()
##        print 'section: ' + parts.get('section', '-')
##        print 'location: ' + parts.get('location', '-')
##        print 'location: ' + parts.get('var', '-')
#
#        print parts.get('section', '-')
#        print parts.get('location', '-')
#        print parts.get('var', '-')
#
#    else:
#        print "no match"

#
    import pprint
#
#    parsed_morphML = read_MorphML("/home/tclose/cerebellar/declarative_model/cells/purkinje/default.xml")
#    pprint.pprint(parsed_morphML.segments)
#    pprint.pprint(parsed_morphML.segmentGroups)
#
    parsed_NCMML = read_NCML("Purkinje", "/home/tclose/cerebellar/declarative_model/cells/Purkinje.xml")
    pprint.pprint(parsed_NCMML.mechanisms)
    pprint.pprint(parsed_NCMML.capacitances)
    pprint.pprint(parsed_NCMML.axial_resistances)
    pprint.pprint(parsed_NCMML.reversal_potentials)





