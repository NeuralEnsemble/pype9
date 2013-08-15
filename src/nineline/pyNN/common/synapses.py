from __future__ import absolute_import
from abc import ABCMeta
import quantities
import nineml.user_layer
import nineline.pyNN.random
import nineline.pyNN.structure.expression

class Synapse(object):

    __metaclass__ = ABCMeta

    @classmethod
    def _convert_params(cls, nineml_params, rng):
        """
        Converts parameters from lib9ml objects into values with 'quantities' units and or 
        random distributions
        """
        assert isinstance(nineml_params, nineml.user_layer.ParameterSet)
        converted_params = {}
        for name, p in nineml_params.iteritems():
            # Use the quantities package to convert all the values in SI units
            if p.unit == 'dimensionless':
                conv_param = p.value
            elif p.unit:
                conv_param = quantities.Quantity(p.value, p.unit)
            elif isinstance(p.value, str):
                conv_param = p.value
            elif isinstance(p.value, nineml.user_layer.RandomDistribution):
                RandomDistributionClass = getattr(nineline.pyNN.random, 
                                                  p.value.definition.component.name)
                conv_param = RandomDistributionClass(p.value.parameters, rng)                
            elif isinstance(p.value, nineml.user_layer.StructureExpression):
                StructureExpressionClass = getattr(nineline.pyNN.structure.expression,
                                                   p.value.definition.component.name)
                conv_param = StructureExpressionClass(p.value.parameters)
            else: 
                raise Exception("Parameter '{}' is of unrecognised type '{}'"
                                .format(p.value, type(p.value)))
            converted_params[cls.nineml_translations[name]] = conv_param 
        return converted_params

    def __init__(self, nineml_params, rng):
        # Sorry if this feels a bit hacky (i.e. relying on the pyNN class being the third class in 
        # the MRO), I thought of a few ways to do this but none were completely satisfactory.
        PyNNClass = self.__class__.__mro__[3]
        assert PyNNClass.__module__.startswith('pyNN') and PyNNClass.__module__.startswith('Synapse') 
        super(PyNNClass, self).__init__(**self._convert_params(nineml_params, rng))
    

class StaticSynapse(Synapse):
    """
    Wraps the pyNN RandomDistribution class and provides a new __init__ method that handles
    the nineml parameter objects
    """
    
    nineml_translations = {'weight':'weight', 'delay':'delay'}
    
    
class ElectricalSynapse(Synapse):
    """
    Wraps the pyNN RandomDistribution class and provides a new __init__ method that handles
    the nineml parameter objects
    """
    
    nineml_translations = {'weight':'weight'}    