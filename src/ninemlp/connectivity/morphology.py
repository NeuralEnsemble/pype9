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
from ninemlp.connectivity import axially_symmetric_tensor
try:
    import matplotlib.pyplot as plt
except:
    # If pyplot is not install, ignore it and only throw an error if a plotting function is called
    plt = None


THRESHOLD_DEFAULT = 0.02
SAMPLE_DIAM_RATIO = 4.0
SAMPLE_FREQ_DEFAULT = 100

class DisplacedVoxelSizeMismatchException(Exception): pass


class Forest(object):

    def __init__(self, xml_filename, include_somas=True):
        # Load dendritic trees
        roots = read_NeurolucidaTreeXML(xml_filename)
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
        # Load somas
        self.somas = {}
        if include_somas:
            soma_contours = read_NeurolucidaSomaXML(xml_filename)
            for name, soma_contours in soma_contours.items():
                self.somas[name] = Soma(soma_contours.contours)

    def __getitem__(self, index):
        return self.trees[index]
    
    def __iter__(self):
        for tree in self.trees:
            yield tree

    def __len__(self):
        return len(self.trees)

    def rotate(self, theta, axis=2):
        """
        Rotates the tree about the chosen axis by theta
        
        @param theta [float]: The degree of clockwise rotation (in degrees)
        @param axis [str/int]: The axis about which to rotate the tree (either 'x'-'z' or 0-2, default 'z'/2)
        """
        for tree in self.trees:
            tree.rotate(theta, axis)
            
    def combined_binary_mask(self, vox_size):
        for tree in self.trees:
            pass
        


