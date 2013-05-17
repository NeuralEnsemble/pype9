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
import pyNN.connectors
from ninemlp import XMLHandler
from ninemlp.connectivity import axially_symmetric_tensor
import itertools
from copy import deepcopy
try:
    import matplotlib.pyplot as plt
except:
    # If pyplot is not installed, ignore it and only throw an error if a plotting function is called
    plt = None

# Constants ----------------------------------------------------------------------------------------

GAUSS_THRESHOLD_DEFAULT = 0.02
SAMPLE_DIAM_RATIO = 4.0
GAUSS_SAMPLE_FREQ_DEFAULT = 100
DEEP_Z_VOX_SIZE = 10000 # This is the vox size used for the z axis to approximate infinite depth
# Pre-calculated for speed (not sure if this would be a bottleneck though)
SQRT_3 = math.sqrt(3)


class DisplacedVoxelSizeMismatchException(Exception): pass

#  Objects to store the morphologies ---------------------------------------------------------------

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
            soma_dict = read_NeurolucidaSomaXML(xml_filename)
            if not len(soma_dict):
                self.has_somas = False
            else:
                if len(soma_dict) != len(self.trees):
                    raise Exception("Number of loaded somas ({}) and trees do not match ({}) "
                                    .format(len(soma_dict), len(self.trees)))
                for label, soma in soma_dict.items():
                    self.trees[soma.index].add_soma(Soma(label, soma.contours))
                self.has_somas = True
        else:
            self.has_somas = False

    def __getitem__(self, index):
        return self.trees[index]

    def __iter__(self):
        for tree in self.trees:
            yield tree

    def __len__(self):
        return len(self.trees)

    def transform(self, transform):
        """
        Transforms the forest by the given transformation matrix
        
        @param transform [numpy.array(3,3)]: The transformation matrix by which to rotate the forest
        """
        for tree in self:
            tree.transform(transform)

    def rotate(self, theta, axis=2):
        """
        Rotates the forest about the chosen axis by theta 
        
        @param theta [float]: The degree of clockwise rotation (in degrees)
        @param axis [str/int]: The axis about which to rotate the tree (either 'x'-'z' or 0-2, default 'z'/2)
        """
        for tree in self:
            tree.rotate(theta, axis)

    def offset(self, offset):
        for tree in self:
            tree.offset(offset)

    def get_volume_mask(self, vox_size, dtype=bool):
        mask = VolumeMask(vox_size, np.vstack([tree.points for tree in self.trees]),
                          np.hstack([tree.diams for tree in self.trees]), dtype)
        if dtype == bool:
            for i, tree in enumerate(self):
                mask.add_tree(tree)
       #         print "Added {} tree to volume mask".format(i)
        else:
            bool_mask = VolumeMask(vox_size, np.vstack([tree.points for tree in self.trees]),
                                   np.hstack([tree.diams for tree in self.trees]), bool)
            for i, tree in enumerate(self):
                tree_mask = deepcopy(bool_mask)
                tree_mask.add_tree(tree)
                mask += tree_mask
        #        print "Added {} tree to volume mask".format(i)
        return mask

    def plot_volume_mask(self, vox_size, show=True, dtype=bool, colour_map=None):
        mask = self.get_volume_mask(vox_size, dtype)
        if not colour_map:
            if dtype == bool:
                colour_map = 'gray'
            else:
                colour_map = 'jet'
        mask.plot(show=show, colour_map=colour_map)

    def xy_coverage(self, vox_size, central_frac=(1.0, 1.0)):
        if len(vox_size) != 2:
            raise Exception("Voxel size needs to be 2-D (X and Y dimensions), found {}D"
                            .format(len(vox_size)))
        self.offset((0.0, 0.0, DEEP_Z_VOX_SIZE / 2.0))
        mask = self.get_volume_mask(vox_size + (DEEP_Z_VOX_SIZE,))
        if mask.dim[2] != 1:
            raise Exception("Not all voxels where contained with the \"deep\" z voxel dimension")
        trimmed_frac = (1.0 - np.array(central_frac)) / 2.0
        start = np.array(np.floor(mask.dim[:2] * trimmed_frac), dtype=int)
        end = np.array(np.ceil(mask.dim[:2] * (1.0 - trimmed_frac)), dtype=int)
        central_mask = mask._mask_array[start[0]:end[0], start[1]:end[1], 0].squeeze()
        coverage = float(np.count_nonzero(central_mask)) / float(np.prod(central_mask.shape))
        self.offset((0.0, 0.0, -DEEP_Z_VOX_SIZE / 2.0))
        return coverage, central_mask

    def normal_to_dendrites(self):
        avg = np.array((0.0, 0.0, 0.0))
        for tree in self:
            avg += tree.normal_to_dendrites()
        avg /= norm(avg)
        return avg

    def normal_to_soma_plane(self):
        if not self.has_somas:
            raise Exception("Forest does not include somas, so their normal is not defined")
        soma_centres = []
        for tree in self:
            soma_centres.append(tree.soma.centre())
        eig_vals, eig_vecs = np.linalg.eig(np.cov(soma_centres, rowvar=0)) #@UnusedVariable
        normal = eig_vecs[:, np.argmin(eig_vals)]
        if normal.sum() < 0:
            normal *= -1.0
        return normal

    def align_to_xyz_axes(self):
        soma_axis = self.normal_to_soma_plane()
        dendrite_axis = self.normal_to_dendrites()
        third_axis = np.cross(dendrite_axis, soma_axis)
        third_axis /= norm(third_axis) # Just to clean up any numerical errors
        re_dendrite_axis = np.cross(third_axis, soma_axis)
        align = np.vstack((soma_axis, third_axis, re_dendrite_axis))
        # As the align matrix is unitary its inverse is equivalent to its transpose
        inv_align = align.transpose();
        for tree in self:
            tree.transform(inv_align)
        return align

    def align_min_bound_to_origin(self):
        self.offset(-self.min_bounds)

    def collapse_to_origin(self):
        for tree in self:
            tree.offset(-tree.centroid)

    def randomize_trees(self):
        raise NotImplementedError

    def perturb(self, mag):
        for tree in self:
            tree.pertub(mag)


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

    def add_soma(self, soma):
        self.soma = soma

    def soma_position(self):
        if self.soma:
            pos = self.soma.centre
        else:
            pos = self._points[0, :]
        return pos

    @property
    def points(self):
        return self._points

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

    def transform(self, transform):
        """
        Transforms the tree by the given transformation matrix
        
        @param transform [numpy.array(3,3)]: The transformation matrix by which to rotate the tree
        """
        if transform.shape != (3, 3):
            raise Exception("Rotation matrix needs to be a 3 x 3 matrix (found {shape[0]} x "
                            "{shape[1]})".format(shape=transform.shape))
        # Rotate all the points in the tree
        self._points = np.dot(self._points, transform)
        # Clear masks, which will no longer match the rotated points
        self._masks.clear()

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

    def perturb(self, mag):
        self._points += np.random.randn(mag)

    def get_volume_mask(self, vox_size, dtype=bool):
        """
        Creates a mask for the given voxel sizes and saves it in self._masks
        
        @param vox_size [tuple(float)]: A 3-d list/tuple/array where each element is the voxel dimension or a single float for isotropic voxels
        """
        vox_size = Mask.parse_vox_size(vox_size)
        if not self._masks.has_key(vox_size):
            self._masks[vox_size] = VolumeMask(vox_size, self, dtype=dtype)
        return self._masks[vox_size]

    def get_mask(self, kernel):
        """
        Creates a mask for the given voxel sizes and saves it in self._masks
        
        @param vox_size [tuple(float)]: A 3-d list/tuple/array where each element is the voxel dimension or a single float for isotropic voxels
        
        """
        if not self._masks.has_key(kernel):
            self._masks[kernel] = ConvolvedMask(self, kernel)
        return self._masks[kernel]

    def displaced_tree(self, displacement):
        """
        Return displaced version of tree (a lightweight copy that borrows this tree's masks)
        
        @param displace [tuple(float)]: Displace to apply to the tree
        """
        return DisplacedTree(self, displacement)

    def offset(self, offset):
        """
        Unlike displaced tree, offset_tree moves all the points of the tree by the given offset 
        (invalidating all masks)
        
        @param displace [tuple(float)]: Displace to apply to the tree
        """
        if len(offset) != 3:
            raise Exception("Offset needs to be of length 3 (found {})".format(len(offset)))
        self._points += offset
        self._masks.clear()

    def num_overlapping(self, tree, vox_size):
        """
        Calculate the number of overlapping voxels between two trees
        
        @param tree [Tree]: The second tree to calculate the overlap with
        @param vox_size [tuple(float)]: The voxel sizes to use when calculating the overlap
        """
        overlap_mask = self.get_volume_mask(vox_size).overlap(tree.get_volume_mask(vox_size))
        return np.sum(overlap_mask)

    def connection_prob(self, tree, kernel):
        """
        Calculate the probability of there being any connection (there may be multiple)
        
        @param tree [Tree]: The second tree to calculate the overlap with
        @param kernel [Kernel]: The kernel used to define the probability masks
        """
        prob_mask = self.get_mask(kernel).overlap(tree.get_mask(kernel))
        return 1.0 - np.prod(prob_mask)

    def plot_volume_mask(self, vox_size, show=True, colour_map=None, dtype=bool):
        if not plt:
            raise Exception("Matplotlib could not be imported and therefore plotting functions "
                            "have been disabled")
        if not colour_map:
            if dtype == bool:
                colour_map = 'gray'
            else:
                colour_map = 'jet'
        mask = self.get_volume_mask(vox_size, dtype=dtype)
        mask.plot(show=show, colour_map=colour_map)

    def plot_prob_mask(self, vox_size, scale=1.0, orient=(1.0, 0.0, 0.0), decay_rate=0.1,
                       isotropy=1.0, threshold=GAUSS_THRESHOLD_DEFAULT, sample_freq=GAUSS_SAMPLE_FREQ_DEFAULT,
                       show=True, colour_map='jet'):
        mask = self.get_prob_mask(vox_size, scale, orient, decay_rate=decay_rate,
                                  isotropy=isotropy, threshold=threshold,
                                  sample_freq=sample_freq)
        mask.plot(show=show, colour_map=colour_map)

    def normal_to_dendrites(self, diam_threshold=1.5):
        """
        Calculate the normal to the plan for points on the dendritic tree that are above the 
        diameter threshold
        """
        # Select points with diameters below a certain threshold
        selected_points = self._points[self.diams < diam_threshold, :]
        # Get normal to the covariance matrix of these points
        eig_vals, eig_vecs = np.linalg.eig(np.cov(selected_points, rowvar=0))
        normal = eig_vecs[:, np.argmin(eig_vals)]
        # Ensure the normal is closer to the [1,1,1] vector than the [-1,-1,-1]
        if normal.sum() < 0:
            normal *= -1.0
        return normal


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

    def get_volume_mask(self, *mask_args):
        """
        Gets the volume mask for the given voxel size and sample diameter ratio. To avoid 
        duplications the mask is accessed from the original (undisplaced) tree, being created and 
        saved there if required.
        
        @param args: A 3-d list/tuple/array where each element is the voxel dimension or a single float for isotropic voxels
        """
        try:
            return self._undisplaced_tree.get_volume_mask(*mask_args).\
                                                                   displaced_mask(self.displacement)
        except DisplacedVoxelSizeMismatchException as e:
            raise Exception("Cannot get volume mask of displaced tree because its displacement {} "
                            "is not a multiple of the mask voxel sizes. {}"
                            .format(self.displacement, e))

    def get_mask(self, *mask_args):
        """
        Gets the convolved mask for the given voxel size and sample diameter ratio. 
        To avoid duplications the mask is accessed from the original (undisplaced) tree, being 
        created and saved there if required.
        
        @param vox_size [tuple(float)]: A 3-d list/tuple/array where each element is the voxel dimension or a single float for isotropic voxels
        """
        try:
            return self._undisplaced_tree.get_mask(*mask_args).displaced_mask(self.displacement)
        except DisplacedVoxelSizeMismatchException as e:
            raise Exception("Cannot get mask of displaced tree because its displacement {} is not a"
                            " multiple of the mask voxel sizes. {}".format(self.displacement, e))

    @property
    def points(self):
        return self._points + self.displacement

    @property
    def segments(self):
        for seg in self._undisplaced_tree.segments:
            yield Tree.Segment(seg.begin + self.displacement, seg.end + self.displacement, seg.diam)


