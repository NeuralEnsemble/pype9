import quantities
import nineml.user_layer
import pyNN.random

class RandomDistribution(pyNN.random.RandomDistribution):

    @classmethod
    def convert_params(cls, nineml_params):
        """
        Converts parameters from lib9ml objects into values with 'quantities' units and or 
        random distributions
        """
        assert isinstance(nineml_params, nineml.user_layer.ParameterSet)
        converted_params = {}
        for name, p in nineml_params.iteritems():
            converted_params[cls.param_translations[name]] = quantities.Quantity(p.value, p.unit)
        return converted_params

    def __init__(self, nineml_params, rng):
        super(RandomDistribution, self).__init__(self.distr_name, rng=rng,
                                                 parameters=self.convert_params(nineml_params))
    

class UniformDistribution(RandomDistribution):
    """
    Wraps the pyNN RandomDistribution class and provides a new __init__ method that handles
    the nineml parameter objects
    """
    distr_name = 'uniform'
    
    param_translations = {'low': 'low', 'high': 'high'}

