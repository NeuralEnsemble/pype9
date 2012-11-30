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
        self._create_segments(self.root)
        tiled_diams = np.tile(self.diams.reshape((-1, 1)), (1, 3))
        self.min_bounds = np.squeeze(np.min(self.points - tiled_diams, axis=0))
        self.max_bounds = np.squeeze(np.max(self.points + tiled_diams, axis=0))
        self._masks = {}

    def _create_segments(self, branch, point_index=0):
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
            point_index = self._create_segments(branch, point_index)
        return point_index

    def get_mask(self, vox_size):
        """
        Creates a mask for the given voxel sizes and saves it in self._masks
        
        @param vox_size [tuple(float)]: A 3-d list/tuple/array where each element is the voxel dimension or a single float for isotropic voxels
        """
        vox_size = Tree.Mask.parse_vox_size(vox_size)
        if not self._masks.has_key(vox_size):
            self._masks[vox_size] = self.Mask(self, vox_size)
        return self._masks[vox_size]

    def shifted_tree(self, shift):
        return ShiftedTree(self, shift)

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
            # Get the start and finish indices of the mask, as determined by the bounds of the tree
            self.start_index = np.array(np.floor(tree.min_bounds / self.vox_size), dtype=np.int)
            self.finish_index = np.array(np.ceil(tree.max_bounds / self.vox_size), dtype=np.int)
            # Set the offset and limit of the mask from the start and finish indices
            self.offset = self.start_index * self.vox_size
            self.limit = self.finish_index * self.vox_size
            # Initialise the actual numpy array to hold the values
            self.dim = self.finish_index - self.start_index
            self._mask = np.zeros(self.dim, dtype=bool)
            # Create an grid of the voxel centres for convenient (and more efficient) 
            # calculation of the distance from voxel centres to the tree points. Regarding the 
            # slightly odd notation of the numpy.mgrid function, the complex number '1j' is used 
            # to specify that the sequences are to be interpreted as self.dim[i] steps between 
            # grid_start[i] and grid_finish[i] instead of a typical slice sequence.
            # (see http://docs.scipy.org/doc/numpy/reference/generated/numpy.mgrid.html)
            grid_start = self.offset + self.vox_size / 2.0
            grid_finish = self.limit - self.vox_size / 2.0
            X, Y, Z = np.mgrid[grid_start[0]:grid_finish[0]:(self.dim[0] * 1j),
                               grid_start[1]:grid_finish[1]:(self.dim[1] * 1j),
                               grid_start[2]:grid_finish[2]:(self.dim[2] * 1j)]
            # Loop through all of the tree segments and "paint" the mask
            for point, diam in zip(tree.points, tree.diams):
                start = np.floor((point - self.offset - diam) / self.vox_size)
                finish = np.ceil((point - self.offset + diam) / self.vox_size)
                indices = np.ogrid[int(start[0]):int(finish[0]),
                                   int(start[1]):int(finish[1]),
                                   int(start[2]):int(finish[2])]
                dist = np.sqrt((X[indices] - point[0]) ** 2 + \
                               (Y[indices] - point[1]) ** 2 + \
                               (Z[indices] - point[2]) ** 2)
                point_mask = dist < diam
                self._mask[indices] += point_mask

        def shifted_mask(self, shift):
            return Tree.ShiftedMask(self, shift)

        @classmethod
        def parse_vox_size(cls, vox_size):
            """
            Converts (if necessary) the vox_size param to a 3-d tuple
            
            @param vox_size [tuple(float)]: A 3-d list/tuple/array where each element is the voxel dimension or a single float for isotropic voxels
            """
            # Ensure that vox_size is a 3-d vector (one for each dimension)
            try:
                vox_size = tuple(vox_size)
                if len(vox_size) != 3:
                    raise Exception("Incorrect number of dimensions ('{}') for vox_size "
                                    "parameter, requires 3.".format(len(vox_size)))
            except TypeError:
                try:
                    vox_size = float(vox_size)
                    vox_size = (vox_size, vox_size, vox_size)
                except TypeError:
                    raise Exception("'vox_size' parameter ('{}') needs to be able to be "
                                    "converted to a tuple or a float ".format(vox_size))
            return vox_size

    class ShiftedMask(Mask):

        def __init__(self, mask, shift):
            self.shift = np.asarray(shift)
            if np.any(np.mod(self.shift, self.vox_size)):
                raise Exception("Shifts ({}) needs to be multiple of respective voxel sizes "
                                "({})".format(shift, self.vox_size))
            # Copy invariant parameters
            self.dim = mask.dim
            self.vox_size = mask.vox_size
            # Shift the start and finish indices of the mask
            self.index_shift = np.array(np.floor(self.shift / self.vox_size), dtype=np.int)
            self.start_index = mask.start_index + self.index_shift
            self.finish_index = mask.finish_index + self.index_shift
            # Set the offset and limit of the mask from the start and finish indices
            self.offset = tree.offset + self.shift
            self.limit = tree.limit + self.shift
            ## The actual mask array is the same as that of the original mask i.e. not a copy. \
            #  This is the whole point of the ShiftedTree and ShiftedMasks avoiding making \
            # copies of this array
            self._mask = mask._mask                
                

class ShiftedTree(Tree):

    def __init__(self, tree, shift):
        """
        Saves a reference to the original tree and records a shift in its origin
        
        @param tree [Tree]: The original tree
        @param shift [tuple(float)]: The shift from the original tree
        """
        self._original_tree = tree
        self.shift = shift
        self._masks = {}

    def get_mask(self, vox_size):
        vox_size = Tree.Mask.parse_vox_size(vox_size)
        if not self._masks.has_key(vox_size):
            self._masks[vox_size] = self._original_tree.get_mask(vox_size).shifted_mask(self.shift)
        return self._masks[vox_size]


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
    import pylab
    trees = read_NeurolucidaXML(normpath(join(SRC_PATH, '..', 'morph', 'Purkinje', 'xml',
                                              'GFP_P60.1_slide7_2ndslice-HN-FINAL.xml')))
    tree = trees[0]
    mask = tree.get_mask((1, 1, 1))
    for z in xrange(mask.dim[2]):
        pylab.figure()
        pylab.imshow(mask._mask[:, :, z])
    pylab.show()
    print "done"


