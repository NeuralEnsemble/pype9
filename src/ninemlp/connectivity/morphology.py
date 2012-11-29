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
from ninemlp import XMLHandler

class Tree(object):

    def __init__(self, root, point_count):
        """
        Initialised the Tree object
        
        @param root [NeurolucidaXMLHandler.Branch]: The root branch of a tree loaded from a Neurolucida XML tree description
        @param point_count [int]: The number of tree points that were loaded from the XML description
        """
        self.root = root
        self.points = np.zeros((point_count, 3))
        self.diams = np.zeros(point_count)
        self._flatten_points(self.root)
        tiled_diams = np.tile(self.diams.reshape((-1,1)), (1,3))
        self.min_bounds = np.squeeze(np.min(self.points - tiled_diams, axis=0))
        self.max_bounds = np.squeeze(np.max(self.points + tiled_diams, axis=0))
        self.mask = None
        self.mask_vox = None

    def _flatten_points(self, branch, point_index=0):
        """
        A recursive algorithm to flatten the loaded tree into a numpy array of points used in the
        tree constructor.
        
        @param branch[NeurolucidaXMLHandler.Branch]
        """
        for point in branch.points:
            self.points[point_index, :] = point[0:3]
            self.diams[point_index] = point[3]
            point_index += 1
        for branch in branch.sub_branches:
            point_index = self._flatten_points(branch, point_index)
        return point_index

    class Mask(object):
        """
        A mask containing the probability of finding a synaptic/presynaptic location at voxels
        (3D pixels) of arbitrary width that divide up the bounding box of a dendritic/axonal tree
        """
        
        def __init__(self, tree, vox_size):
            """
            Initialises the mask from a given Neurolucida tree and voxel size
            
            @param tree [Tree]: A loaded Neurolucida tree
            @param vox_size [float]: The requested voxel sizes with which to divide up the mask with
            """
            self.vox_size = np.asarray(vox_size)
            # Save int versions of the offset and limits for convenient matching with other arrays
            self.start_index = np.array(np.floor(tree.min_bounds / self.vox_size), dtype=np.int)
            self.finish_index = np.array(np.ceil(tree.max_bounds / self.vox_size), dtype=np.int)
            # Get the offset and limits of the mask, which are lower and upper corners of the voxel
            # array that cover the bounds of the tree
            self.offset = self.start_index * self.vox_size
            self.limit = self.finish_index * self.vox_size
            # Initialise the actual numpy array to hold the values
            self.dim = self.finish_index - self.start_index
            self._mask = np.array(self.dim)
            # Create an "open" grid of the voxel centres for efficient (and convenient) 
            # calculation of the distance from voxel centres to the tree points. (Note since it is 
            # open it only takes up O(dim[0] + dim[1] + dim[2]) memory instead of 
            # O(dim[0] * dim[1] * dim[2]), which it would take if it were dense.)
            grid_start = self.offset + self.vox_size / 2.0
            grid_finish = self.limit - self.vox_size / 2.0
            self.X, self.Y, self.Z = np.ogrid[grid_start[0]:grid_finish[0]:(self.dim[0] * 1j),
                                              grid_start[1]:grid_finish[1]:(self.dim[1] * 1j),
                                              grid_start[2]:grid_finish[2]:(self.dim[2] * 1j)]
            for point, diam in zip(tree.points, tree.diams):
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
            self.trees.append(Tree(self.open_branches.pop(), self.point_count))
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
    from os.path import normpath, join
    from ninemlp import SRC_PATH
    trees = read_NeurolucidaXML(normpath(join(SRC_PATH, '..', 'morph', 'Purkinje', 'xml', 
                                              'GFP_P60.1_slide7_2ndslice-HN-FINAL.xml')))
    mask = Tree.Mask(trees[0], (10,10,10))
