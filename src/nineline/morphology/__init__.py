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
from __future__ import absolute_import
from abc import ABCMeta # Metaclass for abstract base classes
import math
import numpy
from numpy.linalg import norm
import collections
import xml.sax
import pyNN.connectors
from nineline import XMLHandler
from ..__init__ import axially_symmetric_tensor
import itertools
from .forest import Forest
from .mask import VolumeMask
from .tree import Tree
from copy import deepcopy
try:
    import matplotlib.pyplot as plt
except:
    # If pyplot is not installed, ignore it and only throw an error if a plotting function is called
    plt = None


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
            self._prob_matrix = numpy.zeros(len(B))
            for i in xrange(len(B)):
                self._prob_matrix[i] = self.A.connection_prob(B[i], self.kernel)
        return self._prob_matrix


class MorphologyBasedProbabilityConnector(pyNN.connectors.IndexBasedProbabilityConnector):
            
    class KernelOverlapExpression(pyNN.connectors.IndexBasedExpression):
        """
        The kernel used to determine the connection probability between an axonal and dendritic
        tree.  
        """
        def __init__(self, pre_kernel, post_kernel):
            """
            `disp_function`: a function that takes a 3xN numpy position matrix and maps each row
                             (displacement) to a probability between 0 and 1
            """
            self._pre_kernel = pre_kernel
            self._post_kernel = post_kernel
                        
        def __call__(self, pre_indices, post_index):
            try:
                post_morph = self.projection.post.morphologies[post_index]
                pre_morphs = self.projection.pre.morphologies[pre_indices]
            except AttributeError:
                raise pyNN.errors.ConnectionError("Pre and/or post-synaptic projections do not have"
                                                  " cell morphologies")
            probs = numpy.empty(len(pre_indices))
            for i, pre_morph in enumerate(pre_morphs):
                probs[i] = pre_morph.connection_prob(post_morph, self._pre_kernel, self._post_kernel)
            return probs             
            
    def __init__(self, pre_kernel, post_kernel, allow_self_connections=True,
                 rng=None, safe=True, callback=None):
        super(MorphologyBasedProbabilityConnector, self).__init__(
                self.KernelOverlapExpression(pre_kernel, post_kernel), 
                allow_self_connections=allow_self_connections, safe=safe, rng=rng, callback=callback)


#  Testing functions -------------------------------------------------------------------------------

if __name__ == '__main__':
    import nineline.geometry.morphology
#     VOX_SIZE = (0.1, 0.1, 500)
#     from os.path import normpath, join
#     print "Loading forest..."
# #    forest = Forest(normpath(join(SRC_PATH, '..', 'morph', 'Purkinje', 'xml',
# #                                  'GFP_P60.1_slide7_2ndslice-HN-FINAL.xml')))
#     forest = Forest(normpath(join('home','tclose','git','kbrain', 'morph', 'Purkinje', 'xml',
#                                   'tree2.xml')), include_somas=False)
#     print "Finished loading forest."
#     forest.offset((0.0, 0.0, -250))
# #    forest.plot_volume_mask(VOX_SIZE, show=False, dtype=int)
# #    plt.title('Original rotation')
# #    print forest.align_to_xyz_axes()
#     # To move the forest away from zero so it is contained with in one z voxel    
#     forest.plot_volume_mask(VOX_SIZE, show=False, dtype=int)
#     plt.title('Aligned rotation')
# #    coverage, central_mask = forest.xy_coverage(VOX_SIZE[:2], (1.0, 1.0))
# #    img = plt.imshow(central_mask, cmap=plt.cm.get_cmap('gray'))
# #    img.set_interpolation('nearest')
# #    print "Coverage: {}".format(coverage)
#     plt.show()
