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
from warnings import warn
from ninemlp.connectivity import axially_symmetric_tensor

class InsufficientTargetsWarning(Warning): pass

#TOD: Should be able to specify axes for each of these geometries to align to

class LinearWithDistance(object):

    def __init__(self, scalar, offset=0.0, min_value=0.0):
        self.scalar = scalar
        self.offset = offset
        self.min_value = min_value

    def __call__(self, dist):
        values = self.offset + self.scalar * dist
        if self.min_value:
            values[values < self.min_value] = self.min_value
        return values

    @classmethod
    def expand_distances(cls):
        return False


class ExponentialWithDistance(object):

    def __init__(self, scalar, exponent, offset=0.0, min_value=0.0):
        self.scalar = scalar
        self.exponent = exponent
        self.offset = offset
        self.min_value = min_value

    def __call__(self, dist):
        values = self.offset + self.scalar * np.exp(self.exponent * dist)
        if self.min_value:
            values[values < self.min_value] = self.min_value
        return values

    @classmethod
    def expand_distances(cls):
        return False


class BoltzmanWithDistance(object):

    def __init__(self, a1, a2, x0, dx, min_value=0.0):
        self.a1 = a1
        self.a2 = a2
        self.x0 = x0
        self.dx = dx
        self.min_value = min_value

    def __call__(self, dist):
        values = (self.a1 - self.a2) / (1 + np.exp ((dist - self.x0) / self.dx)) + self.a2
        if self.min_value:
            values[values < self.min_value] = self.min_value
        return values

    @classmethod
    def expand_distances(cls):
        return False


class LinearWith2DDistance(object):

    def __init__(self, scalar, offset=0.0, min_value=0.0):
        self.scalar = scalar
        self.offset = offset
        self.min_value = min_value

    def __call__(self, disp):
        dist2D = np.sqrt(np.sum(np.square(disp[0:2, :]), axis=0))
        values = self.offset + self.scalar * dist2D
        if self.min_value:
            values[values < self.min_value] = self.min_value
        return values

    @classmethod
    def expand_distances(cls):
        return True


class ExponentialWith2DDistance(object):

    def __init__(self, scalar, exponent, offset=0.0, min_value=0.0):
        self.scalar = scalar
        self.exponent = exponent
        self.offset = offset
        self.min_value = min_value

    def __call__(self, disp):
        dist2D = np.sqrt(np.sum(np.square(disp[0:2, :]), axis=0))
        values = self.offset + self.scalar * np.exp(self.exponent * dist2D)
        if self.min_value:
            values[values < self.min_value] = self.min_value
        return values

    @classmethod
    def expand_distances(cls):
        return True


class MaskBased(object):

    def __init__(self, probability=None, number=None):

        if (probability is not None and number is not None):
            raise Exception ("Only one of probability ({}) and number can be supplied to Mask object")
        self.prob = probability
        self.number = number

    def _probs_from_mask(self, mask):
        if self.prob:
            prob = self.prob
        else:
            if not self.number: # If both self.prob and self.number are None (the default).
                prob = 1.0      # all cells within the mask will be connected.
            else:
                num_nz = np.count_nonzero(mask)
                if num_nz:
                    prob = self.number / num_nz
                else:
                    prob = float('inf')
            # If probability exceeds 1 cap it at 1 as the best that can be done
            if prob > 1.0:
                warn("The number of requested connections ({}) could not be satisfied given "
                     "size of mask ({})".format(int(self.number), num_nz),
                     InsufficientTargetsWarning)
                prob = 1.0
        probs = np.zeros(mask.shape)
        probs[mask] = prob
        return probs


class CylinderMask(MaskBased):
    """
    A class designed to be passed to the pyNN.DistanceBasedProbabilityConnector to determine the 
    probabilityability of connection within an elliptical region
    """

    def __init__(self, radius, probability=None, axisX=0.0, axisY=0.0, axisZ=1.0, number=None):
        """
        @param radius: radius of the circle 
        @param number: the mean number of connections to be generated. If None, all cells within the mask will be connected
        """
        super(CylinderMask, self).__init__(probability, number)
        self.radius = radius
        self.axis = np.array((axisX, axisY, axisZ))
        norm = np.linalg.norm(self.axis)
        if not norm:
            raise Exception("Zero length vector provided as axis of CylinderMask.")
        self.axis /= norm

    def __call__(self, d):
        mask = np.sqrt(np.sum(np.square(np.cross(self.axis, d, axis=0), axis=0))) < self.radius
        return self._probs_from_mask(mask)

    @classmethod
    def expand_distances(cls):
        return True


class SphereMask(MaskBased):
    """
    A class designed to be passed to the pyNN.DistanceBasedProbabilityConnector to determine the 
    probabilityability of connection within an elliptical region
    """

    def __init__(self, radius, probability=None, number=None):
        """
        @param radius: radius of the sphere 
        @param number: the mean number of connections to be generated. If None, all cells within the mask will be connected
        """
        super(SphereMask, self).__init__(probability, number)
        self.radius = radius

    def __call__(self, dist):
        mask = dist < self.radius
        return self._probs_from_mask(mask)

    @classmethod
    def expand_distances(cls):
        return False


