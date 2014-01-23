from __future__ import absolute_import
from abc import ABCMeta # Metaclass for abstract base classes
import math
import numpy
from numpy.linalg import norm
from copy import deepcopy
import .tree
from ..__init__ import axially_symmetric_tensor

try:
    import matplotlib.pyplot as plt
except:
    # If pyplot is not installed, ignore it and only throw an error if a plotting function is called
    plt = None

#  Mask objects to map the morphologies to arrays of data ------------------------------------------

# Constants ----------------------------------------------------------------------------------------

GAUSS_THRESHOLD_DEFAULT = 0.02
GAUSS_SAMPLE_FREQ_DEFAULT = 100
DEEP_Z_VOX_SIZE = 10000 # This is the vox size used for the z axis to approximate infinite depth
# Pre-calculated for speed (not sure if this would be a bottleneck though)
SQRT_3 = math.sqrt(3)
SAMPLE_DIAM_RATIO = 4.0

# Pre-calculated for speed (not sure if this would be a bottleneck though)
SQRT_3 = math.sqrt(3)


class DisplacedVoxelSizeMismatchException(Exception): pass

class Mask(object):

    __metaclass__ = ABCMeta # Declare this class abstract to avoid accidental construction

    def __init__(self, vox_size, points, point_extents, dtype):
        """
        Initialises the mask from a given Neurolucida tree and voxel size
        
        @param vox_size [float]: The requested voxel sizes with which to divide up the mask with
        """
        try:
            self.vox_size = numpy.asarray(vox_size).reshape(3)
        except:
            raise Exception ("Could not convert vox_size ({}) to a 3-d vector".format(vox_size))
        # If point extents are not explicitly provided use the segment radius for each dimension
        # Get the start and finish indices of the mask, as determined by the bounds of the tree
        min_bounds = numpy.squeeze(numpy.min(points - point_extents, axis=0))
        max_bounds = numpy.squeeze(numpy.max(points + point_extents, axis=0))
        self.start_index = numpy.array(numpy.floor(min_bounds / self.vox_size), dtype=numpy.int)
        self.finish_index = numpy.array(numpy.ceil(max_bounds / self.vox_size), dtype=numpy.int)
        # Set the offset and limit of the mask from the start and finish indices
        self.offset = self.start_index * self.vox_size
        self.limit = self.finish_index * self.vox_size
        # Initialise the actual numpy array to hold the values
        self.dim = self.finish_index - self.start_index
        #print self.offset,self.limit
        # Create an grid of the voxel centres for convenient (and more efficient) 
        # calculation of the distance from voxel centres to the tree _points. Regarding the 
        # slightly odd notation of the numpy.mgrid function, the complex numbers ('1j') are used 
        # to specify that the sequences are to be interpreted as N=self.dim[i] steps between 
        # the endpoints, grid_start[i] and grid_finish[i], instead of a typical slice sequence.
        # (see http://docs.scipy.org/doc/numpy/reference/generated/numpy.mgrid.html)
        grid_start = self.offset + self.vox_size / 2.0
        grid_finish = self.limit - self.vox_size / 2.0
        self.X, self.Y, self.Z = numpy.mgrid[grid_start[0]:grid_finish[0]:(self.dim[0] * 1j),
                                          grid_start[1]:grid_finish[1]:(self.dim[1] * 1j),
                                          grid_start[2]:grid_finish[2]:(self.dim[2] * 1j)]
        # Initialise the mask_array with the appropriate data type
        self._mask_array = numpy.zeros(self.dim, dtype=dtype)

    def overlap(self, mask):
        if numpy.any(mask.vox_size != self.vox_size):
            raise Exception("Voxel sizes do not match ({} and {})".format(self.vox_size,
                                                                          mask.vox_size))
        # Get the minimum finish and maximum start indices between the two masks
        start_index = numpy.select([self.start_index >= mask.start_index, True],
                                [self.start_index, mask.start_index])
        finish_index = numpy.select([self.finish_index <= mask.finish_index, True],
                                [self.finish_index, mask.finish_index])
        if numpy.all(finish_index > start_index):
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
            overlap_mask = numpy.array([])
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
            if slice_dim == 0: slice_indices = numpy.ogrid[i:(i + 1), 0:mask_shape[1], 0:mask_shape[2]]
            elif slice_dim == 1: slice_indices = numpy.ogrid[0:mask_shape[0], i:(i + 1), 0:mask_shape[2]]
            elif slice_dim == 2: slice_indices = numpy.ogrid[0:mask_shape[0], 0:mask_shape[1], i:(i + 1)]
            else: raise Exception("Slice dimension can only be 0-2 ({} provided)".format(slice_dim))
            img = plt.imshow(numpy.squeeze(self._mask_array[slice_indices]),
                             cmap=plt.cm.get_cmap(colour_map))
            img.set_interpolation('nearest')
            plt.title('Dim {}, Index {}'.format(slice_dim, i))
            if self._mask_array.dtype != numpy.dtype('bool'):
                plt.colorbar()
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

    @classmethod
    def _parse_tree_points(cls, tree_or_points, diams=None):
        if type(tree_or_points) == tree.Tree:
            tree = tree_or_points
            points = tree.points
            if diams:
                raise Exception("Diameters should only be provided if the 'tree_or_points' is an "
                                "array of points")
            diams = tree.diams
        elif type(tree_or_points) == numpy.ndarray and tree_or_points.shape[1] == 3:
            tree = None
            points = tree_or_points
            if points.shape[0] != len(diams):
                raise Exception("Number of points ({}) and length of diams ({}) do not match."
                                .format(points.shape[0], len(diams)))
        else:
            raise Exception("Incorrect type for 'tree_or_points' parameter ({}), must be either "
                            "'Tree' or numpy.array(N x 3)".format(type(tree_or_points)))
        point_extents = numpy.tile(numpy.reshape(diams / 2.0, (-1, 1)), (1, 3))
        return tree, points, point_extents

    def _check_match(self, mask):
        if any(self.vox_size != mask.vox_size):
            raise Exception("Voxel sizes do not match ({} and {})"
                            .format(self.vox_size, mask.vox_size))
        if any(self.start_index != mask.start_index):
            raise Exception("Start indices do not match ({} and {})"
                            .format(self.start_index, mask.start_index))
        if any(self.finish_index != mask.finish_index):
            raise Exception("Finish indices do not match ({} and {})"
                            .format(self.finish_index, mask.finish_index))

    def __iadd__(self, mask):
        self._check_match(mask)
        self._mask_array += mask._mask_array
        return self

    def __add__(self, mask):
        new_mask = deepcopy(self)
        new_mask += mask._mask_array
        return new_mask


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
        self.displacement = numpy.asarray(displacement)
        if numpy.any(numpy.mod(self.displacement, mask.vox_size)):
            raise DisplacedVoxelSizeMismatchException(
                    "Displacements ({}) need to be multiples of respective voxel sizes ({})"
                    .format(displacement, mask.vox_size))
        # Copy invariant parameters
        self.dim = mask.dim
        self.vox_size = mask.vox_size
        # Displace the start and finish indices of the mask
        self.index_displacement = numpy.array(self.displacement / self.vox_size, dtype=numpy.int)
        self.start_index = mask.start_index + self.index_displacement
        self.finish_index = mask.finish_index + self.index_displacement
        # Set the offset and limit of the mask from the start and finish indices
        self.offset = mask.offset + self.displacement
        self.limit = mask.limit + self.displacement
        ## The actual mask array is the same as that of the original mask i.e. not a copy. \
        # This is the whole point of the DisplacedTree and DisplacedMasks, to avoid making \
        # unnecessary copies of this array.
        self._mask_array = mask._mask_array


