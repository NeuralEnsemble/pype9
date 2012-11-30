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
import math
import numpy as np
from numpy.linalg import norm
import collections
import xml.sax
from ninemlp import XMLHandler

class ShiftVoxelSizeMismatchException(Exception): pass


class Tree(object):

    Segment = collections.namedtuple('Segment', 'begin end diam')

    def __init__(self, root, point_count):
        """
        Initialised the Tree object
        
        @param root [NeurolucidaXMLHandler.Branch]: The root branch of a tree loaded from a Neurolucida XML tree description 
        @param point_count [int]: The number of tree points that were loaded from the XML description
        """
        self.root = root
        self.points = np.zeros((point_count, 3))
        self.diams = np.zeros((point_count, 1))
        self.segments = []
        self._flatten(self.root)
        self._masks = {}

    def _flatten(self, branch, point_index=0, prev_point=None):
        """
        A recursive algorithm to flatten the loaded tree into a numpy array of points used in the
        tree constructor.
        
        @param branch[NeurolucidaXMLHandler.Branch]
        """
        for point in branch.points:
            self.points[point_index, :] = point[0:3]
            self.diams[point_index] = point[3]
            if prev_point:
                self.segments.append(Tree.Segment(prev_point[0:3], point[0:3], point[3]))
            prev_point = point
            point_index += 1
        for branch in branch.sub_branches:
            point_index = self._flatten(branch, point_index, prev_point)
        return point_index

    def get_mask(self, vox_size):
        """
        Creates a mask for the given voxel sizes and saves it in self._masks
        
        @param vox_size [tuple(float)]: A 3-d list/tuple/array where each element is the voxel dimension or a single float for isotropic voxels
        """
        vox_size = Mask.parse_vox_size(vox_size)
        if not self._masks.has_key(vox_size):
            self._masks[vox_size] = self.Mask(self, vox_size)
        return self._masks[vox_size]

    def shifted_tree(self, shift):
        """
        Return shifted version of tree
        
        @param shift [tuple(float)]: Shift to apply to the tree
        """
        return ShiftedTree(self, shift)

    def num_overlapping(self, tree, vox_size):
        """
        Calculate the number of overlapping voxels between two trees
        
        @param tree [Tree]: The second tree to calculate the overlap with
        @param vox_size [tuple(float)]: The voxel sizes to use when calculating the overlap
        """
        overlap_mask = self.get_mask(vox_size).overlap(tree.get_mask(vox_size))
        return np.sum(overlap_mask)

    def any_connection_prob(self, tree, vox_size, gauss_kernel, sample_interval=1):
        """
        Calculate the probability of there being any connection (there may be multiple)
        
        @param tree [Tree]: The second tree to calculate the overlap with
        @param vox_size [tuple(float)]: The voxel sizes to use when calculating the overlap
        """
        overlap_mask = self.get_mask(vox_size).overlap(tree.get_mask(vox_size))
        return 1.0 - np.prod(overlap_mask)


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
        vox_size = Mask.parse_vox_size(vox_size)
        if not self._masks.has_key(vox_size):
            self._masks[vox_size] = self._original_tree.get_mask(vox_size).shifted_mask(self.shift)
        return self._masks[vox_size]