class Tree(object):

    Segment = collections.namedtuple('Segment', 'begin end diam')

    def __init__(self, root):
        """
        Initialised the Tree object
        
        @param root [NeurolucidaTreeXMLHandler.Branch]: The root branch of a tree loaded from a Neurolucida XML tree description
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
        tiled_diams = np.transpose(np.tile(self.diams, (3, 1)))
        self.min_bounds = np.min(self.points - tiled_diams, axis=0)
        self.max_bounds = np.max(self.points + tiled_diams, axis=0)
        self.centroid = np.average(self.points, axis=0)
        # Create dictionaries to store tree masks to save having to regenerate them the next time
        self._masks = collections.defaultdict(dict)

    @property
    def points(self):
        return self._points
    
    @property
    def point_extents(self):
        return np.tile(np.reshape(self.diams / 2.0, (-1, 1)), (1, 3))

    def num_points(self):
        return len(self._points)

    @property
    def segments(self):
        """
        Iterates through all the segments in the tree
        """
        for i, diam in enumerate(self.diams):
            prev_index = self._prev_indices[i]
            if prev_index != -1:
                yield self.Segment(self._points[prev_index, :], self.points[i, :], diam)

    def num_segments(self):
        return len(self._points) - 1

    def _flatten(self, branch, prev_index= -1):
        """
        A recursive algorithm to flatten the loaded tree into a numpy array of _points used in the
        tree constructor.
        
        @param branch[NeurolucidaTreeXMLHandler.Branch]: The loaded branch
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
            rotation_matrix = np.array([[1, 0, 0],
                                        [0, cos_theta, -sin_theta],
                                        [0, sin_theta, cos_theta]])
        elif axis == 1 or axis == 'y':
            rotation_matrix = np.array([[cos_theta, 0, sin_theta],
                                        [0, 1, 0],
                                        [-sin_theta, 0, cos_theta]])
        elif axis == 2 or axis == 'z':
            rotation_matrix = np.array([[cos_theta, -sin_theta, 0],
                                        [sin_theta, cos_theta, 0],
                                        [0, 0, 1]])
        else:
            raise Exception("'axis' argument must be either 0-2 or 'x'-'y' (found {})".format(axis))
        # Rotate all the points in the tree
        self._points = np.dot(self._points, rotation_matrix)
        # Clear masks, which will no longer match the rotated points
        self._masks.clear()

    def get_binary_mask(self, vox_size):
        """
        Creates a mask for the given voxel sizes and saves it in self._masks
        
        @param vox_size [tuple(float)]: A 3-d list/tuple/array where each element is the voxel dimension or a single float for isotropic voxels
        """
        vox_size = Mask.parse_vox_size(vox_size)
        if not self._masks['binary'].has_key(vox_size):
            self._masks['binary'][vox_size] = BinaryMask(self, vox_size)
        return self._masks['binary'][vox_size]

    def get_prob_mask(self, vox_size, scale, orient, decay_rate=0.1, isotropy=1.0,
                      threshold=THRESHOLD_DEFAULT, sample_freq=SAMPLE_FREQ_DEFAULT):
        """
        Creates a mask for the given voxel sizes and saves it in self._masks
        
        @param vox_size [tuple(float)]: A 3-d list/tuple/array where each element is the voxel dimension or a single float for isotropic voxels
        
        """
        vox_size = Mask.parse_vox_size(vox_size)
        if not self._masks['prob'].has_key(vox_size):
            self._masks['prob'][vox_size] = GaussMask(self, vox_size, scale, orient,
                                                      decay_rate=decay_rate, isotropy=isotropy,
                                                      threshold=threshold, sample_freq=sample_freq)
        return self._masks['prob'][vox_size]

    def displaced_tree(self, displace):
        """
        Return displaced version of tree (a lightweight copy that borrows this trees masks)
        
        @param displace [tuple(float)]: Displace to apply to the tree
        """
        return DisplacedTree(self, displace)

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
        prob_mask = self.get_fuzzy_mask(vox_size, gauss_kernel, sample_freq).\
                            overlap(tree.get_fuzzy_mask(vox_size, gauss_kernel, sample_freq))
        return 1.0 - np.prod(prob_mask)

    def plot_binary_mask(self, vox_size, gauss_kernel=None, sample_freq=None,
                  show=True, colour_map=None):
        if not plt:
            raise Exception("Matplotlib could not be imported and therefore plotting functions "
                            "have been disabled")
        mask = self.get_binary_mask(vox_size)
        if not colour_map:
            colour_map = 'gray'
        mask.plot(show=show, colour_map=colour_map)

    def plot_prob_mask(self, vox_size, scale=1.0, orient=(1.0, 0.0, 0.0), decay_rate=0.1,
                       isotropy=1.0, threshold=THRESHOLD_DEFAULT, sample_freq=SAMPLE_FREQ_DEFAULT,
                       show=True, colour_map=None):
        mask = self.get_prob_mask(vox_size, scale, orient, decay_rate=decay_rate,
                                  isotropy=isotropy, threshold=threshold,
                                  sample_freq=sample_freq)
        if not colour_map:
            colour_map = 'jet'
        mask.plot(show=show, colour_map=colour_map)


