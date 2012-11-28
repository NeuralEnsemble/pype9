"""

  This module defines classes to be passed pyNN Connectors to connect populations based on 
  simple point-to-point geometric connectivity rules

  @author Tom Close

"""
#######################################################################################
#
#    Copyright 2011 Okinawa Institute of Science and Technology (OIST), Okinawa, Japan
#
#######################################################################################
import numpy
import collections
from ninemlp import XMLHandler

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
                                    "'{orig}' and '{new}'".format( \
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
