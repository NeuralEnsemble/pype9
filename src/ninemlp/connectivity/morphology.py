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
from abc import ABCMeta # Metaclass for abstract base classes
import math
import numpy as np
from numpy.linalg import norm
import collections
import xml.sax
from ninemlp import XMLHandler

THRESHOLD_DEFAULT = 0.001
SAMPLE_DIAM_RATIO_DEFAULT = 4.0

class ShiftVoxelSizeMismatchException(Exception): pass

class Forest(object):
    
    def __init__(self, roots):
        self.trees = []
        for root in roots:
            self.trees.append(Tree(root))
        self.centroid = np.zeros(3)
        self.min_bounds = np.ones(3) * float('inf')
        self.max_bounds = np.ones(3) * float('-inf')        
        for tree in self.trees:
            self.centroid += tree.centroid
            self.min_bounds = np.select([self.min_bounds <= tree.min_bounds, True],
                                [self.min_bounds, tree.min_bounds])
            self.max_bounds = np.select([self.max_bounds >= tree.max_bounds, True],
                                [self.max_bounds, tree.max_bounds])
        self.centroid /= len(roots)
        
    def __getitem__(self, index):
        return self.trees[index]
        
    def rotate(self, theta, axis=2):
        """
        Rotates the tree about the chosen axis by theta
        
        @param theta [float]: The degree of clockwise rotation (in degrees)
        @param axis [str/int]: The axis about which to rotate the tree (either 'x'-'z' or 0-2, default 'z'/2)
        """
        for tree in self.trees:
            tree.rotate(theta, axis)


