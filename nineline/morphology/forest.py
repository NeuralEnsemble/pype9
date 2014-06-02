"""
  This package reads a "forest" of dendritic (or axonal) trees and generates
  connectivity patterns from them

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the GPL v2, see LICENSE for details.
"""
from __future__ import absolute_import
import numpy
from numpy.linalg import norm
from . import tree
from copy import deepcopy
from . import mask
from .io.neurolucida import read_NeurolucidaTreeXML, read_NeurolucidaSomaXML
try:
    import matplotlib.pyplot as plt
except:
    # If pyplot is not installed, ignore it and only throw an error if a
    # plotting function is called
    plt = None


class Forest(object):

    def __init__(self, xml_filename, include_somas=True):
        # Load dendritic trees
        roots = read_NeurolucidaTreeXML(xml_filename)
        self.trees = []
        for root in roots:
            self.trees.append(tree.Tree(root))
        self.centroid = numpy.zeros(3)
        self.min_bounds = numpy.ones(3) * float('inf')
        self.max_bounds = numpy.ones(3) * float('-inf')
        for tree in self.trees:
            self.centroid += tree.centroid
            self.min_bounds = numpy.select([self.min_bounds <= tree.min_bounds,
                                            True],
                                           [self.min_bounds, tree.min_bounds])
            self.max_bounds = numpy.select([self.max_bounds >= tree.max_bounds,
                                            True],
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
                    raise Exception("Number of loaded somas ({}) and trees "
                                    "do not match ({}) "
                                    .format(len(soma_dict), len(self.trees)))
                for label, soma in soma_dict.items():
                    self.trees[soma.index].add_soma(
                        tree.Soma(label, soma.contours))
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

        @param transform [numpy.array(3,3)]: The transformation matrix by
                                             which to rotate the forest
        """
        for tree in self:
            tree.transform(transform)

    def rotate(self, theta, axis=2):
        """
        Rotates the forest about the chosen axis by theta

        @param theta [float]: The degree of clockwise rotation (in degrees)
        @param axis [str/int]: The axis about which to rotate the tree (either
                               'x'-'z' or 0-2, default 'z'/2)
        """
        for tree in self:
            tree.rotate(theta, axis)

    def offset(self, offset):
        for tree in self:
            tree.offset(offset)

    def get_volume_mask(self, vox_size, dtype=bool):
        mask = mask.VolumeMask(vox_size, numpy.vstack([tree.points
                                                      for tree in self.trees]),
                               numpy.hstack([tree.diams
                                             for tree in self.trees]), dtype)
        if dtype == bool:
            for i, tree in enumerate(self):  # @UnusedVariable
                mask.add_tree(tree)
#         print "Added {} tree to volume mask".format(i)
        else:
            bool_mask = mask.VolumeMask(vox_size,
                                        numpy.vstack([tree.points
                                                      for tree in self.trees]),
                                        numpy.hstack([tree.diams
                                                      for tree in self.trees]),
                                        bool)
            for i, tree in enumerate(self):  # @UnusedVariable
                tree_mask = deepcopy(bool_mask)
                tree_mask.add_tree(tree)
                mask += tree_mask
        #        print "Added {} tree to volume mask".format(i)
        return mask

    def plot_volume_mask(
            self, vox_size, show=True, dtype=bool, colour_map=None):
        mask = self.get_volume_mask(vox_size, dtype)
        if not colour_map:
            if dtype == bool:
                colour_map = 'gray'
            else:
                colour_map = 'jet'
        mask.plot(show=show, colour_map=colour_map)

    def xy_coverage(self, vox_size, central_frac=(1.0, 1.0)):
        if len(vox_size) != 2:
            raise Exception("Voxel size needs to be 2-D (X and Y dimensions), "
                            "found {}D".format(len(vox_size)))
        self.offset((0.0, 0.0, mask.DEEP_Z_VOX_SIZE / 2.0))
        mask = self.get_volume_mask(vox_size + (mask.DEEP_Z_VOX_SIZE,))
        if mask.dim[2] != 1:
            raise Exception("Not all voxels where contained with the \"deep\" "
                            "z voxel dimension")
        trimmed_frac = (1.0 - numpy.array(central_frac)) / 2.0
        start = numpy.array(
            numpy.floor(mask.dim[:2] * trimmed_frac), dtype=int)
        end = numpy.array(
            numpy.ceil(mask.dim[:2] * (1.0 - trimmed_frac)), dtype=int)
        central_mask = mask._mask_array[
            start[0]:end[0], start[1]:end[1], 0].squeeze()
        coverage = (float(numpy.count_nonzero(central_mask)) /
                    float(numpy.prod(central_mask.shape)))
        self.offset((0.0, 0.0, -mask.DEEP_Z_VOX_SIZE / 2.0))
        return coverage, central_mask

    def normal_to_dendrites(self):
        avg = numpy.array((0.0, 0.0, 0.0))
        for tree in self:
            avg += tree.normal_to_dendrites()
        avg /= norm(avg)
        return avg

    def normal_to_soma_plane(self):
        if not self.has_somas:
            raise Exception("Forest does not include somas, so their normal is"
                            " not defined")
        soma_centres = []
        for tree in self:
            soma_centres.append(tree.soma.centre())
        eig_vals, eig_vecs = numpy.linalg.eig(
            numpy.cov(soma_centres, rowvar=0))  # @UnusedVariable
        normal = eig_vecs[:, numpy.argmin(eig_vals)]
        if normal.sum() < 0:
            normal *= -1.0
        return normal

    def align_to_xyz_axes(self):
        soma_axis = self.normal_to_soma_plane()
        dendrite_axis = self.normal_to_dendrites()
        third_axis = numpy.cross(dendrite_axis, soma_axis)
        third_axis /= norm(third_axis)  # Just to clean up any numerical errors
        re_dendrite_axis = numpy.cross(third_axis, soma_axis)
        align = numpy.vstack((soma_axis, third_axis, re_dendrite_axis))
        # As the align matrix is unitary its inverse is equivalent to its
        # transpose
        inv_align = align.transpose()
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
