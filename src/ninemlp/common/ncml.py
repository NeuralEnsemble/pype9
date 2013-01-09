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
import collections
from ninemlp.common import XMLHandler, ValueWithUnits, group_varname

DEFAULT_V_INIT = -65


class MorphMLHandler(XMLHandler):
    """
    A XML handler to extract morphology specifications from MorphML (version 2), storing them 
    within the handler object to be read when neuron model objects are initialised from a generated 
    NCML class.
    """

    # Create named tuples (sort of light-weight classes with no methods, like a struct in C/C++) to
    # store the extracted MorphML data.
    Morphology = collections.namedtuple('Morphology', 'morph_id celltype_id segments groups ' \
                                                      'default_group')

    ## The basic data required to create a segment. 'proximal' and 'distal' are 'Point3D' tuples specifying the location and diameter of the segment, and 'parent' is a 'Parent' tuple.
    Segment = collections.namedtuple('Segment', 'id proximal distal parent')

    ## A reference to the parent segment used in the 'Segment' tuple. Includes the location the along the parent segment that the child segment connects to.
    Parent = collections.namedtuple('Parent', 'id fractionAlong')

    ## A position along a segment. Used to specify the location and diameter of neuronal segments.
    Point3D = collections.namedtuple('Point3D', 'x y z diam')

    ## A segment group. Contains the group's id and a list of its members.
    SegmentGroup = collections.namedtuple('SegmentGroup', 'id members default')

    def __init__(self, celltype_id=None, morph_id=None):
        """
        Initialises the handler, saving the cell name and creating the lists to hold the segments 
        and segment groups.
        """
        XMLHandler.__init__(self)
        self.celltype_id = celltype_id
        self.morph_id = morph_id
        self.found_cell_id = False

    def startElement(self, tag_name, attrs):
        """
        Overrides function in xml.sax.handler to parse all MorphML tag openings. Creates 
        corresponding segment and segment-group tuples in the handler object.
        """
        if self._opening(tag_name, attrs, 'cell', required_attrs=[('id', self.celltype_id)]):
            self.found_cell_id = True
            # Get the default morph_id from the cell attributes
            self.default_morph_id = attrs.get('defaultMorphology', None)
            # If the morph_id wasn't explicitly specified in the Handler constructor use the 
            # default value if it has been specified in the cell tag (otherwise there should only
            # be one morphology present
            if not self.morph_id and self.default_morph_id:
                self.morph_id = self.default_morph_id
        elif self._opening(tag_name, attrs, 'morphology', parents=['cell'],
                                                            required_attrs=[('id', self.morph_id)]):
            if hasattr(self, 'morphology'):
                if self.morph_id:
                    message = "Multiple morphologies were found in the '{celltype}' NCML file " \
                              "matching the ID '{id}'".format(celltype=self.celltype_id,
                                                              id=self.morph_id)
                else:
                    message = "Multiple morphologies are specified in the given '{celltype}' " \
                              "NCML file but no morphology was specified either in the " \
                              "NCMLHandler constructor or in the cell tag".\
                              format(celltype=self.celltype_id)
                raise Exception(message)
            self.segments = []
            self.segment_groups = []
            self.default_group = None
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
                                                   float(attrs.get('fractionAlong', '1.0')))
        elif self._opening(tag_name, attrs, 'segmentGroup', parents=['morphology']):
            self.segment_group_id = attrs['id']
            self.segment_group_members = []
            self.segment_group_default_member = None
            if attrs.get('default', None) == 'True':
                if self.default_group:
                    raise Exception("Cannot have two default members for a single segmentGroup (" \
                                    "'{orig}' and '{new}'".format(orig=self.default_group,
                                                                  new=attrs['id']))
                self.default_group = attrs['id']
        elif self._opening(tag_name, attrs, 'member', parents=['segmentGroup']):
            self.segment_group_members.append(attrs['segment'])
            if attrs.get('default', None) == 'True':
                if self.segment_group_default_member:
                    raise Exception("Cannot have two default members for a single segmentGroup (" \
                                    "'{orig}' and '{new}'".format(\
                                    orig=self.segment_group_default_member, new=attrs['segment']))
                self.segment_group_default_member = attrs['segment']

    def endElement(self, name):
        """
        Overrides function in xml.sax.handler to parse MorphML tag closings. Only required for data
        tuples that cannot create all nested tuples at the start of the element.
        """
        if self._closing(name, 'morphology', parents=['cell'],
                                                            required_attrs=[('id', self.morph_id)]):
            self.morphology = self.Morphology(self.morph_id, self.celltype_id, self.segments,
                                                            self.segment_groups, self.default_group)
        elif self._closing(name, 'segment', parents=['morphology']):
            self.segments.append(self.Segment(self.segment_id,
                                                          self.proximal,
                                                          self.distal,
                                                          self.parent))
        elif self._closing(name, 'segmentGroup', parents=['morphology']):
            self.segment_groups.append(self.SegmentGroup(self.segment_group_id,
                                     self.segment_group_members, self.segment_group_default_member))
        XMLHandler.endElement(self, name)