class Tree(object):

    Segment = collections.namedtuple('Segment', 'begin end diam')

    def __init__(self, root):
        """
        Initialised the Tree object
        
        @param root [NeurolucidaXMLHandler.Branch]: The root branch of a tree loaded from a Neurolucida XML tree description 
        @param point_count [int]: The number of tree points that were loaded from the XML description
        """
        # Recursively flatten all branches stemming from the root
        self._points = []
        self._prev_indices = []
        self.diams = []
        self._flatten(root)
        # Convert flattened lists to numpy arrays
        self._points = np.array(self._points)
        self.diams = np.array(self.diams)    
        # Calculate bounds used in determining mask dimensions
        tiled_diams = np.transpose(np.tile(self.diams, (3,1)))
        self.min_bounds = np.min(self.points - tiled_diams, axis=0)
        self.max_bounds = np.max(self.points + tiled_diams, axis=0)
        self.centroid = np.average(self.points, axis=0)
        # Create dictionaries to store tree masks to save having to regenerate them the next time
        self._binary_masks = {}
        self._inv_prob_masks = {}

    @property
    def points(self):
        return self._points

    @property
    def segments(self):
        """
        Iterates through all the segments in the tree
        """
        for i, diam in enumerate(self.diams):
            prev_index = self._prev_indices[i]
            if prev_index != -1:
                yield self.Segment(self._points[prev_index, :], self.points[i, :], diam)     

    def _flatten(self, branch, prev_index=-1):
        """
        A recursive algorithm to flatten the loaded tree into a numpy array of _points used in the
        tree constructor.
        
        @param branch[NeurolucidaXMLHandler.Branch]: The loaded branch
        @param point_index [int]: the index (point count) of the current point
        @param prev_index [int]: the index of the previous point (-1 signifies no previous point, i.e the segment is a root node)
        """
        for point in branch.points:
            self._points.append(point[0:3])
            self.diams.append(point[3])
            self._prev_indices.append(prev_index)
            prev_index = len(self._points) - 1
        for branch in branch.sub_branches:
            self._flatten(branch, prev_index)

    def rotate(self, theta, axis=2):
        """
        Rotates the tree about the chosen axis by theta
        
        @param theta [float]: The degree of clockwise rotation (in degrees)
        @param axis [str/int]: The axis about which to rotate the tree (either 'x'-'z' or 0-2, default 'z'/2)
        """
        # Convert theta to radians
        theta_rad = theta * 2 * np.pi / 360.0
        # Precalculate the sine and cosine
        cos_theta = np.cos(theta_rad)
        sin_theta = np.sin(theta_rad)
        # Get appropriate rotation matrix
        if axis == 0 or axis == 'x':        
            rotation_matrix = np.array([[1, 0,         0],
                                        [0, cos_theta, -sin_theta],
                                        [0, sin_theta, cos_theta]])
        elif axis == 1 or axis == 'y':        
            rotation_matrix = np.array([[cos_theta,  0, sin_theta],
                                        [0,          1, 0],
                                        [-sin_theta, 0, cos_theta]])
        elif axis == 2 or axis == 'z':        
            rotation_matrix = np.array([[cos_theta, -sin_theta, 0],
                                        [sin_theta, cos_theta,  0],
                                        [0,         0,          1]])
        else:
            raise Exception("'axis' argument must be either 0-2 or 'x'-'y' (found {})".format(axis))
        # Rotate all the points in the tree
        self._points = np.dot(self._points, rotation_matrix)
        # Clear masks, which will no longer match the rotated points
        self._binary_masks = {}
        self._inv_prob_masks = {}
        

    def get_binary_mask(self, vox_size, sample_diam_ratio=SAMPLE_DIAM_RATIO_DEFAULT):
        """
        Creates a mask for the given voxel sizes and saves it in self._masks
        
        @param vox_size [tuple(float)]: A 3-d list/tuple/array where each element is the voxel dimension or a single float for isotropic voxels
        """
        vox_size = Mask.parse_vox_size(vox_size)
        if not self._binary_masks.has_key(vox_size):
            self._binary_masks[vox_size] = BinaryMask(self, vox_size, sample_diam_ratio)
        return self._binary_masks[vox_size]

    def get_inv_prob_mask(self, vox_size, gauss_kernel, threshold=THRESHOLD_DEFAULT,
                           sample_diam_ratio=SAMPLE_DIAM_RATIO_DEFAULT):
        """
        Creates a mask for the given voxel sizes and saves it in self._masks
        
        @param vox_size [tuple(float)]: A 3-d list/tuple/array where each element is the voxel dimension or a single float for isotropic voxels
        
        """
        vox_size = Mask.parse_vox_size(vox_size)
        if not self._inv_prob_masks.has_key(vox_size):
            self._inv_prob_masks[vox_size] = InverseProbabilityMask(self, vox_size, gauss_kernel,
                                                                    threshold, sample_diam_ratio)
        return self._inv_prob_masks[vox_size]

    def get_prob_mask(self, vox_size, gauss_kernel, threshold,
                           sample_diam_ratio=SAMPLE_DIAM_RATIO_DEFAULT):
        inv_prob_mask = self.get_inv_prob_mask(vox_size, gauss_kernel, threshold, sample_diam_ratio)
        return 1.0 - inv_prob_mask

    def shifted_tree(self, shift):
        """
        Return shifted version of tree (a lightweight copy that borrows this trees masks)
        
        @param shift [tuple(float)]: Shift to apply to the tree
        """
        return ShiftedTree(self, shift)

    def num_overlapping(self, tree, vox_size):
        """
        Calculate the number of overlapping voxels between two trees
        
        @param tree [Tree]: The second tree to calculate the overlap with
        @param vox_size [tuple(float)]: The voxel sizes to use when calculating the overlap
        """
        overlap_mask = self.get_binary_mask(vox_size).overlap(tree.get_binary_mask(vox_size))
        return np.sum(overlap_mask)

    def connection_prob(self, tree, vox_size, gauss_kernel, threshold, sample_freq):
        """
        Calculate the probability of there being any connection (there may be multiple)
        
        @param tree [Tree]: The second tree to calculate the overlap with
        @param vox_size [tuple(float)]: The voxel sizes to use when calculating the overlap
        """
        inv_prob_mask = self.get_inv_prob_mask(vox_size, gauss_kernel, sample_freq).\
                            overlap(tree.get_inv_prob_mask(vox_size, gauss_kernel, sample_freq))
        return 1.0 - np.prod(inv_prob_mask)

    def plot_mask(self, vox_size, mask_type='binary', gauss_kernel=None, sample_freq=None,
                  show=True):
        if mask_type == 'binary':
            mask = self.get_binary_mask(vox_size)
        elif mask_type == 'inverse_prob':
            mask = self.get_inv_prob_mask(vox_size, gauss_kernel, sample_freq)
        mask.plot(show=show)