class VolumeMask(Mask):

    def __init__(self, vox_size, tree_or_points, diams=None, dtype=bool):
        # Get tree (if provided instead of list of points), points and point extents from provided 
        # parameters
        tree, points, point_extents = Mask._parse_tree_points(tree_or_points, diams)
        # Call the base 'Mask' class constructor
        Mask.__init__(self, vox_size, points, point_extents, dtype)
        # For convenience calculate this here to save calculating it each iteration
        self.half_vox = self.vox_size / 2.0
        # Add the tree to the mask if it was provided
        if tree:
            self.add_tree(tree)

    def add_tree(self, tree):
        # Loop through all of the tree _point_data and "paint" the mask
        for seg in tree.segments:
            seg_radius = seg.diam / 2.0
            # Calculate the number of samples required for the current segment
            num_samples = numpy.ceil(norm(seg.end - seg.begin) *
                                  (SAMPLE_DIAM_RATIO / seg.diam))
            # Loop through the samples for the given segment and add their "point_mask" to the 
            # overall mask
            for frac in numpy.linspace(1, 0, num_samples, endpoint=False):
                # Set the point extent to be the segment diameter unless it is below the minimum along
                # that dimension
                point = (1.0 - frac) * seg.begin + frac * seg.end
                # Get the point in the reference frame of the mask
                offset_point = point - self.offset
                # Get an extent guaranteed to at least reach one voxel (but not extend into
                # two unless its radius is big enough) and set the extent about the current point 
                # to that or the segment radius depending on which is greater.
                point_extent = (offset_point + self.half_vox) % self.vox_size
                over_half = point_extent > self.half_vox
                point_extent[over_half] = self.vox_size[over_half] - point_extent[over_half]
                point_extent *= SQRT_3
                point_extent[point_extent < seg_radius] = seg_radius
                # Determine the extent of the mask indices that could be affected by the point
                extent_start = numpy.floor((offset_point - seg_radius) / self.vox_size)
                extent_finish = numpy.ceil((offset_point + seg_radius) / self.vox_size)
                # Get an "open" grid (uses less memory if it is open) of voxel indices to apply 
                # the distance function to.
                # (see http://docs.scipy.org/doc/numpy/reference/generated/numpy.ogrid.html)
                extent_indices = numpy.ogrid[int(extent_start[0]):int(extent_finish[0]),
                                          int(extent_start[1]):int(extent_finish[1]),
                                          int(extent_start[2]):int(extent_finish[2])]
                # Calculate the distances from each of the voxel centres to the given point
                dist = numpy.sqrt(((self.X[extent_indices] - point[0]) / point_extent[0]) ** 2 + \
                               ((self.Y[extent_indices] - point[1]) / point_extent[1]) ** 2 + \
                               ((self.Z[extent_indices] - point[2]) / point_extent[2]) ** 2)
                # Mask all _points that that are closer than the point diameter
                point_mask = dist < 1.0
                self._mask_array[extent_indices] += point_mask