class NCMLHandler(XMLHandler):
    """
    A XML handler to extract information required to generate python classes for conductanced-based 
    neuron models from NINEML-Conductance descriptions. Storing them within the handler object to be
    read when neuron model objects are initialised from the generated NCML class.
    """

    NCMLDescription = collections.namedtuple('NCMLDescription', 'celltype_id \
                                                                 ncml_id \
                                                                 build_options \
                                                                 mechanisms \
                                                                 synapses \
                                                                 gap_junctions \
                                                                 capacitances \
                                                                 axial_resistances \
                                                                 reversal_potentials \
                                                                 passive_currents \
                                                                 action_potential_threshold')

    ## Axial resitivity of the segment group ('group_id').
    AxialResistivity = collections.namedtuple('AxialResistivity', 'value group_id')

    ## Ionic current of the segment group ('group_id').
    BuildOptions = collections.namedtuple('BuildOptions', 'method kinetics')
    IonicCurrent = collections.namedtuple('IonicCurrent', 'id group_id params')
    IonicCurrentParam = collections.namedtuple('IonicCurrentParam', 'name value')
    PassiveCurrent = collections.namedtuple('PassiveCurrent', 'group_id cond_density')
    Synapse = collections.namedtuple('Synapse', 'id type group_id params')
    GapJunction = collections.namedtuple('GapJunction', 'group_id')
    SynapseParam = collections.namedtuple('SynapseParam', 'name value')
    SpecificCapacitance = collections.namedtuple('SpecificCapacitance', 'value group_id')
    ReversePotential = collections.namedtuple('NCMLReversePotential', 'species value group_id')
    ActionPotentialThreshold = collections.namedtuple('ActionPotentialThreshold', 'v')

    def __init__(self, celltype_id=None, ncml_id=None):
        XMLHandler.__init__(self)
        self.celltype_id = celltype_id
        self.ncml_id = ncml_id
        self.found_cell_id = False

    def startElement(self, tag_name, attrs):
        if self._opening(tag_name, attrs, 'cell', required_attrs=[('id', self.celltype_id)]):
            self.found_cell_id = True
        elif self._opening(tag_name, attrs, 'biophysicalProperties', parents=['cell'],
                                                            required_attrs=[('id', self.ncml_id)]):
            self.ncml = self.NCMLDescription(
                                 self.celltype_id, attrs['id'], collections.defaultdict(dict),
                                                                [], [], [], [], [], [], [], {})
        elif self._opening(tag_name, attrs, 'defaultBuildOptions',
                           parents=['biophysicalProperties']):
            pass
        elif self._opening(tag_name, attrs, 'build', parents=['defaultBuildOptions']):
            self.build_tool = attrs['tool']
            self.build_simulator = attrs['simulator']
            self.ncml.build_options[self.build_tool][self.build_simulator] = \
                                                            self.BuildOptions(attrs['method'], [])
        elif self._opening(tag_name, attrs, 'kinetic', parents=['defaultBuildOptions', 'build']):
            self.ncml.build_options[self.build_tool][self.build_simulator].\
                    kinetics.append(attrs['comp_id'])
        elif self._opening(tag_name, attrs, 'membraneProperties',
                           parents=['biophysicalProperties']):
            pass
        elif self._opening(tag_name, attrs, 'synapses', parents=['biophysicalProperties']):
            pass
        elif self._opening(tag_name, attrs, 'intracellularProperties',
                           parents=['biophysicalProperties']):
            pass
        elif self._opening(tag_name, attrs, 'actionPotentialThreshold',
                                                                parents=['biophysicalProperties']):
            if self.ncml.action_potential_threshold.has_key('v'):
                raise Exception("Action potential threshold is multiply specified.")
            self.ncml.action_potential_threshold['v'] = float(attrs['v'])
        elif self._opening(tag_name, attrs, 'ncml:ionicCurrent', parents=['membraneProperties']) or\
                self._opening(tag_name, attrs, 'ncml:decayingPool', parents=['membraneProperties']):
            self.ncml.mechanisms.append(self.IonicCurrent(attrs['name'],
                                                   attrs.get('segmentGroup', None),
                                                   []))
        # -- This tag is deprecated as it is replaced by output python properties file from nemo --#
        elif self._opening(tag_name, attrs, 'parameter', parents=['ionicCurrent']):
            self.ncml.mechanisms[-1].params.append(self.IonicCurrentParam(attrs['name'],
                                                                    ValueWithUnits(attrs['value'],
                                                                   attrs.get('units', None))))
        #-- END --#
        elif self._opening(tag_name, attrs, 'passiveCurrent', parents=['membraneProperties']):
            # If no 'segmentGroup' is provided, default to None
            self.ncml.passive_currents.append(self.PassiveCurrent(attrs.get('segmentGroup', None),
                                                              ValueWithUnits(attrs['condDensity'],
                                                                     attrs.get('units', None))))
        elif self._opening(tag_name, attrs, 'conductanceSynapse', parents=['synapses']):
            self.ncml.synapses.append(self.Synapse(attrs['id'],
                                              attrs['type'],
                                              attrs.get('segmentGroup', None),
                                                  []))
        elif self._opening(tag_name, attrs, 'gapJunction', parents=['synapses']):
            self.ncml.gap_junctions.append(self.GapJunction(attrs.get('segmentGroup', None)))
        elif self._opening(tag_name, attrs, 'parameter', parents=['conductanceSynapse']):
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


