from __future__ import absolute_import
from abc import ABCMeta
import quantities
import nineml.user_layer
import pyNN.connectors
from . import create_anonymous_function


class StructureExpression(object):

    __metaclass__ = ABCMeta

    @classmethod
    def _convert_params(cls, nineml_params):
        """
        Converts parameters from lib9ml objects into values with 'quantities'
        units and or random distributions
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
        # Sorry if this feels a bit hacky (i.e. relying on the pyNN class being
        # the third class in the MRO), I thought of a few ways to do this but
        # none were completely satisfactory.
        PyNNClass = self.__class__.__mro__[2]
#         assert (PyNNClass.__module__.startswith('pyNN') and
#                 PyNNClass.__module__.endswith('connectors'))
        params = self._convert_params(nineml_params)
        PyNNClass.__init__(self, **params)


class _PositionBasedExpression(pyNN.connectors.IndexBasedExpression):

    """
    This provides the guts of the PositionBasedExpression class and will
    hopefully be included in PyNN in the future, but for now it needs to be
    separated from the 9ML wrapper so that it can also be used in the
    PositionBasedProbabiliityConnector
    """

    def __init__(self, expression, source_structure, target_structure):
        """
        `function`: a function that takes a 3xN numpy position matrix and maps
                    each row (displacement) to a probability between 0 and 1
        """
        self.expression = expression
        self.source_structure = source_structure
        self.target_structure = target_structure
        pyNN.connectors.IndexBasedExpression.__init__(self)

    def __call__(self, i, j):
        source_positions = self.projection.pre.structures[
            self.source_structure].positions[:, i]
        target_positions = self.projection.post.structures[
            self.target_structure].positions[:, j]
        values = self.expression(sourceX=source_positions[0],
                                 sourceY=source_positions[1],
                                 sourceZ=source_positions[2],
                                 targetX=target_positions[0],
                                 targetY=target_positions[1],
                                 targetZ=target_positions[2])
        self.validate_values(values)
        return values

    def __str__(self):
        return str(self.expression.str)


class PositionBasedExpression(StructureExpression, _PositionBasedExpression):

    """
    A displacement based prob_expression function used to determine the
    connection probability and the value of variable connection parameters of a
    projection
    """

    nineml_translations = {'expression': 'expression',
                           'sourceStructure': 'source_structure',
                           'targetStructure': 'target_structure'}
