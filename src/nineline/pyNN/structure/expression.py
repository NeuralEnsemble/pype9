from abc import ABCMeta
import quantities
import nineml.user_layer
import pyNN.connectors
from .. import create_anonymous_function

class StructureExpression(object):

    __metaclass__ = ABCMeta

    @classmethod
    def _convert_params(cls, nineml_params):
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
            elif isinstance(p.value, str):
                conv_param = p.value
            elif isinstance(p.value, nineml.user_layer.AnonymousFunction):
                conv_param = create_anonymous_function(p.value)
            else:
                conv_param = quantities.Quantity(p.value, p.unit)
            converted_params[cls.nineml_translations[name]] = conv_param 
        return converted_params

    def __init__(self, nineml_params):
        # Sorry if this feels a bit hacky (i.e. relying on the pyNN class being the third class in 
        # the MRO), I thought of a few ways to do this but none were completely satisfactory.
        PyNNClass = self.__class__.__mro__[2]
        assert PyNNClass.__module__.startswith('pyNN') and PyNNClass.__module__.startswith('Expression') 
        params = self._convert_params(nineml_params)
        PyNNClass.__init__(self, **params)
    

class PositionBasedExpression(StructureExpression, pyNN.connectors.PositionBasedExpression):
    """
    Wraps the pyNN RandomDistribution class and provides a new __init__ method that handles
    the nineml parameter objects
    """
    
    nineml_translations = {'expression': 'expression', 'sourceBranch':'source_branch',
                          'targetBranch':'target_branch'}