class DisplacedTree(Tree):

    def __init__(self, tree, displacement):
        """
        A lightweight, displaced copy of the original tree, which avoids the regeneration of new 
        masks if the displacement is an even multiple of the voxel dimensions of the mask by simply
        offsetting the origin of the mask. Note that because it is a lightweight copy, changes to 
        the original tree will be reflected in its displaced copies.
        
        @param tree [Tree]: The original tree
        @param displace [tuple(float)]: The displace from the original tree
        """
        if len(displacement) != 3:
            raise Exception("The 'displacement' argument needs to be of length 3 "
                            "(x, y & z coordinates), (found length {})".format(len(displacement)))
        self.displacement = np.array(displacement)
        # The reference to the undisplaced tree is used to store undisplaced masks to be 
        # accessed by all displaced copies
        self._undisplaced_tree = tree
        # Displace the bounds and the centroid of the tree
        self.centroid = tree.centroid + self.displacement
        self.min_bounds = tree.min_bounds + self.displacement
        self.max_bounds = tree.max_bounds + self.displacement

    def get_binary_mask(self, *mask_args):
        """
        Gets the binary mask for the given voxel size and sample diameter ratio. To avoid 
        duplications the mask is accessed from the original (undisplaced) tree, being created and 
        saved there if required.
        
        @param args: A 3-d list/tuple/array where each element is the voxel dimension or a single float for isotropic voxels
        """
        try:
            return self._undisplaced_tree.get_binary_mask(*mask_args).\
                                                                   displaced_mask(self.displacement)
        except DisplacedVoxelSizeMismatchException as e:
            raise Exception("Cannot get binary mask of displaced tree because its displacement {} "
                            "is not a multiple of the mask voxel sizes. {}"
                            .format(self.displacement, e))

    def get_fuzzy_mask(self, *mask_args):
        """
        Gets the fuzzy mask for the given voxel size and sample diameter ratio. 
        To avoid duplications the mask is accessed from the original (undisplaced) tree, being 
        created and saved there if required.
        
        @param vox_size [tuple(float)]: A 3-d list/tuple/array where each element is the voxel dimension or a single float for isotropic voxels
        """
        try:
            return self._undisplaced_tree.get_fuzzy_mask(*mask_args).\
                                                                   displaced_mask(self.displacement)
        except DisplacedVoxelSizeMismatchException as e:
            raise Exception("Cannot get fuzzy mask of displaced tree because its "
                            "displacement {} is not a multiple of the mask voxel sizes. {}"
                            .format(self.displacement, e))
    @property
    def points(self):
        return self._points + self.displacement

    @property
    def segments(self):
        for seg in self._undisplaced_tree.segments:
            yield Tree.Segment(seg.begin + self.displacement, seg.end + self.displacement, seg.diam)


class Mask(object):

    __metaclass__ = ABCMeta # Declare this class abstract to avoid accidental construction

    def __init__(self, vox_size, points, point_extents):
        """
        Initialises the mask from a given Neurolucida tree and voxel size
        
        @param vox_size [float]: The requested voxel sizes with which to divide up the mask with
        """
        try:
            self.vox_size = np.asarray(vox_size).reshape(3)
        except:
            raise Exception ("Could not convert vox_size ({}) to a 3-d vector".format(vox_size))
        # If point extents are not explicitly provided use the segment radius for each dimension
        # Get the start and finish indices of the mask, as determined by the bounds of the tree
        min_bounds = np.squeeze(np.min(points - point_extents, axis=0))
        max_bounds = np.squeeze(np.max(points + point_extents, axis=0))
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

    def displaced_mask(self, displacement):
        return DisplacedMask(self, displacement)

    def plot(self, slice_dim=2, skip=1, show=True, colour_map=None):
        for i in xrange(0, self.dim[slice_dim], skip):
            if not plt:
                raise Exception("Matplotlib could not be imported and therefore plotting functions "
                                "have been disabled")
            plt.figure()
            mask_shape = self._mask_array.shape
            if slice_dim == 0: slice_indices = np.ogrid[i:(i + 1), 0:mask_shape[1], 0:mask_shape[2]]
            elif slice_dim == 1: slice_indices = np.ogrid[0:mask_shape[0], i:(i + 1), 0:mask_shape[2]]
            elif slice_dim == 2: slice_indices = np.ogrid[0:mask_shape[0], 0:mask_shape[1], i:(i + 1)]
            else: raise Exception("Slice dimension can only be 0-2 ({} provided)".format(slice_dim))
            plt.imshow(np.squeeze(self._mask_array[slice_indices]),
                       cmap=plt.cm.get_cmap(colour_map))
            plt.title('dim {}, index {}'.format(slice_dim, i))
        if show:
            plt.show()

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


