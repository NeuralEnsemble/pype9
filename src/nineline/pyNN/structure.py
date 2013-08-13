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
from pyNN.random import NumpyRNG, RandomDistribution
from collections import namedtuple

DistributedParam = namedtuple("DistributedParam", "param distr")


class Structure(object):
    
    @classmethod
    def _convert_params(cls, params, rng):
        raise NotImplementedError

class Line(pyNN.space.Line):
    def __init__(self, parameters, rng):
        raise NotImplementedError

class Grid2D(pyNN.space.Grid2D):
    def __init__(self, parameters, rng):
        raise NotImplementedError

class Grid3D(pyNN.space.Grid3D):
    def __init__(self, parameters, rng):
        raise NotImplementedError

class Ring(pyNN.space.Line):
    
    def __init__(self, parameters, rng):
        raise NotImplementedError

class UniformWithinBox(pyNN.space.RandomStructure):
    """
    Overrides pyNN.space.RandomStructure to provide a new 'box' specific constructor to match
    9ml stub
    """
    def __init__(self, x, y, z, x0, y0, z0):
        box = pyNN.space.Cuboid(x, y, z)
        super(UniformWithinBox, self).__init__(box, origin=(x0, y0, z0))


class UniformWithinSphere(pyNN.space.RandomStructure):
    """
    Overrides pyNN.space.RandomStructure to provide a new 'sphere' specific constructor to match
    9ml stub
    """
    def __init__(self, radius, x0, y0, z0):
        sphere = pyNN.space.Sphere(radius)
        super(UniformWithinBox, self).__init__(sphere, origin=(x0, y0, z0))
    

class PerturbedGrid2D(pyNN.space.Grid2D):

    def __init__(self, aspect_ratio=1.0, dx=1.0, dy=1.0, x0=0.0,
                 y0=0.0, z=0.0, fill_order="sequential"):
        pyNN.space.Grid2D.__init__(self, aspect_ratio=aspect_ratio, dx=dx, dy=dy, x0=x0, y0=y0,
                                   z=z, fill_order=fill_order)
        self.distr_params = []

    def apply_distribution(self, dim, distr_type, params, rng=None):
        if not rng:
            rng = NumpyRNG()
        # Convert the dimension from 'x', 'y', 'z' string into index
        try:
            dim = ['x', 'y', 'z'].index(dim) 
        except ValueError:
            if dim not in [0, 1, 2]:
                raise Exception("Dimension needs to be either x-z or 0-2 (found {})".format(dim))
        self.distr_params.append(DistributedParam(dim, 
                                                  RandomDistribution(distr_type, params, rng=rng)))

    def _generate_base_positions(self, n):
        return pyNN.space.Grid2D.generate_positions(self, n)
    
    def generate_positions(self, n):
        positions =  self._generate_base_positions(n)
        for d in self.distr_params:
            positions[d.param,:] += d.distr.next(n, mask_local=False)
        return positions


class PerturbedGrid3D(pyNN.space.Grid3D, PerturbedGrid2D):

    def __init__(self, aspect_ratioXY=1.0, aspect_ratioXZ=1.0, dx=1.0,
                 dy=1.0, dz=1.0, x0=0.0, y0=0.0, z0=0, fill_order="sequential"):
        pyNN.space.Grid3D.__init__(self, aspect_ratioXY=aspect_ratioXY,
                                   aspect_ratioXZ=aspect_ratioXZ, dx=dx, dy=dy, dz=dz, x0=x0, y0=y0,
                                   z0=z0, fill_order=fill_order)
        self.distr_params = []

    def _generate_base_positions(self, n):
        return pyNN.space.Grid3D.generate_positions(self, n)
        
