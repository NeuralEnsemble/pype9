from __future__ import absolute_import
import pyNN.connectors
import nineline.pyNN.connectors
import nineline.morphology.point2point


class ProjectionToCloneNotCreatedYetException(Exception):

    def __init__(self, orig_proj_id=None):
        self.orig_proj_id = orig_proj_id


class Projection(object):

    created_projections = {}

    def __init__(self, source, target, nineml_model, rng=None):
        ConnectorClass = getattr(nineline.pyNN.connectors,
                                 nineml_model.rule.definition.component.name)
        try:
            connector = ConnectorClass(nineml_model.rule.parameters, rng)
        except ProjectionToCloneNotCreatedYetException:
            raise ProjectionToCloneNotCreatedYetException(nineml_model.name)
        SynapseClass = getattr(self._synapses_module,
                               nineml_model.connection_type.definition.\
                                                                component.name)
        synapse = SynapseClass(
            nineml_model.connection_type.parameters, self.get_min_delay(), rng)
        receptor = ('{' + nineml_model.target.segment + '}' +
                    nineml_model.synaptic_response.parameters['responseName'].\
                                                                         value)
        # Sorry if this feels a bit hacky (i.e. relying on the pyNN class being
        # the third class in the MRO), I thought of a few ways to do this but
        # none were completely satisfactory.
        PyNNClass = self.__class__.__mro__[2]
        assert (PyNNClass.__module__.startswith('pyNN') and
                PyNNClass.__module__.endswith('projections'))
        PyNNClass.__init__(self, source, target, connector,
                           synapse_type=synapse,
                           source=nineml_model.source.segment,
                           receptor_type=receptor,
                           label=nineml_model.name)
        # This is used in the clone connectors, there should be a better way
        # than this though I reckon
        self.created_projections[nineml_model.name] = self

    @classmethod
    def _get_target_str(cls, synapse, segment=None):
        if not segment:
            segment = "source_section"
        return segment + "." + synapse

    @classmethod
    def _get_connection_param_expr(cls, label, param, min_value=0.0):
        if isinstance(param, float) or param is None:
            param_expr = param
        elif cls.is_value_str(param):
            param_expr = cls._convert_units(param)
        elif hasattr(param, 'pattern'):
            if param.pattern == "Constant":
                param_expr = cls._convert_units(param.args['value'])
            elif param.pattern == 'DisplacementBased':
                expr_name = param.args.pop('geometry')
                GeometricExpression = getattr(
                    nineline.morphology.point2point, expr_name)
                try:
                    param_expr = pyNN.connectors.\
                                    DisplacementDependentProbabilityConnector.\
                                    DisplacementExpression(
                                       GeometricExpression(
                                         min_value=min_value,
                                         **cls._convert_all_units(param.args)))
                except TypeError as e:
                    raise Exception("Could not initialise distance expression "
                                    "class '{}' from given arguments '{}' for "
                                    "projection '{}'\n('{}')"
                                    .format(expr_name, param.args, label, e))
            else:
                raise Exception("Invalid parameter pattern ('{}') for "
                                "projection '{}'".format(param.pattern, label))
        else:
            raise Exception("Could not parse parameter specification '{}' for "
                            "projection '{}'".format(param, label))
        return param_expr

    @classmethod
    def is_value_str(cls, value_str):
        try:
            cls._convert_units(value_str)
            return True
        except:
            return False

    @classmethod
    def _convert_units(cls, value_str, units=None):
        raise NotImplementedError("_convert_units needs to be implemented by "
                                  "simulator specific Network class")

    @classmethod
    def _convert_all_units(cls, values_dict):
        for key, val in values_dict.items():
            values_dict[key] = cls._convert_units(val)
        return values_dict