class DisplacedMask(Mask):
    """
    A displaced version of the Mask, that reuses the same mask array only with updated
    start and finish indices (also updated offset and limits)
    """

    def __init__(self, mask, displacement):
        """
        Initialises the displaced mask
        
        @param mask [Mask]: The original mask
        @param displacement [tuple(float)]: The displacement of the "displaced mask"
        """
        self.displacement = np.asarray(displacement)
        if np.any(np.mod(self.displacement, mask.vox_size)):
            raise DisplacedVoxelSizeMismatchException(
                    "Displacements ({}) need to be multiples of respective voxel sizes ({})"
                    .format(displacement, mask.vox_size))
        # Copy invariant parameters
        self.dim = mask.dim
        self.vox_size = mask.vox_size
        # Displace the start and finish indices of the mask
        self.index_displacement = np.array(self.displacement / self.vox_size, dtype=np.int)
        self.start_index = mask.start_index + self.index_displacement
        self.finish_index = mask.finish_index + self.index_displacement
        # Set the offset and limit of the mask from the start and finish indices
        self.offset = mask.offset + self.displacement
        self.limit = mask.limit + self.displacement
        ## The actual mask array is the same as that of the original mask i.e. not a copy. \
        # This is the whole point of the DisplacedTree and DisplacedMasks, to avoid making \
        # unnecessary copies of this array.
        self._mask_array = mask._mask_array


class BinaryMask(Mask):

    def __init__(self, tree, vox_size):
        # Call the base 'Mask' class constructor
        Mask.__init__(self, vox_size, tree.points, tree.point_extents)
        # Initialise the mask_array with the appropriate data type
        self._mask_array = np.zeros(self.dim, dtype=bool)
        # Set a minimum extent in each dimension to ensure the that the point extents are large 
        # enough in each dimension to not "fall in the gaps" between voxels
        min_extent = np.array(vox_size) * (math.sqrt(3.0) / 2.0)
        # Loop through all of the tree _point_data and "paint" the mask
        for seg in tree.segments:
            # Set the point extent to be the segment diameter unless it is below the minimum along
            # that dimension
            point_extent = np.array((seg.diam, seg.diam, seg.diam))
            point_extent[point_extent < min_extent] = min_extent[point_extent < min_extent]
            # Calculate the number of samples required for the current segment
            num_samples = np.ceil(norm(seg.end - seg.begin) *
                                  (SAMPLE_DIAM_RATIO / min(point_extent)))
            # Loop through the samples for the given segment and add their "point_mask" to the 
            # overall mask
            for frac in np.linspace(1, 0, num_samples, endpoint=False):
                point = (1.0 - frac) * seg.begin + frac * seg.end
                # Determine the extent of the mask indices that could be affected by the point
                extent_start = np.floor((point - self.offset - seg.diam / 2.0) / self.vox_size)
                extent_finish = np.ceil((point - self.offset + seg.diam / 2.0) / self.vox_size)
                # Get an "open" grid (uses less memory if it is open) of voxel indices to apply 
                # the distance function to.
                # (see http://docs.scipy.org/doc/numpy/reference/generated/numpy.ogrid.html)
                extent_indices = np.ogrid[int(extent_start[0]):int(extent_finish[0]),
                                          int(extent_start[1]):int(extent_finish[1]),
                                          int(extent_start[2]):int(extent_finish[2])]
                # Calculate the distances from each of the voxel centres to the given point
                dist = np.sqrt(((self.X[extent_indices] - point[0]) / point_extent[0]) ** 2 + \
                               ((self.Y[extent_indices] - point[1]) / point_extent[1]) ** 2 + \
                               ((self.Z[extent_indices] - point[2]) / point_extent[2]) ** 2)
                # Mask all _points that that are closer than the point diameter
                point_mask = dist < 1.0
                self._mask_array[extent_indices] += point_mask


