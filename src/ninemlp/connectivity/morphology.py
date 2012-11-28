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
import numpy as np
import collections
import xml.sax
from ninemlp import XMLHandler, SRC_PATH
from copy import copy

class Tree(object):

    def __init__(self, root, point_count):
        self.root = root
        self.points = np.zeros((point_count, 4))
        self._flatten_points(self.root)
        self.tiled_diams = np.tile(self.diams, (1, 3))
        self.min_bounds = np.squeeze(np.min(self.points[:, 0:2] - self.tiled_diams))
        self.max_bounds = np.squeeze(np.max(self.points[:, 0:2] + self.tiled_diams))
        self.mask = None
        self.mask_vox = None

    def _flatten_points(self, branch, point_index=0):
        """
        A recursive algorithm to flatten the loaded tree into a np array
        """
        for point in branch.points:
            self.points[point_index, :] = point
            point_index += 1
        for branch in branch.sub_branches:
            point_index = self._flatten_points(branch, point_index)
        return point_index

    def create_mask(self, vox=(1, 1, 1)):
        vox = np.array(vox)
        offsets = np.array(np.floor(self.min_bounds / vox), dtype=np.int)
        limits = np.array(np.ceil(self.max_bounds / vox), dtype=np.int)
        dims = limits - offsets
        mask = np.array(dims)
        scaled_points = copy(self.points[:, 0:2])
        diam_extents = copy(self.tiled_diams)
        for dim_i in xrange(3):
            scaled_points[:, dim_i] /= vox[dim_i]
            diam_extents[:, dim_i] /= vox[dim_i]
        for scaled_point, diam_extent in zip(scaled_points, diam_extents):
            # from extent to extent paint the voxels
            pass

class NeurolucidaXMLHandler(XMLHandler):
    """
    An XML handler to extract dendrite locates from Neurolucida XML format
    """
    # Create named tuples (sort of light-weight classes with no methods, like a struct in C/C++) to
    # store the extracted NeurolucidaXMLHandler data.
    Point = collections.namedtuple('Point', 'x y z diam')
    Branch = collections.namedtuple('Branch', 'points sub_branches')

    def __init__(self):
        """
        Initialises the handler, saving the cell name and creating the lists to hold the segments 
        and segment groups.
        """
        XMLHandler.__init__(self)
        self.trees = []
        self.open_branches = []

    def startElement(self, tag_name, attrs):
        """
        Overrides function in xml.sax.handler to parse all MorphML tag openings. Creates 
        corresponding segment and segment-group tuples in the handler object.
        """
        if self._opening(tag_name, attrs, 'tree', required_attrs=[('type', 'Dendrite')]):
            self.open_branches.append(self.Branch([], []))
            self.point_count = 0
        elif self._opening(tag_name, attrs, 'branch', parents=[('tree', 'branch')]):
            branch = self.Branch([], [])
            self.open_branches[-1].sub_branches.append(branch)
            self.open_branches.append(branch)
        elif self._opening(tag_name, attrs, 'point', parents=[('tree', 'branch')]):
            self.open_branches[-1].points.append(self.Point(attrs['x'], attrs['y'], attrs['z'],
                                                            attrs['d']))
            self.point_count += 1

    def endElement(self, tag_name):
        if self._closing(tag_name, 'tree', required_attrs=[('type', 'Dendrite')]):
            assert(len(self.open_branches) == 1)
            self.trees.append(Tree(self.open_branches.pop()), self.point_count)
            self.tree_point_count = 0
        elif self._closing(tag_name, 'branch', parents=[('tree', 'branch')]):
            self.open_branches.pop()
        XMLHandler.endElement(self, tag_name)


def read_NeurolucidaXML(filename):
    parser = xml.sax.make_parser()
    handler = NeurolucidaXMLHandler()
    parser.setContentHandler(handler)
    parser.parse(filename)
    return handler.trees

if __name__ == '__main__':
    import os.path
    trees = read_NeurolucidaXML(os.path.normpath(os.path.join(SRC_PATH, '..', 'morph', 'Purkinje',
                                                  'xml', 'GFP_P60.1_slide7_2ndslice-HN-FINAL.xml')))
    trees[0].create_mask()