class ShiftedTree(Tree):

    def __init__(self, tree, shift):
        """
        Saves a reference to the original tree and records a shift in its origin
        
        @param tree [Tree]: The original tree
        @param shift [tuple(float)]: The shift from the original tree
        """
        if len(shift) != 3:
            raise Exception("The 'shift' argument needs to be of length 3 (x, y & z coordinates), "
                            "(found length {})".format(len(shift)))
        self.shift = np.array(shift)
        # The reference to the unshifted tree is used to store unshifted masks to be 
        # accessed by all shifted copies
        self._unshifted_tree = tree
        # Shift the bounds and the centroid of the tree
        self.centroid = tree.centroid + self.shift
        self.min_bounds = tree.min_bounds + self.shift
        self.max_bounds = tree.max_bounds + self.shift    

    def get_binary_mask(self, *mask_args):
        """
        Gets the binary mask for the given voxel size and sample diameter ratio. To avoid 
        duplications the mask is accessed from the original (unshifted) tree, being created and 
        saved there if required.
        
        @param args: A 3-d list/tuple/array where each element is the voxel dimension or a single float for isotropic voxels
        """
        return self._unshifted_tree.get_binary_mask(*mask_args).shifted_mask(self.shift)

    def get_inv_prob_mask(self, *mask_args):
        """
        Gets the inverse probability mask for the given voxel size and sample diameter ratio. 
        To avoid duplications the mask is accessed from the original (unshifted) tree, being 
        created and saved there if required.
        
        @param vox_size [tuple(float)]: A 3-d list/tuple/array where each element is the voxel dimension or a single float for isotropic voxels
        """        
        return self._unshifted_tree.get_inv_prob_mask(*mask_args).shifted_mask(self.shift)

    @property
    def points(self):
        return self._points + self.shift

    @property
    def segments(self):
        for seg in self._unshifted_tree.segments:
            yield Tree.Segment(seg.begin + self.shift, seg.end + self.shift, seg.diam)