class FuzzyMask(Mask):

    def __init__(self,tree, vox_size):
        self._generate_mask_array(tree, vox_size)

    def _generate_mask_array(self, tree, vox_size):
        """
        
        @param tree [Tree]: The tree to draw the mask for
        @param vox_size [np.array(3)]: The size of the voxels
        @param kernel [method]: A method that takes a displacement vector and returns a value 
        """
        # Get the require parameters that are calculated by the derived class
        point_extent = self.get_point_extent() # The extent around each point that will be > threshold
        sample_freq = self.get_sample_freq() # The number of samples per unit length
        # Call the base 'Mask' class constructor to set up the 
        Mask.__init__(self, vox_size, tree.points, np.tile(point_extent, (tree.num_points(), 1)))
        # Initialise the mask_array
        self._mask_array = np.zeros(self.dim, dtype=float)
        print "Generating mask..."
        # Loop through all of the tree _point_data and "paint" the mask
        for count, seg in enumerate(tree.segments):
            # Calculate the number of samples required for the current segment
            num_samples = np.ceil(norm(seg.end - seg.begin) * sample_freq)
            # Calculate how much to scale the 
            if num_samples:
                length_scale = norm(seg.end - seg.begin) / num_samples
            # Loop through the samples for the given segment and add their "point_mask" to the 
            # overal mask
            for frac in np.linspace(1, 0, num_samples, endpoint=False):
                point = (1.0 - frac) * seg.begin + frac * seg.end
                # Determine the extent of the mask indices that could be affected by the point
                extent_start = np.floor((point - self.offset - point_extent) / self.vox_size)
                extent_finish = np.array(np.ceil((point - self.offset + point_extent) 
                                                 / self.vox_size), dtype=int)
                # Get an "open" grid (uses less memory if it is open) of voxel indices to apply 
                # the distance function to.
                # (see http://docs.scipy.org/doc/numpy/reference/generated/numpy.ogrid.html)
                extent_indices = np.ogrid[int(extent_start[0]):int(extent_finish[0]),
                                          int(extent_start[1]):int(extent_finish[1]),
                                          int(extent_start[2]):int(extent_finish[2])]
                # Get the displacements from the point to the voxel centres within the 
                # bounds of the extent.
                X = self.X[extent_indices]
                Y = self.Y[extent_indices]
                Z = self.Z[extent_indices]                                
                disps = np.vstack((X.ravel() - point[0], Y.ravel() - point[1], 
                                   Z.ravel() - point[2])).transpose()
                # Get the values of the point-spread function at each of the voxel centres
                values = self.point_spread_function(disps)
                # Add the point-spread function values to the mask_array
                self._mask_array[extent_indices] += length_scale * values.reshape(X.shape)
            if count % (tree.num_segments() // 10) == 0 and count != 0:
                print "Generating mask - {}% complete" \
                        .format(round(float(count) / float(tree.num_segments()) * 100))

    def point_spread_function(self, disps):
        # Should be implemented in derived class
        raise NotImplementedError

    def get_point_extent(self):
        # Should be implemented in derived class
        raise NotImplementedError

    def get_sample_freq(self):
        # Should be implemented in derived class        
        raise NotImplementedError


class GaussMask(FuzzyMask):

    def __init__(self, tree, vox_size, scale=1.0, orient=(1.0, 0.0, 0.0), decay_rate=0.1,
                 isotropy=1.0, threshold=THRESHOLD_DEFAULT, sample_freq=SAMPLE_FREQ_DEFAULT):
        self.scale = scale
        self.tensor = axially_symmetric_tensor(decay_rate, orient, isotropy)
        if threshold >= 1.0:
            raise Exception ("Extent threshold must be < 1.0 (was {})".format(threshold))
        self.threshold = threshold
        self.sample_freq = sample_freq
        FuzzyMask.__init__(self, tree, vox_size)

    def point_spread_function(self, disps):
        # Calculate the Gaussian point spread function f = k * exp[-0.5 * d^t . W . d] for each 
        # displacement, where 'W' is the weights matrix and 'd' is a displacement vector
        values = self.scale * np.exp(-0.5 * np.sum(disps.dot(self.tensor) * disps, axis=1))
        return values

    def get_point_extent(self):
        eig_vals, eig_vecs = np.linalg.eig(self.tensor)
        # Get the extent along each of the Eigen-vectors where the point-spread function reaches the
        # threshold, the extent along the "internal" axes of the kernel
        internal_extents = np.sqrt(-2.0 * math.log(self.threshold) / eig_vals)
        # Calculate the extent of the kernel along the x-y-z axes, the "external" axes
        extents = np.sqrt(np.sum((eig_vecs * internal_extents) ** 2, axis=1))
        return extents

    def get_sample_freq(self):
        return self.sample_freq


class Soma(object):

    def __init__(self, contours):
        """
        Initialises the Soma object
        
        @param contours [list(NeurolucidaSomaXMLHandler.Contour)]: A list of contour objects
        """
        # Recursively flatten all branches stemming from the root
        num_points = sum([len(contour.points) for contour in contours])
        self._points = np.zeros((num_points, 4))
        point_count = 0
        for contour in contours:
            for point in contour.points:
                self._points[point_count, :] = point
                point_count += 1

    @property
    def points(self):
        return self._points


class NeurolucidaTreeXMLHandler(XMLHandler):
    """
    An XML handler to extract dendrite locates from Neurolucida XML format
    """
    # Create named tuples (sort of light-weight classes with no methods, like a struct in C/C++) to
    # store the extracted NeurolucidaTreeXMLHandler data.
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


class NeurolucidaSomaXMLHandler(XMLHandler):
    """
    An XML handler to extract dendrite locates from Neurolucida XML format
    """
    # Create named tuples (sort of light-weight classes with no methods, like a struct in C/C++) to
    # store the extracted NeurolucidaTreeXMLHandler data.
    Soma = collections.namedtuple('Soma', 'contours')
    Contour = collections.namedtuple('Contour', 'points')
    Point = collections.namedtuple('Point', 'x y z diam')

    def __init__(self):
        """
        Initialises the handler, saving the cell name and creating the lists to hold the _point_data 
        and segment groups.
        """
        XMLHandler.__init__(self)
        self.somas = {}

    def startElement(self, tag_name, attrs):
        """
        Overrides function in xml.sax.handler to parse all MorphML tag openings. Creates 
        corresponding segment and segment-group tuples in the handler object.
        """
        if self._opening(tag_name, attrs, 'contour'):
            contour_name = attrs['name']
            if not self.somas.has_key(contour_name):
                self.somas[contour_name] = self.Soma([])
            self.current_contour = self.Contour([])
            self.somas[contour_name].contours.append(self.current_contour)
        elif self._opening(tag_name, attrs, 'point', parents=[('contour')]):
            self.current_contour.points.append(self.Point(attrs['x'], attrs['y'], attrs['z'], attrs['d']))


def read_NeurolucidaTreeXML(filename):
    parser = xml.sax.make_parser()
    handler = NeurolucidaTreeXMLHandler()
    parser.setContentHandler(handler)
    parser.parse(filename)
    return handler.roots

def read_NeurolucidaSomaXML(filename):
    parser = xml.sax.make_parser()
    handler = NeurolucidaSomaXMLHandler()
    parser.setContentHandler(handler)
    parser.parse(filename)
    return handler.somas

#    """
#    A mask containing the of finding a synaptic/presynaptic location at voxels
#    (3D pixels) of arbitrary width that divide up the bounding box of a dendritic/axonal tree
#    """

if __name__ == '__main__':
    from os.path import normpath, join
    from ninemlp import SRC_PATH
    forest = Forest(normpath(join(SRC_PATH, '..', 'morph', 'Purkinje', 'xml',
                                  'tree2.xml')))
    forest[0].plot_prob_mask((5, 5, 5), decay_rate=0.01)



