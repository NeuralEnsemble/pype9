from abc import ABCMeta
import quantities
import nineml.user_layer
import pyNN.connectors
import nineline.pyNN.random
import nineline.pyNN.structure.expression
from nineline.pyNN.structure.expression import PositionBasedExpression

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
            converted_params[cls.nineml_translations[name]] = conv_param
        return converted_params
    
    def __init__(self, nineml_params, rng=None):
        # Sorry if this feels a bit hacky (i.e. relying on the pyNN class being the third class in 
        # the MRO), I thought of a few ways to do this but none were completely satisfactory.
        PyNNClass = self.__class__.__mro__[2]
        assert PyNNClass.__module__.startswith('pyNN') and PyNNClass.__module__.startswith('Connector') 
        PyNNClass.__init__(self, **self._convert_params(nineml_params, rng))


class PositionBasedProbabilityConnector(Connector, pyNN.connectors.IndexBasedProbabilityConnector):
    """
    For each pair of pre-post cells, the connection probability depends on an function of the 
    displacement between them.

    Takes any of the standard :class:`Connector` optional arguments and, in
    addition:

        `prob_expression`:
            a function that takes a source position and a target position array and calculates a
            probability matrix from them.
        `source_branch`, `target_branch`:
            the part of the source and target cells to use as the reference points. This allows
            multiple reference points on the cell to be used, eg. soma, dendritic/axonal branch 
            points.  If a cell only has one set of positions then they do not need to be 
            specified (typically a soma)
        `allow_self_connections`:
            if the connector is used to connect a Population to itself, this
            flag determines whether a neuron is allowed to connect to itself,
            or only to other neurons in the Population.
        `rng`:
            an :class:`RNG` instance used to evaluate whether connections exist
    """        
    
    nineml_translations = {'allowSelfConnections':'allow_self_connections', 
                           'probabilityExpression':'prob_expression', 
                           'sourceBranch': 'source_branch', 'targetBranch':'target_branch'}
    
    parameter_names = ('allow_self_connections', 'prob_expression', 'source_branch', 'target_branch')        
            
    def __init__(self, nineml_params, rng):
        conv_params = self._convert_params(nineml_params, rng)
        pyNN.connectors.IndexBasedProbabilityConnector.__init__(self,
                PositionBasedExpression(conv_params['prob_expression'], conv_params['source_branch'],
                                        conv_params['target_branch']), 
                allow_self_connections=conv_params['allow_self_connections'], rng=rng)    
                

class AllToAllConnector(Connector, pyNN.connectors.AllToAllConnector):
    
    nineml_translations = {'allowSelfConnections': 'allow_self_connections'}


class FixedProbabilityConnector(Connector, pyNN.connectors.FixedProbabilityConnector):
    
    nineml_translations = {'allowSelfConnections':'allow_self_connections', 
                           'probability':'p_connect'}

class FixedNumberPostConnector(Connector, pyNN.connectors.FixedNumberPostConnector):
    
    nineml_translations = {'allowSelfConnections':'allow_self_connections', 'number':'n'}


class FixedNumberPreConnector(Connector, pyNN.connectors.FixedNumberPreConnector):
    
    nineml_translations = {'allowSelfConnections':'allow_self_connections', 'number':'n'}


class OneToOneConnector(Connector, pyNN.connectors.OneToOneConnector):
    
    nineml_translations = {}


class SmallWorldConnector(Connector, pyNN.connectors.SmallWorldConnector):
    
    nineml_translations = {'allowSelfConnections':'allow_self_connections', 'degree': 'degree', 
                           'rewiring':'rewiring', 'numberOfConnections':'n_connections'}


class CloneConnector(Connector, pyNN.connectors.CloneConnector):
    
    nineml_translations = {'projection':'reference_projection'}            

        