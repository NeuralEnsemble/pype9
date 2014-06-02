"""

  This module defines classes to be passed pyNN Connectors to connect populations based on
  simple point-to-point geometric connectivity rules

  @author Tom Close


"""
##########################################################################
#
#    Copyright 2011 Okinawa Institute of Science and Technology (OIST), Okinawa, Japan
#
##########################################################################
from __future__ import absolute_import
import numpy
import collections
from . import mask
from .io.neurolucida import read_NeurolucidaTreeXML

try:
    import matplotlib.pyplot as plt
except:
    # If pyplot is not installed, ignore it and only throw an error if a
    # plotting function is called
    plt = None

# try:
#     from pyface.qt import QtGui, QtCore
#     from PyQt4 import uic
#
#     from traits.api import HasTraits, Instance, on_trait_change, \
#         Int, Dict
#     from traitsui.api import View, Item
#     from mayavi.core.ui.api import MayaviScene, MlabSceneModel, \
#             SceneEditor
#     from mayavi import mlab
#
#     ################################################################################
# The actual visualization
#     class Visualization(HasTraits):
#         scene = Instance(MlabSceneModel, ())
#
#         @on_trait_change('scene.activated')
#         def update_plot(self):
# This function is called when the view is opened. We don't
# populate the scene when the view is not yet open, as some
# VTK features require a GLContext.
#
# We can do normal mlab calls on the embedded scene.
# self.scene.mlab.test_points3d()
#             pass
#
# the layout of the dialog screated
#         view = View(Item('scene', editor=SceneEditor(scene_class=MayaviScene),
#                          height=400, width=500, show_label=False),
# resizable=True # We need this to resize with the parent widget
#                     )
#
# The QWidget containing the visualization, this is pure PyQt4 code.
#     class MayaviQWidget(QtGui.QWidget):
#         def __init__(self, parent=None):
#             QtGui.QWidget.__init__(self, parent)
#             layout = QtGui.QVBoxLayout(self)
#             layout.setContentsMargins(0,0,0,0)
#             layout.setSpacing(0)
#             self.visualization = Visualization()
#
# If you want to debug, beware that you need to remove the Qt
# input hook.
# QtCore.pyqtRemoveInputHook()
# import pdb ; pdb.set_trace()
# QtCore.pyqtRestoreInputHook()
#
# The edit_traits call will generate the widget to embed.
#             self.ui = self.visualization.edit_traits(parent=self,
#                                                      kind='subpanel').control
#             layout.addWidget(self.ui)
#             self.ui.setParent(self)
# except:
mlab = None


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
        self.connected_segments = []
        self._flatten(root)
        # Convert flattened lists to numpy arrays
        self._points = numpy.array(self._points)
        self.diams = numpy.array(self.diams)
        # Calculate bounds used in determining mask dimensions
        tiled_diams = numpy.transpose(numpy.tile(self.diams, (3, 1)))
        self.min_bounds = numpy.min(self.points - tiled_diams, axis=0)
        self.max_bounds = numpy.max(self.points + tiled_diams, axis=0)
        self.centroid = numpy.average(self.points, axis=0)
        # Create dictionaries to store tree masks to save having to regenerate
        # them the next time
        self._masks = collections.defaultdict(dict)

    @classmethod
    def load_neurolucidaXML(cls, filename):
        roots = read_NeurolucidaTreeXML(filename)
        if len(roots) > 1:
            raise Exception(
                "More than one tree loaded from file '{}'".format(filename))
        return cls(roots[0])

    def _flatten(self, branch, prev_index=-1):
        """
        A recursive algorithm to flatten the loaded tree into a numpy array of _points used in the
        tree constructor.

        @param branch[NeurolucidaTreeXMLHandler.Branch]: The loaded branch
        @param point_index [int]: the index (point count) of the current point
        @param prev_index [int]: the index of the previous point (-1 signifies no previous point, i.e the segment is a root node)
        """
        connected = []
        for point in branch.points:
            index = len(self._points)
            self._points.append(point[0:3])
            self.diams.append(point[3])
            self._prev_indices.append(prev_index)
            connected.append(index)
            prev_index = index
        self.connected_segments.append(numpy.array(connected))
        for branch in branch.sub_branches:
            self._flatten(branch, prev_index)

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

    @property
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
                yield self.Segment(self._points[prev_index, :], self.points[i,:], diam)

    @property
    def num_segments(self):
        return len(self._points) - 1

    def transform(self, transform):
        """
        Transforms the tree by the given transformation matrix

        @param transform [numpy.array(3,3)]: The transformation matrix by which to rotate the tree
        """
        if transform.shape != (3, 3):
            raise Exception("Rotation matrix needs to be a 3 x 3 matrix (found {shape[0]} x "
                            "{shape[1]})".format(shape=transform.shape))
        # Rotate all the points in the tree
        self._points = numpy.dot(self._points, transform)
        # Clear masks, which will no longer match the rotated points
        self._masks.clear()

    def rotate(self, theta, axis=2):
        """
        Rotates the tree about the chosen axis by theta

        @param theta [float]: The degree of clockwise rotation (in degrees)
        @param axis [str/int]: The axis about which to rotate the tree (either 'x'-'z' or 0-2, default 'z'/2)
        """
        # Convert theta to radians
        theta_rad = theta * 2 * numpy.pi / 360.0
        # Precalculate the sine and cosine
        cos_theta = numpy.cos(theta_rad)
        sin_theta = numpy.sin(theta_rad)
        # Get appropriate rotation matrix
        if axis == 0 or axis == 'x':
            rotation_matrix = numpy.array([[1, 0, 0],
                                           [0, cos_theta, -sin_theta],
                                           [0, sin_theta, cos_theta]])
        elif axis == 1 or axis == 'y':
            rotation_matrix = numpy.array([[cos_theta, 0, sin_theta],
                                           [0, 1, 0],
                                           [-sin_theta, 0, cos_theta]])
        elif axis == 2 or axis == 'z':
            rotation_matrix = numpy.array([[cos_theta, -sin_theta, 0],
                                           [sin_theta, cos_theta, 0],
                                           [0, 0, 1]])
        else:
            raise Exception(
                "'axis' argument must be either 0-2 or 'x'-'y' (found {})".format(axis))
        # Rotate all the points in the tree
        self._points = numpy.dot(self._points, rotation_matrix)
        # Clear masks, which will no longer match the rotated points
        self._masks.clear()

    def perturb(self, mag):
        self._points += numpy.random.randn(mag)

    def get_volume_mask(self, vox_size, dtype=bool):
        """
        Creates a mask for the given voxel sizes and saves it in self._masks

        @param vox_size [tuple(float)]: A 3-d list/tuple/array where each element is the voxel dimension or a single float for isotropic voxels
        """
        vox_size = mask.Mask.parse_vox_size(vox_size)
        if vox_size not in self._masks:
            self._masks[vox_size] = mask.VolumeMask(
                vox_size, self, dtype=dtype)
        return self._masks[vox_size]

    def get_mask(self, kernel):
        """
        Creates a mask for the given voxel sizes and saves it in self._masks

        @param vox_size [tuple(float)]: A 3-d list/tuple/array where each element is the voxel dimension or a single float for isotropic voxels

        """
        if kernel not in self._masks:
            self._masks[kernel] = mask.ConvolvedMask(self, kernel)
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
            raise Exception(
                "Offset needs to be of length 3 (found {})".format(len(offset)))
        self._points += offset
        self._masks.clear()

    def num_overlapping(self, tree, vox_size):
        """
        Calculate the number of overlapping voxels between two trees

        @param tree [Tree]: The second tree to calculate the overlap with
        @param vox_size [tuple(float)]: The voxel sizes to use when calculating the overlap
        """
        overlap_mask = self.get_volume_mask(
            vox_size).overlap(tree.get_volume_mask(vox_size))
        return numpy.sum(overlap_mask)

    def connection_prob(self, tree, kernel1, kernel2):
        """
        Calculate the probability of there being any connection (there may be multiple)

        @param tree [Tree]: The second tree to calculate the overlap with
        @param kernel [Kernel]: The kernel used to define the probability masks
        """
        prob_mask = self.get_mask(kernel1).overlap(tree.get_mask(kernel2))
        return 1.0 - numpy.prod(prob_mask)

    def plot_volume_mask(
            self, vox_size, show=True, colour_map=None, dtype=bool):
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
                       isotropy=1.0, threshold=mask.GAUSS_THRESHOLD_DEFAULT,
                       sample_freq=mask.GAUSS_SAMPLE_FREQ_DEFAULT, show=True, colour_map='jet'):
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
        eig_vals, eig_vecs = numpy.linalg.eig(
            numpy.cov(selected_points, rowvar=0))
        normal = eig_vecs[:, numpy.argmin(eig_vals)]
        # Ensure the normal is closer to the [1,1,1] vector than the [-1,-1,-1]
        if normal.sum() < 0:
            normal *= -1.0
        return normal

    def plot3D(self, mayavi):
        "Draw the surface the first time"

        f = mlab.figure(1, bgcolor=(0, 0, 0))

