"""

  This module contains extensions to the pyNN.space module
  
  @author Tom Close

"""

#######################################################################################
#
#    Copyright 2012 Okinawa Institute of Science and Technology (OIST), Okinawa, Japan
#
#######################################################################################
from abc import ABCMeta
import numpy
import quantities
import nineml.user_layer
import pyNN.space
import nineline.pyNN.random

class Layout(object):
    
    __metaclass__ = ABCMeta
    
    @classmethod
    def _convert_params(cls, nineml_params, rng):
        """
        Converts parameters from lib9ml objects into values with 'quantities' units and or 
        random distributions
        """
        converted_params = {}
        for name, p in nineml_params.iteritems():
            if p.unit == 'dimensionless':
                conv_param = p.value
            elif p.unit:
                conv_param = quantities.Quantity(p.value, p.unit)
                # Convert to SI units and drop the quantity as it may interfere with the layout
                # function (it will be added in again after the positions are generated, with the
                # assumption that all dimensions are length)
                conv_param = float(conv_param.simplified)
            elif isinstance(p.value, str):
                conv_param = p.value
            elif isinstance(p.value, nineml.user_layer.RandomDistribution):
                RandomDistributionClass = getattr(nineline.pyNN.random, 
                                                  p.value.definition.component.name)
                conv_param = RandomDistributionClass(p.value.parameters, rng)
            converted_params[cls.nineml_translations[name]] = conv_param 
        return converted_params
    
    def __init__(self, n, nineml_params, rng=None):
        self.size = n
        self._positions = None
        # Sorry if this feels a bit hacky (i.e. relying on the pyNN class being the third class in 
        # the MRO), I thought of a few ways to do this but none were completely satisfactory.
        PyNNClass = self.__class__.__mro__[2]
        assert PyNNClass.__module__.startswith('pyNN')
        PyNNClass.__init__(self, **self._convert_params(nineml_params, rng))
        

class Line(Layout, pyNN.space.Line):
    
    nineml_translations = {'dx': 'dx', 'x0': 'x0', 'y': 'y', 'z': 'z' }


class Grid2D(Layout, pyNN.space.Grid2D):
    
    nineml_translations = {'aspectRatioXY': 'aspect_ratio', 'dx': 'dx', 'dy': 'dy', 'x0': 'x0', 
                           'y0': 'y0', 'z0': 'z0', 'fillOrder': 'fill_order'}
    

class Grid3D(Layout, pyNN.space.Grid3D):
    
    nineml_translations = {'aspectRatioXY': 'aspect_ratioXY', 'aspectRatioXZ': 'aspect_ratioXZ', 
                           'dx': 'dx', 'dy': 'dy', 'dz': 'dz', 'x0': 'x0', 'y0': 'y0', 'z0': 'z0', 
                           'fillOrder': 'fill_order'}
   

class PerturbedGrid2D(Layout, pyNN.space.PerturbedGrid2D):

    nineml_translations = {'aspectRatioXY': 'aspect_ratio', 'dx': 'dx', 'dy': 'dy', 'x0': 'x0', 
                           'y0': 'y0', 'z0': 'z0', 'xPerturbation':'perturb_x', 
                           'yPerturbation':'perturb_y', 'zPerturbation':'perturb_z', 
                           'fillOrder': 'fill_order'}


class PerturbedGrid3D(Layout, pyNN.space.PerturbedGrid3D):

    nineml_translations = {'aspectRatioXY': 'aspect_ratioXY', 'aspectRatioXZ': 'aspect_ratioXZ', 
                           'dx': 'dx', 'dy': 'dy', 'dz': 'dz', 'x0': 'x0', 'y0': 'y0', 'z0': 'z0',
                           'xPerturbation':'perturb_x', 'yPerturbation':'perturb_y', 
                           'zPerturbation':'perturb_z', 'fillOrder': 'fill_order'}        


class UniformWithinBox(Layout, pyNN.space.RandomStructure):
    """
    Overrides pyNN.space.RandomStructure to provide a new 'box' specific constructor to match
    9ml stub
    """
    nineml_translations = {'x': 'x', 'y': 'y', 'z': 'z', 'x0': 'x0', 'y0': 'y0', 'z0': 'z0'}
    
    def __init__(self, nineml_params, rng=None):
        params = self._convert_params(nineml_params, rng)
        box = pyNN.space.Cuboid(params['x'], params['y'], params['z'])
        super(UniformWithinBox, self).__init__(box, origin=(params['x0'], params['y0'], 
                                                            params['z0']), rng=rng)


class UniformWithinSphere(Layout, pyNN.space.RandomStructure):
    """
    Overrides pyNN.space.RandomStructure to provide a new 'sphere' specific constructor to match
    9ml stub
    """
    
    nineml_translations = {'radius': 'radius', 'x0': 'x0', 'y0': 'y0', 'z0': 'z0'}
    
    def __init__(self, nineml_params, rng=None):
        params = self._convert_params(nineml_params, rng)
        sphere = pyNN.space.Sphere(params['radius'])
        super(UniformWithinSphere, self).__init__(sphere, origin=(params['x0'], params['y0'], 
                                                            params['z0']), rng=rng)
