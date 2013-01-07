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

import numpy
from warnings import warn

class InsufficientTargetsWarning(Warning): pass

#TOD: Should be able to specify axes for each of these geometries to align to

class LinearWithDistance(object):

    def __init__(self, scalar, offset=0.0, min_value=0.0):
        self.scalar = scalar
        self.offset = offset
        self.min_value = min_value

    def get_values(self, d):
        dist = numpy.sqrt(numpy.sum(numpy.square(d), axis=0))
        values = self.offset + self.scalar * dist
        if self.min_value:
            values[values < self.min_value] = self.min_value
        return values

class ExponentialWithDistance(object):

    def __init__(self, scalar, exponent, offset=0.0, min_value=0.0):
        self.scalar = scalar
        self.exponent = exponent
        self.offset = offset
        self.min_value = min_value

    def get_values(self, d):
        dist = numpy.sqrt(numpy.sum(numpy.square(d), axis=0))
        values = self.offset + self.scalar * numpy.exp(self.exponent * dist)
        if self.min_value:
            values[values < self.min_value] = self.min_value
        return values


class LinearWith2DDistance(object):

    def __init__(self, scalar, offset=0.0, min_value=0.0):
        self.scalar = scalar
        self.offset = offset        
        self.min_value = min_value

    def get_values(self, d):
        dist = numpy.sqrt(numpy.sum(numpy.square(d[0:2, :]), axis=0))
        values = self.offset + self.scalar * dist
        if self.min_value:
            values[values < self.min_value] = self.min_value
        return values

class ExponentialWith2DDistance(object):

    def __init__(self, scalar, exponent, offset=0.0, min_value=0.0):
        self.scalar = scalar
        self.exponent = exponent
        self.offset = offset        
        self.min_value = min_value

    def get_values(self, d):
        dist = numpy.sqrt(numpy.sum(numpy.square(d[0:2, :]), axis=0))
        values = self.offset + self.scalar * numpy.exp(self.exponent * dist)
        if self.min_value:
            values[values < self.min_value] = self.min_value
        return values


class MaskBased(object):

    def _probs_from_mask(self, mask, number):
        if not number: # If number is default value of None, all cells within the mask will be connected.
            scale = 1.0
        else:
            num_nz = numpy.count_nonzero(mask)
            if num_nz:
                scale = number / num_nz
            else:
                scale = float('inf')
        # If probability exceeds 1 cap it at 1 as the best that can be done
        if scale > 1.0:
            warn("The number of requested connections ({}) could not be satisfied given size of "
                 "mask ({})".format(int(number), num_nz), InsufficientTargetsWarning)
            scale = 1.0
        probs = numpy.zeros(mask.shape)
        probs[mask] = scale
        return probs

class CircleMask(MaskBased):
    """
    A class designed to be passed to the pyNN.DistanceBasedProbabilityConnector to determine the 
    probability of connection within an elliptical region
    """

    def __init__(self, radius, number=None):
        """
        @param radius: radius of the circle 
        @param number: the mean number of connections to be generated. If None, all cells within the mask will be connected
        """
        self.radius = radius
        self.number = number

    def get_values(self, d):
        mask = numpy.sqrt(numpy.sum(numpy.square(d[0:2, :]), axis=0)) < self.radius
        return self._probs_from_mask(mask, self.number)

class SphereMask(MaskBased):
    """
    A class designed to be passed to the pyNN.DistanceBasedProbabilityConnector to determine the 
    probability of connection within an elliptical region
    """

    def __init__(self, radius, number=None):
        """
        @param radius: radius of the sphere 
        @param number: the mean number of connections to be generated. If None, all cells within the mask will be connected
        """
        self.radius = radius
        self.number = number

    def get_values(self, d):
        mask = numpy.sqrt(numpy.sum(numpy.square(d), axis=0)) < self.radius
        return self._probs_from_mask(mask, self.number)


class EllipseMask(MaskBased):
    """
    A class designed to be passed to the pyNN.DistanceBasedProbabilityConnector to determine the 
    probability of connection within an elliptical region
    """

    def __init__(self, x_scale, y_scale, number=None):
        """
        @param x: scale of the x axis of the ellipse
        @param y: scale of the y axis of the ellipse        
        @param number: the mean number of connections to be generated. If None, all cells within the mask will be connected
        """
        self.x_scale = x_scale
        self.y_scale = y_scale
        self.number = number

    def get_values(self, d):
        mask = numpy.square(d[0] / self.x_scale) + numpy.square(d[1] / self.y_scale) < 1
        return self._probs_from_mask(mask, self.number)


class EllipsoidMask(MaskBased):
    """
    A class designed to be passed to the pyNN.DistanceBasedProbabilityConnector to determine the 
    probability of connection within an elliptical region
    """

    def __init__(self, x_scale, y_scale, z_scale, number=None):
        """
        @param x: scale of the x axis of the ellipsoid
        @param y: scale of the y axis of the ellipsoid   
        @param z: scale of the z axis of the ellipsoid        
        @param number: the mean number of connections to be generated. If None, all cells within the mask will be connected
        """
        self.x_scale = x_scale
        self.y_scale = y_scale
        self.z_scale = z_scale
        self.number = number

    def get_values(self, d):
        mask = numpy.square(d[0] / self.x_scale) + numpy.square(d[1] / self.y_scale) + numpy.square(d[2] / self.z_scale) < 1
        return self._probs_from_mask(mask, self.number)