class ConvolvedMask(Mask):

    __metaclass__ = ABCMeta # Declare this class abstract to avoid accidental construction

    def __init__(self, tree_or_points, kernel):
        tree, points, point_extents = Mask._parse_tree_points(tree_or_points) #@UnusedVariable
        # The extent around each point that will be > threshold        
        self._kernel = kernel
        # Call the base 'Mask' class constructor to set up the 
        Mask.__init__(self, kernel.vox_size, points, numpy.tile(kernel.extent,
                                                             (tree.num_points(), 1)), float)
        # Add the tree to the mask if it was provided
        if tree:
            self.add_tree(tree)

    def add_tree(self, tree):
        """
        Adds the tree to a given mask
        
        @param tree [tree.Tree]: The tree to draw the mask for
        @param vox_size [numpy.array(3)]: The size of the voxels
        @param kernel [method]: A method that takes a displacement vector and returns a value 
        """
        print "Generating mask..."
        # Loop through all of the tree _point_data and "paint" the mask
        for count, seg in enumerate(tree.segments):
            # Calculate the number of samples required for the current segment
            num_samples = numpy.ceil(norm(seg.end - seg.begin) * self._kernel.sample_freq)
            # Calculate how much to scale the 
            if num_samples:
                length_scale = norm(seg.end - seg.begin) / num_samples
            # Loop through the samples for the given segment and add their "point_mask" to the 
            # overal mask
            for frac in numpy.linspace(1, 0, num_samples, endpoint=False):
                point = (1.0 - frac) * seg.begin + frac * seg.end
                # Determine the extent of the mask indices that could be affected by the point
                extent_start = numpy.floor((point - self.offset - self._kernel.extent) / self.vox_size)
                extent_finish = numpy.array(numpy.ceil((point - self.offset + self._kernel.extent)
                                                 / self.vox_size), dtype=int)
                # Get an "open" grid (uses less memory if it is open) of voxel indices to apply 
                # the distance function to.
                # (see http://docs.scipy.org/doc/numpy/reference/generated/numpy.ogrid.html)
                extent_indices = numpy.ogrid[int(extent_start[0]):int(extent_finish[0]),
                                          int(extent_start[1]):int(extent_finish[1]),
                                          int(extent_start[2]):int(extent_finish[2])]
                # Get the displacements from the point to the voxel centres within the 
                # bounds of the extent.
                X = self.X[extent_indices]
                Y = self.Y[extent_indices]
                Z = self.Z[extent_indices]
                disps = numpy.vstack((X.ravel() - point[0], Y.ravel() - point[1],
                                   Z.ravel() - point[2])).transpose()
                # Get the values of the point-spread function at each of the voxel centres
                values = self._kernel(disps)
                # Add the point-spread function values to the mask_array
                self._mask_array[extent_indices] += length_scale * values.reshape(X.shape)
            if count % (tree.num_segments() // 10) == 0 and count != 0:
                print "Generating mask - {}% complete" \
                        .format(round(float(count) / float(tree.num_segments()) * 100))



#  Kernels to use in convolved masks ---------------------------------------------------------------

class Kernel(object):
    """
    Base class for kernels to passed to convolvedMask
    """

    __metaclass__ = ABCMeta # Declare this class abstract to avoid accidental construction

    def __call__(self, displacements):
        raise NotImplementedError("'__call__()' method should be implemented by derived class")

    @property
    def extent(self):
        raise NotImplementedError("'extent' property should be implemented by derived class")

    @property
    def vox_size(self):
        raise NotImplementedError("'vox_size' property should be implemented by derived class")


class GaussianKernel(Kernel):

    def __init__(self, vox_x, vox_y, vox_z, scale, decay_rate, threshold=GAUSS_THRESHOLD_DEFAULT,
                 isotropy=1.0, orient=(1.0, 0.0, 0.0), sample_freq=GAUSS_SAMPLE_FREQ_DEFAULT):
        if threshold >= 1.0:
            raise Exception ("Extent threshold must be < 1.0 (found '{}')".format(threshold))
        self._vox_size = numpy.array((vox_x, vox_y, vox_z))
        self._threshold = threshold
        self._scale = scale
        self._tensor = axially_symmetric_tensor(decay_rate, orient, isotropy)
        self.sample_freq = sample_freq
        # Calculate the extent of the kernel along the x,y, and z axes
        eig_vals, eig_vecs = numpy.linalg.eig(self._tensor)
        # Get the extent along each of the Eigen-vectors where the point-spread function reaches the
        # threshold, the extent along the "internal" axes of the kernel
        internal_extents = numpy.sqrt(-2.0 * math.log(self._threshold) / eig_vals)
        # Calculate the extent of the kernel along the x-y-z axes, the "external" axes
        self._extent = numpy.sqrt(numpy.sum((eig_vecs * internal_extents) ** 2, axis=1))

    def __call__(self, disps):
        # Calculate the Gaussian point spread function f = k * exp[-0.5 * d^t . W . d] for each 
        # displacement, where 'W' is the weights matrix and 'd' is a displacement vector
        values = self._scale * numpy.exp(-0.5 * numpy.sum(disps.dot(self._tensor) * disps, axis=1))
        # Threshold out all values that fall beneath the threshold used to determine the
        # extent of the required block of voxels. This removes the dependence on the orientation 
        # relative to the mask axes, where the kernels would otherwise be trimmed to
        values[values < self._threshold] = 0.0
        return values

    @property
    def extent(self):
        return self._extent

    @property
    def vox_size(self):
        return self._vox_size
