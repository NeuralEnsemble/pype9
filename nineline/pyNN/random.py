from __future__ import absolute_import
from abc import ABCMeta
import nineml.user_layer
import pyNN.random
from nineline.pyNN import convert_to_pyNN_units

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
                conv_param, param_units = convert_to_pyNN_units(p.value, p.unit)
                if units is None:
                    units = param_units
                elif units != param_units:
                    raise Exception("Dimensions of random distribution parameters do not match "
                                    "({} and {})".format(units, param_units))
            converted_params[cls.nineml_translations[name]] = conv_param 
        return converted_params, units

    def __init__(self, nineml_params, rng, use_units=True):
        converted_params, units = self._convert_params(nineml_params)
        self.units = units if use_units else None
        ordered_params = []
        for name in self.parameter_order:
            ordered_params.append(converted_params[name])
        super(RandomDistribution, self).__init__(self.distr_name, rng=rng,
                                                 parameters=ordered_params)
        
    def next(self, n=None, mask_local=None):
        """
        Wraps the PyNN RandomDistribution 'next' method and makes sure the units are attached
        """
        x = super(RandomDistribution, self).next(n=n, mask_local=mask_local)
        if self.units:
            x = x * self.units
        return x
    

class UniformDistribution(RandomDistribution):
    """
    Wraps the pyNN RandomDistribution class and provides a new __init__ method that handles
    the nineml parameter objects
    """
    distr_name = 'uniform'
    
    nineml_translations = {'low': 'low', 'high': 'high'}
    #needed because PyNN doesn't support kwargs for RandomDistribution objects yet
    parameter_order = ('low', 'high')