class Soma(object):

    def __init__(self, label, contours):
        """
        Initialises the Soma object
        
        @param contours [list(NeurolucidaSomaXMLHandler.Contour)]: A list of contour objects
        """
        self.label = label
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

    @property
    def centre(self):
        avg = np.sum(self._points[:, :3], axis=0)
        return avg / norm(avg)


#  Mask objects to map the morphologies to arrays of data ------------------------------------------

class Mask(object):

    __metaclass__ = ABCMeta # Declare this class abstract to avoid accidental construction

    def __init__(self, vox_size, points, point_extents, dtype):
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
        #print self.offset,self.limit
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
        # Initialise the mask_array with the appropriate data type
        self._mask_array = np.zeros(self.dim, dtype=dtype)

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

    def plot(self, slice_dim=2, skip=1, show=True, colour_map=None, colour_bar=True):
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
            img = plt.imshow(np.squeeze(self._mask_array[slice_indices]),
                             cmap=plt.cm.get_cmap(colour_map))
            img.set_interpolation('nearest')
            plt.title('Dim {}, Index {}'.format(slice_dim, i))
            if self._mask_array.dtype != np.dtype('bool'):
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
        if type(tree_or_points) == Tree:
            tree = tree_or_points
            points = tree.points
            if diams:
                raise Exception("Diameters should only be provided if the 'tree_or_points' is an "
                                "array of points")
            diams = tree.diams
        elif type(tree_or_points) == np.ndarray and tree_or_points.shape[1] == 3:
            tree = None
            points = tree_or_points
            if points.shape[0] != len(diams):
                raise Exception("Number of points ({}) and length of diams ({}) do not match."
                                .format(points.shape[0], len(diams)))
        else:
            raise Exception("Incorrect type for 'tree_or_points' parameter ({}), must be either "
                            "'Tree' or numpy.array(N x 3)".format(type(tree_or_points)))
        point_extents = np.tile(np.reshape(diams / 2.0, (-1, 1)), (1, 3))
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
            num_samples = np.ceil(norm(seg.end - seg.begin) *
                                  (SAMPLE_DIAM_RATIO / seg.diam))
            # Loop through the samples for the given segment and add their "point_mask" to the 
            # overall mask
            for frac in np.linspace(1, 0, num_samples, endpoint=False):
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
                extent_start = np.floor((offset_point - seg_radius) / self.vox_size)
                extent_finish = np.ceil((offset_point + seg_radius) / self.vox_size)
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


