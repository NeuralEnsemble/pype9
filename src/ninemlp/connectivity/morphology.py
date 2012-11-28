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
import collections
from ninemlp import XMLHandler
import weakref
import xml.sax

class NeurolucidaXMLHandler(XMLHandler):
    """
    An XML handler to extract dendrite locates from Neurolucida XML format
    """
    # Create named tuples (sort of light-weight classes with no methods, like a struct in C/C++) to
    # store the extracted NeurolucidaXMLHandler data.
    Point = collections.namedtuple('Point', 'x y z diam')
    
    # I wasn't able to use a namedtuple for Branch as I need to create weakrefs of it and tuples
    # aren't weakrefable for performance reasons
    class Branch:
        def __init__(self, parent=None):
            self.points = []
            self.sub_branches = []
            if parent:
                self._parent = weakref.ref(parent)
            else:
                self._parent = None

        def __str__(self):
            return "points: {}, sub_branches: {}, parent {}".format(self.points, self.sub_branches,
                                                                   self._parent)
            
        def parent(self):
            if self._parent:
                return self._parent()
            else:
                return None

    def __init__(self):
        """
        Initialises the handler, saving the cell name and creating the lists to hold the segments 
        and segment groups.
        """
        XMLHandler.__init__(self)
        self.trees = []
        self.current_branch = None

    def startElement(self, tag_name, attrs):
        """
        Overrides function in xml.sax.handler to parse all MorphML tag openings. Creates 
        corresponding segment and segment-group tuples in the handler object.
        """
        print tag_name
        if self._opening(tag_name, attrs, 'tree', required_attrs=[('type', 'Dendrite')]):
            tree = self.Branch()
            self.trees.append(tree) 
            self.current_branch = tree
        elif self._opening(tag_name, attrs, 'branch', parents=[('tree', 'branch')]):
            # Weakref is used to avoid a circular reference between the branch and its parent
            # thus preventing the structure from being destroyed by the garbarge collector
            branch = self.Branch(self.current_branch)
            self.current_branch.sub_branches.append(branch)
            self.current_branch = branch
        elif self._opening(tag_name, attrs, 'point', parents=['branch']):
            self.current_branch.points.append(self.Point(attrs['x'], attrs['y'], attrs['z'], 
                                                         attrs['d']))
            
    def endElement(self, tag_name):
        if self._closing(tag_name, 'branch', parents=[('tree', 'branch')]):
            # Set the "current branch" to the current "current branch"'s parent
            parent = self.current_branch.parent()
            if parent:
                self.current_branch = parent
            else:
                raise Exception("Already reached the top of the branch tree, cannot climb any " \
                                "higher")
            
def read_NeurolucidaXML(filename):
    parser = xml.sax.make_parser()
    handler = NeurolucidaXMLHandler()
    parser.setContentHandler(handler)
    parser.parse(filename)
    return handler.trees