#         for tube_indices in self.connected_segments:
#             points = self.points[tube_indices,:]
#             diam = numpy.average(self.diams[tube_indices])
#             surface = mlab.plot3d(points[:,0], points[:,1], points[:,2], tube_radius=diam,
#                                   colormap='Greys')
#         return f
        # rendering disabled
        mayavi.visualization.scene.disable_render = True

        points = mlab.pipeline.scalar_scatter(self.points[:, 0], self.points[:, 1], self.points[:, 2],
                                              self.diams / 2.0)

        dataset = points.mlab_source.dataset
        dataset.point_data.get_array(0).name = 'diameter'
        dataset.lines = numpy.hstack((numpy.reshape(numpy.arange(self.num_points - 1), (1, -1)),
                                      numpy.reshape(self._prev_indices[2:], (1, -1))))
        dataset.point_data.update()

        # The tube
        src = mlab.pipeline.set_active_attribute(
            points, point_scalars='diameter')
        stripper = mlab.pipeline.stripper(src)
        tube = mlab.pipeline.tube(stripper, tube_sides=6, tube_radius=1)
        tube.filter.capping = True
#        tube.filter.use_default_normal = False
        tube.filter.vary_radius = 'vary_radius_by_absolute_scalar'

#         array_id = dataset.point_data.add_array(1.0)
#         dataset.point_data.get_array(array_id).name = 'none'
#         dataset.point_data.update()
        src2 = mlab.pipeline.set_active_attribute(tube,
                                                  point_scalars='none')
        self.surf = mlab.pipeline.surface(src2, colormap='blue-red')

        # ReEnable the rendering
#         mayavi.visualization.scene.disable_render = False
        return (tube, dataset)


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
        self.displacement = numpy.array(displacement)
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
        except mask.DisplacedVoxelSizeMismatchException as e:
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
            return self._undisplaced_tree.get_mask(
                *mask_args).displaced_mask(self.displacement)
        except mask.DisplacedVoxelSizeMismatchException as e:
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
        self._points = numpy.zeros((num_points, 4))
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
        avg = numpy.sum(self._points[:, :3], axis=0)
        return avg / numpy.norm(avg)