class ConvolvedMask(Mask):

    __metaclass__ = ABCMeta # Declare this class abstract to avoid accidental construction

    def __init__(self, tree_or_points, kernel):
        tree, points, point_extents = Mask._parse_tree_points(tree_or_points) #@UnusedVariable
        # The extent around each point that will be > threshold        
        self._kernel = kernel
        # Call the base 'Mask' class constructor to set up the 
        Mask.__init__(self, kernel.vox_size, points, np.tile(kernel.extent,
                                                             (tree.num_points(), 1)), float)
        # Add the tree to the mask if it was provided
        if tree:
            self.add_tree(tree)

    def add_tree(self, tree):
        """
        Adds the tree to a given mask
        
        @param tree [Tree]: The tree to draw the mask for
        @param vox_size [np.array(3)]: The size of the voxels
        @param kernel [method]: A method that takes a displacement vector and returns a value 
        """
        print "Generating mask..."
        # Loop through all of the tree _point_data and "paint" the mask
        for count, seg in enumerate(tree.segments):
            # Calculate the number of samples required for the current segment
            num_samples = np.ceil(norm(seg.end - seg.begin) * self._kernel.sample_freq)
            # Calculate how much to scale the 
            if num_samples:
                length_scale = norm(seg.end - seg.begin) / num_samples
            # Loop through the samples for the given segment and add their "point_mask" to the 
            # overal mask
            for frac in np.linspace(1, 0, num_samples, endpoint=False):
                point = (1.0 - frac) * seg.begin + frac * seg.end
                # Determine the extent of the mask indices that could be affected by the point
                extent_start = np.floor((point - self.offset - self._kernel.extent) / self.vox_size)
                extent_finish = np.array(np.ceil((point - self.offset + self._kernel.extent)
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
        self._vox_size = np.array((vox_x, vox_y, vox_z))
        self._threshold = threshold
        self._scale = scale
        self._tensor = axially_symmetric_tensor(decay_rate, orient, isotropy)
        self.sample_freq = sample_freq
        # Calculate the extent of the kernel along the x,y, and z axes
        eig_vals, eig_vecs = np.linalg.eig(self._tensor)
        # Get the extent along each of the Eigen-vectors where the point-spread function reaches the
        # threshold, the extent along the "internal" axes of the kernel
        internal_extents = np.sqrt(-2.0 * math.log(self._threshold) / eig_vals)
        # Calculate the extent of the kernel along the x-y-z axes, the "external" axes
        self._extent = np.sqrt(np.sum((eig_vecs * internal_extents) ** 2, axis=1))

    def __call__(self, disps):
        # Calculate the Gaussian point spread function f = k * exp[-0.5 * d^t . W . d] for each 
        # displacement, where 'W' is the weights matrix and 'd' is a displacement vector
        values = self._scale * np.exp(-0.5 * np.sum(disps.dot(self._tensor) * disps, axis=1))
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


#  Extensions to the PyNN connector classes required to use morphology based connectivity ----------

class ConnectionProbabilityMatrix(object):
    """
    The connection probability matrix between two morphologies
    """

    def __init__(self, B, kernel, mask=None):
        self.A = None
        self._prob_matrix = None
        self.kernel = kernel
        if mask is not None:
            self.B = list(itertools.compress(B, mask))
        else:
            self.B = B

    def set_source(self, A):
        self.A = A
        self._prob_matrix = None

    def as_array(self, sub_mask=None):
        if self._prob_matrix is None and self.A is not None:
            B = self.B if sub_mask is None else list(itertools.compress(self.B, sub_mask))
            self._prob_matrix = np.zeros(len(B))
            for i in xrange(len(B)):
                self._prob_matrix[i] = self.A.connection_prob(B[i], self.kernel)
        return self._prob_matrix


#class ProbabilisticConnector(pyNN.connectors.ProbabilisticConnector):
#
#    def __init__(self, projection, weights=0.0, delays=None,
#                 allow_self_connections=True, space=pyNN.connectors.Space(), safe=True):
#        pyNN.connectors.ProbabilisticConnector.__init__(self, projection=projection,
#                                                        weights=weights, delays=delays,
#                                                        allow_self_connections=allow_self_connections,
#                                                        space=space, safe=safe)
#
#    def _set_distance_matrix(self, src):
#        morphology = src.parent.morphologies[src.parent.id_to_index(src)]
#        if self.prepare_sources and src.local:
#            self.full_distance_matrix.set_source(morphology)
#        else:
#            self.distance_matrix.set_source(morphology)
#
#    @property
#    def distance_matrix(self):
#        """
#        We want to avoid calculating positions if it is not necessary, so we
#        delay it until the distance matrix is actually used.
#        """
#        if self._distance_matrix is None:
#            self._distance_matrix = ConnectionProbabilityMatrix(self.projection.post.morphologies,
#                                                                self.space, self.local)
#        return self._distance_matrix
#
#    @property
#    def full_distance_matrix(self):
#        """
#        We want to avoid calculating positions if it is not necessary, so we
#        delay it until the distance matrix is actually used.
#        """
#        if self._full_distance_matrix is None:
#            self._full_distance_matrix = ConnectionProbabilityMatrix(self.projection.post.morphologies,
#                                                                     self.space, self.full_mask)
#        return self._full_distance_matrix

#
#class MorphologyBasedProbabilityConnector(pyNN.connectors.DistanceDependentProbabilityConnector):
#    """
#    For each pair of pre-post cells, the connection probability depends on distance.
#    """
#    parameter_names = ('allow_self_connections', 'd_expression')
#
#    #Override the base classes Probabilistic connector to use the morphologies
#    ProbConnector = ProbabilisticConnector
#
#    def __init__(self, kernel, allow_self_connections=True,
#                 weights=0.0, delays=None, safe=True, verbose=False, n_connections=None):
#        # This is a right hack, as I am using the "space" object to pass the kernel, which then 
#        # returns the probability in the distance matrix instead of the distance, hence the d_expression
#        # is just 'd'
#        super(MorphologyBasedProbabilityConnector, self).__init__('d', 
#                allow_self_connections=allow_self_connections, weights=weights, delays=delays,
#                space=kernel, safe=safe, verbose=verbose, n_connections=n_connections)


#  Handlers to load the morphologies from Neurolucida xml files ------------------------------------

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
    Soma = collections.namedtuple('Soma', 'index contours')
    Contour = collections.namedtuple('Contour', 'points')
    Point = collections.namedtuple('Point', 'x y z diam')

    def __init__(self):
        """
        Initialises the handler, saving the cell name and creating the lists to hold the _point_data 
        and segment groups.
        """
        XMLHandler.__init__(self)
        self.somas = {}
        self.soma_count = 0

    def startElement(self, tag_name, attrs):
        """
        Overrides function in xml.sax.handler to parse all MorphML tag openings. Creates 
        corresponding segment and segment-group tuples in the handler object.
        """
        if self._opening(tag_name, attrs, 'contour'):
            contour_name = attrs['name']
            if not self.somas.has_key(contour_name):
                self.somas[contour_name] = self.Soma(self.soma_count, [])
                self.soma_count += 1
            self.current_contour = self.Contour([])
            self.somas[contour_name].contours.append(self.current_contour)
        elif self._opening(tag_name, attrs, 'point', parents=[('contour')]):
            self.current_contour.points.append(self.Point(attrs['x'], attrs['y'], attrs['z'],
                                                          attrs['d']))


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



#  Testing functions -------------------------------------------------------------------------------

if __name__ == '__main__':
    VOX_SIZE = (0.1, 0.1, 500)
    from os.path import normpath, join
    from ninemlp import SRC_PATH
    print "Loading forest..."
#    forest = Forest(normpath(join(SRC_PATH, '..', 'morph', 'Purkinje', 'xml',
#                                  'GFP_P60.1_slide7_2ndslice-HN-FINAL.xml')))
    forest = Forest(normpath(join(SRC_PATH, '..', 'morph', 'Purkinje', 'xml',
                                  'tree2.xml')), include_somas=False)
    print "Finished loading forest."
    forest.offset((0.0, 0.0, -250))
#    forest.plot_volume_mask(VOX_SIZE, show=False, dtype=int)
#    plt.title('Original rotation')
#    print forest.align_to_xyz_axes()
    # To move the forest away from zero so it is contained with in one z voxel    
    forest.plot_volume_mask(VOX_SIZE, show=False, dtype=int)
    plt.title('Aligned rotation')
#    coverage, central_mask = forest.xy_coverage(VOX_SIZE[:2], (1.0, 1.0))
#    img = plt.imshow(central_mask, cmap=plt.cm.get_cmap('gray'))
#    img.set_interpolation('nearest')
#    print "Coverage: {}".format(coverage)
    plt.show()
