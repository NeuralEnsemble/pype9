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

class Perturbed2DGrid(pyNN.space.Grid2D):

    def __init__(self, distr_type, distr_params, self, aspect_ratio=1.0, dx=1.0, dy=1.0, x0=0.0, 
                                                  y0=0.0, fill_order="sequential", rng=None):
        pyNN.space.Grid2D.__init__(self, aspect_ratio=aspect_ratio, dx=dx, dy=dy, x0=x0, y0=y0,
                                   fill_order=fill_order)
        self.distr_type = distr_type
        self.distr_params = distr_params
        self.rng = rng or NumpyRNG()

    def generate_positions(self, n):
        positions = super(Perturbed2DGrid, self).generate_positions(n)
        positions += getattr(self.rng, self.distr_type)(**self.distr_params)
        return positions

class Perturbed3DGrid(pyNN.space.Grid3D):

    def __init__(self, distr_type, distr_params, aspect_ratioXY=1.0, aspect_ratioXZ=1.0, dx=1.0, 
                 dy=1.0, dz=1.0, x0=0.0, y0=0.0, z0=0, fill_order="sequential", rng=None):
        pyNN.space.Grid3D.__init__(self, aspect_ratioXY=aspect_ratioXY,
                                   aspect_ratioXZ=aspect_ratioXZ, dx=dx, dy=dy, dz=dz, x0=x0, y0=y0,
                                   z0=z0, fill_order=fill_order)
        self.distr_type = distr_type
        self.distr_params = distr_params
        self.rng = rng or NumpyRNG()

    def generate_positions(self, n):
        positions = super(Perturbed3DGrid, self).generate_positions(n)
        positions += getattr(self.rng, self.distr_type)(**self.distr_params)
        return positions