def read_MorphML(celltype_id, filename, morph_id=None):
    parser = xml.sax.make_parser()
    handler = MorphMLHandler(celltype_id, morph_id=morph_id)
    parser.setContentHandler(handler)
    parser.parse(filename)
    if not handler.found_cell_id:
        raise Exception("Target cell id, '%s', was not found in given XML file '{}'" .\
                        format(celltype_id, filename))
    if not hasattr(handler, 'morphology'):
        raise Exception("'morphology' tag was not found in given XML file '{}'".format(filename))
    return handler.morphology


def read_NCML(celltype_id, filename):
    parser = xml.sax.make_parser()
    handler = NCMLHandler(celltype_id)
    parser.setContentHandler(handler)
    parser.parse(filename)
    if not handler.found_cell_id:
        raise Exception("Target cell id, '%s', was not found in given XML file '{}'".\
                        format(celltype_id, filename))
    if not hasattr(handler, 'ncml'):
        raise Exception("'biophysicalProperties' tag was not found in given XML file '{}'".\
                        format(filename))
    return handler.ncml


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

    @classmethod
    def get_parameter_names(cls):
        """
        Returns a list of parameters that can be set for the NCMLCell class.
        
        @return [list(str)]: The list of parameter names in the class
        """
        return cls.parameter_names

    def get_group(self, group_id):
        return self.groups[group_id] if group_id else self.all_segs