class EllipseMask(MaskBased):
    """
    A class designed to be passed to the pyNN.DistanceBasedProbabilityConnector to determine the 
    probabilityability of connection within an elliptical region
    """

    def __init__(self, x_scale, y_scale, probability=None, number=None):
        """
        @param x: scale of the x axis of the ellipse
        @param y: scale of the y axis of the ellipse        
        @param number: the mean number of connections to be generated. If None, all cells within the mask will be connected
        """
        super(EllipseMask, self).__init__(probability, number)
        self.x_scale = x_scale
        self.y_scale = y_scale

    def __call__(self, d):
        mask = np.square(d[0] / self.x_scale) + np.square(d[1] / self.y_scale) < 1
        return self._probs_from_mask(mask)

    @classmethod
    def expand_distances(cls):
        return True


class OldEllipsoidMask(MaskBased):
    """
    A class designed to be passed to the pyNN.DistanceBasedProbabilityConnector to determine the 
    probabilityability of connection within an elliptical region
    """

    def __init__(self, x_scale, y_scale, z_scale, probability=None, number=None):
        """
        @param x: scale of the x axis of the ellipse
        @param y: scale of the y axis of the ellipse        
        @param number: the mean number of connections to be generated. If None, all cells within the mask will be connected
        """
        super(OldEllipsoidMask, self).__init__(probability, number)
        self.x_scale = x_scale
        self.y_scale = y_scale
        self.z_scale = z_scale

    def __call__(self, d):
        mask = np.square(d[0] / self.x_scale) + np.square(d[1] / self.y_scale) + np.square(d[2] / self.z_scale) < 1
        return self._probs_from_mask(mask)

    @classmethod
    def expand_distances(cls):
        return True


class EllipsoidMask(MaskBased):
    """
    A class designed to be passed to the pyNN.DistanceBasedProbabilityConnector to determine the 
    probabilityability of connection within an elliptical region
    """

    def __init__(self, scale, orient_x, orient_y, orient_z, isotropy, probability=None, number=None):
        """
        @param x: scale of the x axis of the ellipsoid
        @param y: scale of the y axis of the ellipsoid   
        @param z: scale of the z axis of the ellipsoid        
        @param number: the mean number of connections to be generated. If None, all cells within the mask will be connected
        """
        super(EllipsoidMask, self).__init__(probability, number)
        self.scale = scale
        self.orient = np.array((orient_x, orient_y, orient_z))
        self.isotropy = isotropy

    def __call__(self, displacement):
        
        working_matrix = axially_symmetric_tensor(self.scale, self.orient, self.isotropy)
        working_matrix_inverse = np.linalg.inv(working_matrix)
        transformed_matrix = np.dot(working_matrix_inverse, displacement)
        distance = np.sqrt(transformed_matrix[0]**2+transformed_matrix[1]**2+transformed_matrix[2]**2)
        mask = distance < 1.0
        return self._probs_from_mask(mask)

    @classmethod
    def expand_distances(cls):
        return True


class RectangleMask(MaskBased):
    """
    A class designed to be passed to the pyNN.DistanceBasedProbabilityConnector to determine the 
    probabilityability of connection within an elliptical region
    """

    def __init__(self, x_scale, y_scale, probability=None, number=None):
        """
        @param x: scale of the x axis side of the rectangle
        @param y: scale of the y axis side of the rectangle 
        @param number: the mean number of connections to be generated. If None, all cells within the mask will be connected
        """
        super(RectangleMask, self).__init__(probability, number)
        self.x_scale = x_scale
        self.y_scale = y_scale

    def __call__(self, d):
        mask = (d[0] < self.x_scale) * (d[1] < self.y_scale)
        return self._probs_from_mask(mask)

    @classmethod
    def expand_distances(cls):
        return True


class BoxMask(MaskBased):
    """
    A class designed to be passed to the pyNN.DistanceBasedProbabilityConnector to determine the 
    probabilityability of connection within an elliptical region
    """

    def __init__(self, x_scale, y_scale, z_scale, probability=None, number=None):
        """
        @param x: scale of the x axis side of the rectangle
        @param y: scale of the y axis side of the rectangle 
        @param number: the mean number of connections to be generated. If None, all cells within the mask will be connected
        """
        super(RectangleMask, self).__init__(probability, number)
        self.x_scale = x_scale
        self.y_scale = y_scale
        self.z_scale = z_scale

    def __call__(self, d):
        mask = (d[0] < self.x_scale) * (d[1] < self.y_scale) * (d[2] < self.z_scale)
        return self._probs_from_mask(mask)

    @classmethod
    def expand_distances(cls):
        return True

if __name__ == '__main__':
    # Put testing code in here
    print "Finished tests"