class Mask(object):
    """
    A mask containing the probability of finding a synaptic/presynaptic location at voxels
    (3D pixels) of arbitrary width that divide up the bounding box of a dendritic/axonal tree
    """
    __metaclass__ = ABCMeta # Declare this class abstract to avoid accidental construction

    def __init__(self, tree, vox_size, point_extents):
        """
        Initialises the mask from a given Neurolucida tree and voxel size
        
        @param tree [Tree]: A loaded Neurolucida tree
        @param vox_size [float]: The requested voxel sizes with which to divide up the mask with
        """
        self.vox_size = np.asarray(vox_size)
        # Get the start and finish indices of the mask, as determined by the bounds of the tree
        min_bounds = np.squeeze(np.min(tree._points - point_extents, axis=0))
        max_bounds = np.squeeze(np.max(tree._points + point_extents, axis=0))
        self.start_index = np.array(np.floor(min_bounds / self.vox_size), dtype=np.int)
        self.finish_index = np.array(np.ceil(max_bounds / self.vox_size), dtype=np.int)
        # Set the offset and limit of the mask from the start and finish indices
        self.offset = self.start_index * self.vox_size
        self.limit = self.finish_index * self.vox_size
        # Initialise the actual numpy array to hold the values
        self.dim = self.finish_index - self.start_index
        # Create an grid of the voxel centres for convenient (and more efficient) 
        # calculation of the distance from voxel centres to the tree _points. Regarding the 
        # slightly odd notation of the numpy.mgrid function, the complex numbers ('1j') are used 
        # to specify that the sequences are to be interpreted as N=self.dim[i] steps between 
        # the endpoints, grid_start[i] and grid_finish[i], instead of a typical slice sequence.
        # (see http://docs.scipy.org/doc/numpy/reference/generated/numpy.mgrid.html)
        grid_start = self.offset + self.vox_size / 2.0
        grid_finish = self.limit - self.vox_size / 2.0
        self.X, self.Y, self.Z = np.mgrid[grid_start[0]:grid_finish[0]:(self.dim[0] * 1j),
                                          grid_start[1]:grid_finish[1]:(self.dim[1] * 1j),
                                          grid_start[2]:grid_finish[2]:(self.dim[2] * 1j)]

    def overlap(self, mask):
        if np.any(mask.vox_size != self.vox_size):
            raise Exception("Voxel sizes do not match ({} and {})".format(self.vox_size,
                                                                          mask.vox_size))
        # Get the minimum finish and maximum start indices between the two masks
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
            overlap_mask = np.array([])
        return overlap_mask

    def shifted_mask(self, shift):
        return ShiftedMask(self, shift)

    def plot(self, slice_dim=2, skip=1, show=True):
        for i in xrange(0, self.dim[slice_dim], skip):
            pylab.figure()
            mask_shape = self._mask_array.shape
            if slice_dim == 0: slice_indices = np.ogrid[i:(i+1), 0:mask_shape[1], 0:mask_shape[2]]
            elif slice_dim == 1: slice_indices = np.ogrid[0:mask_shape[0], i:(i+1), 0:mask_shape[2]]
            elif slice_dim == 2: slice_indices = np.ogrid[0:mask_shape[0], 0:mask_shape[1], i:(i+1)]
            else: raise Exception("Slice dimension can only be 0-2 ({} provided)".format(slice_dim))
            pylab.imshow(np.squeeze(self._mask_array[slice_indices]))
            pylab.title('dim {}, index {}'.format(slice_dim, i))
        if show:
            pylab.show()

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
        if np.any(np.mod(self.shift, mask.vox_size)):
            raise ShiftVoxelSizeMismatchException("Shifts ({}) needs to be multiples of respective "
                                                  "voxel sizes ({})".format(shift, mask.vox_size))
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


class BinaryMask(Mask):

    def __init__(self, tree, vox_size, sample_diam_ratio=SAMPLE_DIAM_RATIO_DEFAULT):
        # Set the minimum diameter required for a point to be guaranteed to effect
        # at least one voxel
        min_point_radius = np.max(vox_size) * (math.sqrt(3.0) / 2.0)
        point_radii = tree.diams
        point_radii[point_radii < min_point_radius] = min_point_radius
        point_extents = np.tile(point_radii.reshape((-1, 1)), (1, 3))
        # Call the base 'Mask' class constructor to set up the 
        Mask.__init__(self, tree, vox_size, point_extents)
        # Initialise the mask_array
        self._mask_array = np.zeros(self.dim, dtype=bool)
        # Loop through all of the tree _point_data and "paint" the mask
        for begin, end, diam in tree.segments:
            # Check to see whether the point radius is below the minimum
            point_radius = diam if diam >= min_point_radius else min_point_radius
            # Calculate the number of samples required for the current segment
            num_samples = np.ceil(norm(end - begin) * (sample_diam_ratio / diam))
            # Loop through the samples for the given segment and add their "point_mask" to the 
            # overal mask
            for frac in np.linspace(1, 0, num_samples, endpoint=False):
                point = (1.0 - frac) * begin + frac * end
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
                dist = np.sqrt((self.X[extent_indices] - point[0]) ** 2 + \
                               (self.Y[extent_indices] - point[1]) ** 2 + \
                               (self.Z[extent_indices] - point[2]) ** 2)
                # Mask all _points that that are closer than the point diameter
                point_mask = dist < point_radius
                self._mask_array[extent_indices] += point_mask


