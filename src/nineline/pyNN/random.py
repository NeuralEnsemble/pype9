from abc import ABCMeta
import quantities
import nineml.user_layer
import pyNN.random

class RandomDistribution(pyNN.random.RandomDistribution):

    __metaclass__ = ABCMeta

    @classmethod
    def _convert_params(cls, nineml_params):
        """
        Converts parameters from lib9ml objects into values with 'quantities' units and or 
        random distributions
        """
        assert isinstance(nineml_params, nineml.user_layer.ParameterSet)
        converted_params = {}
        units = None
        for name, p in nineml_params.iteritems():
            # Use the quantities package to convert all the values in SI units
            if p.unit == 'dimensionless':
                conv_param = p.value
            else: 
                conv_param = quantities.Quantity(p.value, p.unit).simplified
                if units is None:
                    units = conv_param.units
                elif units != conv_param.units:
                    raise Exception("Dimensions of random distribution parameters do not match "
                                    "({} and {})".format(units, conv_param.units))    
            converted_params[cls.param_translations[name]] = conv_param 
        return converted_params, units

    def __init__(self, nineml_params, rng):
        converted_params, self.units = self._convert_params(nineml_params)
        super(RandomDistribution, self).__init__(self.distr_name, rng=rng,
                                                 parameters=converted_params)
        
    def next(self, n=None, mask_local=None):
        """
        Wraps the PyNN RandomDistribution 'next' method and makes sure the units are attached
        """
        x = super(RandomDistribution, self).next(n=n, mask_local=mask_local)
        if self.units and not isinstance(x, quantities.Quantity):
            x = quantities.Quantity(x, self.units)
        return x
    

class UniformDistribution(RandomDistribution):
    """
    Wraps the pyNN RandomDistribution class and provides a new __init__ method that handles
    the nineml parameter objects
    """
    distr_name = 'uniform'
    
    param_translations = {'low': 'low', 'high': 'high'}