class Mask(object):
    """
    A mask containing the probability of finding a synaptic/presynaptic location at voxels
    (3D pixels) of arbitrary width that divide up the bounding box of a dendritic/axonal tree
    """

    def __init__(self, tree, vox_size, sample_freq=0.0):
        """
        Initialises the mask from a given Neurolucida tree and voxel size
        
        @param tree [Tree]: A loaded Neurolucida tree
        @param vox_size [float]: The requested voxel sizes with which to divide up the mask with
        """
        self.vox_size = np.asarray(vox_size)

        # Set the minimum diameter required for a point to be guaranteed to effect
        # at least one voxel
        min_point_radius = np.max(self.vox_size) * (math.sqrt(3) / 2)
        point_radii = tree.diams
        point_radii[point_radii < min_point_radius] = min_point_radius
        # Get the start and finish indices of the mask, as determined by the bounds of the tree
        tiled_radii = np.tile(point_radii.reshape((-1, 1)), (1, 3))
        min_bounds = np.squeeze(np.min(tree.points - tiled_radii, axis=0))
        max_bounds = np.squeeze(np.max(tree.points + tiled_radii, axis=0))
        self.start_index = np.array(np.floor(min_bounds / self.vox_size), dtype=np.int)
        self.finish_index = np.array(np.ceil(max_bounds / self.vox_size), dtype=np.int)
        # Set the offset and limit of the mask from the start and finish indices
        self.offset = self.start_index * self.vox_size
        self.limit = self.finish_index * self.vox_size
        # Initialise the actual numpy array to hold the values
        self.dim = self.finish_index - self.start_index
        self._mask_array = np.zeros(self.dim, dtype=bool)
        # Create an grid of the voxel centres for convenient (and more efficient) 
        # calculation of the distance from voxel centres to the tree points. Regarding the 
        # slightly odd notation of the numpy.mgrid function, the complex numbers ('1j') are used 
        # to specify that the sequences are to be interpreted as N=self.dim[i] steps between 
        # the endpoints, grid_start[i] and grid_finish[i], instead of a typical slice sequence.
        # (see http://docs.scipy.org/doc/numpy/reference/generated/numpy.mgrid.html)
        grid_start = self.offset + self.vox_size / 2.0
        grid_finish = self.limit - self.vox_size / 2.0
        X, Y, Z = np.mgrid[grid_start[0]:grid_finish[0]:(self.dim[0] * 1j),
                           grid_start[1]:grid_finish[1]:(self.dim[1] * 1j),
                           grid_start[2]:grid_finish[2]:(self.dim[2] * 1j)]
        # Loop through all of the tree segments and "paint" the mask
        for seg in tree.segments:
            num_samples = np.ceil(norm(seg.end - seg.end) * sample_freq)
            for frac in np.linspace(0, 1, num_samples):
                point = (1.0 - frac) * seg.begin + frac * seg.end
                point_radius = (1.0 - frac) * seg.begin_diam + frac * seg.end_diam
                # Determine the extent of the mask indices that could be affected by the point
                extent_start = np.floor((point - self.offset - point_radius) / self.vox_size)
                extent_finish = np.ceil((point - self.offset + point_radius) / self.vox_size)
                # Get an "open" grid (uses less memory if it is open) of voxel indices to apply 
                # the distance function to.
                # (see http://docs.scipy.org/doc/numpy/reference/generated/numpy.ogrid.html)
                extent_indices = np.ogrid[int(extent_start[0]):int(extent_finish[0]),
                                          int(extent_start[1]):int(extent_finish[1]),
                                          int(extent_start[2]):int(extent_finish[2])]
                # Calculate the distances from each of the voxel centres to the given point
                dist = np.sqrt((X[extent_indices] - point[0]) ** 2 + \
                               (Y[extent_indices] - point[1]) ** 2 + \
                               (Z[extent_indices] - point[2]) ** 2)
                # Mask all points that that are closer than the point diameter
                point_mask = dist < point_radius
                self._mask_array[extent_indices] += point_mask

    def overlap(self, mask):
        if np.any(mask.vox_size != self.vox_size):
            raise Exception("Voxel sizes do not match ({} and {})".format(self.vox_size,
                                                                          mask.vox_size))
        start_index = np.select([self.start_index >= mask.start_index, True],
                                [self.start_index, mask.start_index])
        finish_index = np.select([self.finish_index <= mask.finish_index, True],
                                [self.finish_index, mask.finish_index])
        if np.all(finish_index > start_index):
            self_start_index = start_index - self.start_index
            self_finish_index = finish_index - self.start_index
            mask_start_index = start_index - mask.start_index
            mask_finish_index = finish_index - mask.start_index
            # Multiply the overlapping portions of the mask arrays together to get the overlap         
            overlap_mask = self._mask_array[self_start_index[0]:self_finish_index[0],
                                            self_start_index[1]:self_finish_index[1],
                                            self_start_index[2]:self_finish_index[2]] * \
                           mask._mask_array[mask_start_index[0]:mask_finish_index[0],
                                            mask_start_index[1]:mask_finish_index[1],
                                            mask_start_index[2]:mask_finish_index[2]]
        else:
            overlap_mask = np.array()
        return overlap_mask

    def shifted_mask(self, shift):
        return ShiftedMask(self, shift)

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
    """
    A shifted version of the Mask, that reuses the same mask array only with updated
    start and finish indices (also updated offset and limits)
    """

    def __init__(self, mask, shift):
        """
        Initialises the shifted mask
        
        @param mask [Mask]: The original mask
        @param shift [tuple(float)]: The shift applied to the mask
        """
        self.shift = np.asarray(shift)
        if np.any(np.mod(self.shift, self.vox_size)):
            raise ShiftVoxelSizeMismatchException("Shifts ({}) needs to be multiples of "
                                                      "respective voxel sizes ({})"
                                                      .format(shift, self.vox_size))
        # Copy invariant parameters
        self.dim = mask.dim
        self.vox_size = mask.vox_size
        # Shift the start and finish indices of the mask
        self.index_shift = np.array(self.shift / self.vox_size, dtype=np.int)
        self.start_index = mask.start_index + self.index_shift
        self.finish_index = mask.finish_index + self.index_shift
        # Set the offset and limit of the mask from the start and finish indices
        self.offset = mask.offset + self.shift
        self.limit = mask.limit + self.shift
        ## The actual mask array is the same as that of the original mask i.e. not a copy. \
        # This is the whole point of the ShiftedTree and ShiftedMasks, to avoid making \
        # unnecessary copies of this array.
        self._mask_array = mask._mask_array



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
    vox_size = (2.5, 2.5, 2.5)
    print "overlap: {}".format(trees[2].num_overlapping(trees[4], vox_size=vox_size))
    tree = trees[2]
    mask = tree.get_mask(vox_size)
    for z in xrange(mask.dim[2]):
        pylab.figure()
        pylab.imshow(mask._mask_array[:, :, z])
        pylab.title(z)
    pylab.show()
    print "done"


