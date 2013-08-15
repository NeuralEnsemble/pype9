from abc import ABCMeta
import quantities
import nineml.user_layer
import pyNN.connectors
import nineline.pyNN.random
import nineline.pyNN.structure.expression

class Connector(object):
    
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
            elif isinstance(p.value, str):
                conv_param = p.value
            elif isinstance(p.value, nineml.user_layer.RandomDistribution):
                RandomDistributionClass = getattr(nineline.pyNN.random, 
                                                  p.value.definition.component.name)
                conv_param = RandomDistributionClass(p.value.parameters, rng)
            elif isinstance(p.value, nineml.user_layer.StructureExpression):
                StructureExpressionClass = getattr(nineline.pyNN.structure.expression, 
                                                  p.value.definition.component.name)
                conv_param = StructureExpressionClass(p.value.parameters, rng)
            converted_params[cls.translations[name]] = conv_param
        return converted_params
    
    def __init__(self, nineml_params, rng=None):
        # Sorry if this feels a bit hacky (i.e. relying on the pyNN class being the third class in 
        # the MRO), I thought of a few ways to do this but none were completely satisfactory.
        PyNNClass = self.__class__.__mro__[2]
        assert PyNNClass.__module__.startswith('pyNN')
        PyNNClass.__init__(self, **self._convert_params(nineml_params, rng))
        

class AllToAllConnector(Connector, pyNN.connectors.AllToAllConnector):
    
    translations = {'allowSelfConnections': 'allow_self_connections'}


class FixedProbabilityConnector(Connector, pyNN.connectors.FixedProbabilityConnector):
    
    translations = {'allowSelfConnections':'allow_self_connections', 'probability':'p_connect'}


class PositionBasedProbabilityConnector(Connector, pyNN.connectors.PositionBasedProbabilityConnector):
    
    translations = {'allowSelfConnections':'allow_self_connections', 
                    'probabilityExpression':'prob_expression', 'sourceBranch': 'source_branch',
                    'targetBranch':'target_branch'}


class FixedNumberPostConnector(Connector, pyNN.connectors.FixedNumberPostConnector):
    
    translations = {'allowSelfConnections':'allow_self_connections', 'number':'n'}


class FixedNumberPreConnector(Connector, pyNN.connectors.FixedNumberPreConnector):
    
    translations = {'allowSelfConnections':'allow_self_connections', 'number':'n'}


class OneToOneConnector(Connector, pyNN.connectors.OneToOneConnector):
    
    translations = {}


class SmallWorldConnector(Connector, pyNN.connectors.SmallWorldConnector):
    
    translations = {'allowSelfConnections':'allow_self_connections', 'degree': 'degree', 
                    'rewiring':'rewiring', 'numberOfConnections':'n_connections'}


class CloneConnector(Connector, pyNN.connectors.CloneConnector):
    
    translations = {'projection':'reference_projection'}            

        