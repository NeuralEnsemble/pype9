"""

  This module contains extensions to the pyNN.space module
  
  @author Tom Close

"""

#######################################################################################
#
#    Copyright 2012 Okinawa Institute of Science and Technology (OIST), Okinawa, Japan
#
#######################################################################################

import pyNN.space
from pyNN.random import NumpyRNG

class Grid2D(pyNN.space.Grid2D):

    def __init__(self, aspect_ratio=1.0, dx=1.0, dy=1.0, x0=0.0,
                 y0=0.0, z=0.0, fill_order="sequential"):
        pyNN.space.Grid2D.__init__(self, aspect_ratio=aspect_ratio, dx=dx, dy=dy, x0=x0, y0=y0,
                                   z=z, fill_order=fill_order)
        self.distributions = []

    def apply_distribution(self, dim, type, params, rng=None):
        if not rng:
            rng = NumpyRNG()
        if dim == 'x': dim = 0
        elif dim == 'y': dim = 1
        elif dim == 'z': dim = 2
        elif dim not in [0, 1, 2]:
            raise Exception("Dimension needs to be either x-z or 0-2 (found {})".format(dim))
        try:
            self.distributions.append((dim, getattr(rng, type), (params)))
        except AttributeError:
            raise Exception("Provided random number generator does not have distribution '{}"
                            .format(type))

    def generate_positions(self, n):
        positions = pyNN.space.Grid2D.generate_positions(self, n)
        for distr in self.distributions:
            positions[distr[0],:] += distr[1](*distr[2])
        return positions

class Grid3D(pyNN.space.Grid3D, Grid2D):

    def __init__(self, aspect_ratioXY=1.0, aspect_ratioXZ=1.0, dx=1.0,
                 dy=1.0, dz=1.0, x0=0.0, y0=0.0, z0=0, fill_order="sequential"):
        pyNN.space.Grid3D.__init__(self, aspect_ratioXY=aspect_ratioXY,
                                   aspect_ratioXZ=aspect_ratioXZ, dx=dx, dy=dy, dz=dz, x0=x0, y0=y0,
                                   z0=z0, fill_order=fill_order)
        self.distributions = []

    def generate_positions(self, n):
        positions = pyNN.space.Grid3D.generate_positions(self, n)
        for distr in self.distributions:
            positions[distr[0],:] += distr[1](**distr[2])
        return positions