class BaseNCMLMetaClass(type):
    """
    Metaclass for building NineMLCellType subclasses
    Called by nineml_celltype_from_model
    """

    COMMON_RECORDABLE = ['v', 'spikes']

    def __new__(cls, name, bases, dct):
        # Retrieved parsed model (it is placed in dct to conform with
        # with the standard structure for the "__new__" function of metaclasses).
        cls.name = name
        cls.dct = dct
        ncml_model = dct['ncml_model']
        dct["default_parameters"] = cls._construct_default_parameters()
        dct["default_initial_values"] = cls._construct_initial_values()
        dct["synapse_types"] = cls._construct_synapse_types()
        dct["standard_receptor_type"] = False
        dct["injectable"] = True
        dct["conductance_based"] = True
        dct["model_name"] = ncml_model.celltype_id
        dct["recordable"] = cls._construct_recordable()
        dct["weight_variables"] = cls._construct_weight_variables()
        dct["parameter_names"] = dct['default_parameters'].keys()
        return super(BaseNCMLMetaClass, cls).__new__(cls, name, bases, dct)

    @classmethod
    def _construct_default_parameters(cls): #@UnusedVariable
        """
        Reads the default parameters in the NCML components and appends them to the parameters
        of the model class
        """
        ncml_model = cls.dct["ncml_model"]
        morphml_model = cls.dct["morphml_model"]
        default_params = {'parent': None}
        component_parameters = cls.dct["component_parameters"]
        # Add current and synapse mechanisms parameters
        for mech in ncml_model.mechanisms:
            if component_parameters.has_key(mech.id):
                default_params.update([(group_varname(mech.group_id) + "." + mech.id +
                                        "." + key, val[0])
                                       for key, val in component_parameters[mech.id].iteritems()])
            else:
                for param in mech.params:
                    default_params[group_varname(mech.group_id) + "." + mech.id + "." +
                                   param.name] = param.value
        for syn in ncml_model.synapses:
            for param in syn.params:
                default_params[group_varname(syn.group_id) + "." + syn.id + "." +
                               param.name] = param.value
        # Add basic electrical property parameters
        for cm in ncml_model.capacitances:
            default_params[group_varname(cm.group_id) + "." + "cm"] = cm.value
        for ra in ncml_model.axial_resistances:
            default_params[group_varname(ra.group_id) + "." + "Ra"] = ra.value
#        for e_v in ncml_model.reversal_potentials:
#            default_params[self.group_varname(e_v.group_id) + "." + \
#                                               "e_rev_" + e_v.species] = e_v.value
        # A morphology parameters
        for seg_group in morphml_model.groups:
            # None, defers to the value loaded in the MorphML file but allows them to be overwritten
            default_params[group_varname(seg_group.id) + ".diam"] = None
            default_params[group_varname(seg_group.id) + ".L"] = None
        return default_params

    @classmethod
    def _construct_initial_values(cls): #@UnusedVariable
        """
        Constructs the default initial values dictionary of the cell class from the NCML model
        """
        initial_values = {}
        # Similar to _construct_initial_values, here initial values are read from the parsed model
        # to populate the intial_values dictionary.
        # FIXME: Should be read from the NCML model (will need to check with Ivan the best way to do
        # this
        return initial_values

#    @classmethod
#    def _construct_parameter_names(cls):
#        """
#        Constructs the parameter names list of the cell class from the NCML model
#        """
#        ncml_modl = cls.dct['ncml_model']
#        parameter_names = []        
#        return parameter_names

    @classmethod
    def _construct_synapse_types(cls):
        """
        Constructs the dictionary of recordable parameters from the NCML model
        """
        ncml_model = cls.dct['ncml_model']
        return [syn.id for syn in ncml_model.synapses]

    @classmethod
    def _construct_recordable(cls):
        """
        Constructs the dictionary of recordable parameters from the NCML model
        """
        return BaseNCMLMetaClass.COMMON_RECORDABLE

    @classmethod
    def _construct_weight_variables(cls):
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