class InverseProbabilityMask(Mask):

    def __init__(self, tree, vox_size, gauss_kernel, threshold=THRESHOLD_DEFAULT,
                 sample_diam_ratio=SAMPLE_DIAM_RATIO_DEFAULT):
        point_extents = np.ones((tree.num_points, 3)) * extent
        # Call the base 'Mask' class constructor to set up the 
        Mask.__init__(self, tree, vox_size, point_extents)
        # Initialise the mask_array
        self._mask_array = np.zeros(self.dim, dtype=bool)
        # Loop through all of the tree _point_data and "paint" the mask
        for begin, end in tree.segments:
            # Calculate the number of samples required for the current segment
            num_samples = np.ceil(norm(end - begin) * sample_freq)
            # Loop through the samples for the given segment and add their "point_mask" to the 
            # overal mask
            for frac in np.linspace(1, 0, num_samples, endpoint=False):
                point = (1.0 - frac) * begin + frac * end
                # Determine the extent of the mask indices that could be affected by the point
                extent_start = np.floor((point - self.offset - extent) / self.vox_size)
                extent_finish = np.ceil((point - self.offset + extent) / self.vox_size)
                # Get an "open" grid (uses less memory if it is open) of voxel indices to apply 
                # the distance function to.
                # (see http://docs.scipy.org/doc/numpy/reference/generated/numpy.ogrid.html)
                extent_indices = np.ogrid[int(extent_start[0]):int(extent_finish[0]),
                                          int(extent_start[1]):int(extent_finish[1]),
                                          int(extent_start[2]):int(extent_finish[2])]
                # Calculate the distances from each of the voxel centres to the given point
                dist = np.sqrt((self.X[extent_indices] - point[0]) ** 2 + \
                               (self.Y[extent_indices] - point[1]) ** 2 + \
                               (self.Z[extent_indices] - point[2]) ** 2)
                # Mask all _points that that are closer than the point diameter
                point_mask = np.exp(-0.5 / gauss_kernel * dist)
                self._mask_array[extent_indices] += point_mask


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
        Initialises the handler, saving the cell name and creating the lists to hold the _point_data 
        and segment groups.
        """
        XMLHandler.__init__(self)
        self.roots = []
        self.open_branches = []

    def startElement(self, tag_name, attrs):
        """
        Overrides function in xml.sax.handler to parse all MorphML tag openings. Creates 
        corresponding segment and segment-group tuples in the handler object.
        """
        if self._opening(tag_name, attrs, 'tree', required_attrs=[('type', 'Dendrite')]):
            self.open_branches.append(self.Branch([], []))
        elif self._opening(tag_name, attrs, 'branch', parents=[('tree', 'branch')]):
            branch = self.Branch([], [])
            self.open_branches[-1].sub_branches.append(branch)
            self.open_branches.append(branch)
        elif self._opening(tag_name, attrs, 'point', parents=[('tree', 'branch')]):
            self.open_branches[-1].points.append(self.Point(float(attrs['x']), float(attrs['y']), 
                                                            float(attrs['z']), float(attrs['d'])))

    def endElement(self, tag_name):
        if self._closing(tag_name, 'tree', required_attrs=[('type', 'Dendrite')]):
            assert(len(self.open_branches) == 1)
            self.roots.append(self.open_branches.pop())
        elif self._closing(tag_name, 'branch', parents=[('tree', 'branch')]):
            self.open_branches.pop()
        XMLHandler.endElement(self, tag_name)


def read_NeurolucidaXML(filename):
    parser = xml.sax.make_parser()
    handler = NeurolucidaXMLHandler()
    parser.setContentHandler(handler)
    parser.parse(filename)
    return Forest(handler.roots)


if __name__ == '__main__':
    from os.path import normpath, join
    from ninemlp import SRC_PATH
    import pylab
    forest = read_NeurolucidaXML(normpath(join(SRC_PATH, '..', 'morph', 'Purkinje', 'xml',
                                              'GFP_P60.1_slide7_2ndslice-HN-FINAL.xml')))
    
    vox_size = (2, 2, 2)
#    print "overlap: {}".format(forest[2].num_overlapping(forest[4], vox_size=vox_size))
    tree = forest[2]
    forest[2].plot_mask(vox_size, show=False)    
    tree.rotate(10, axis=0)
    forest[2].plot_mask(vox_size)



