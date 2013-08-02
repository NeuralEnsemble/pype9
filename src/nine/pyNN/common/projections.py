import os
import numpy
import warnings
import pyNN.connectors
import nine.trees.point2point
import nine.trees.morphology
from nine.cells import NineCell

class Projection(object):
    
    class ProjectionToCloneNotCreatedYetException(Exception):
        
        def __init__(self, orig_proj_id):
            self.orig_proj_id = orig_proj_id
    
    @classmethod
    def factory(cls, label, pre, dest, connection, source, target, weight, delay, synapse_family, 
                proj_dir, rng, already_created_projections=[], verbose=False, 
                allow_self_connections=False):
        # Set expressions for connection weights and delays
        weight_expr = cls._get_connection_param_expr(label, weight)
        if synapse_family == 'Electrical':
            allow_self_connections='NoMutual'
        else:
            delay_expr = cls._get_connection_param_expr(label, delay,
                                                         min_value=cls.get_min_delay())
        # Set up other required connector args
        other_connector_args = {}
        if connection.pattern != "OneToOne":
            other_connector_args['allow_self_connections'] = allow_self_connections
        # Create the "Connector" class to connect up the projection
        if connection.pattern == 'DisplacementBased':
            expression = connection.args.pop('geometry')
            if not hasattr(nine.trees.point2point, expression):
                raise Exception("Unrecognised distance expression '{}'".format(expression))
            try:
                GeometricExpression = getattr(nine.trees.point2point, expression)
                connect_expr = GeometricExpression(**cls._convert_all_units(connection.args))
            except TypeError as e:
                raise Exception("Could not initialise distance expression class '{}' from given " 
                                "arguments '{}' for projection '{}'\n('{}')"
                                .format(expression, connection.args, label, e))
            connector = cls._pyNN_module.connectors.DisplacementDependentProbabilityConnector(
                                    connect_expr, **other_connector_args)
        elif connection.pattern == 'MorphologyBased':
            kernel_name = connection.args.pop('kernel')
            if not hasattr(nine.trees.morphology, kernel_name + 'Kernel'):
                raise Exception("Unrecognised distance expression '{}'".format(kernel_name))
            try:
                Kernel = getattr(nine.trees.morphology, kernel_name + 'Kernel')
                kernel = Kernel(**cls._convert_all_units(connection.args))
            except TypeError as e:
                raise Exception("Could not initialise distance expression class '{}' from given " 
                                "arguments '{}' for projection '{}'\n('{}')"
                                .format(kernel_name, connection.args, label, e))
            connector = nine.trees.morphology.MorphologyBasedProbabilityConnector(
                                                                    kernel, **other_connector_args)
        # If connection pattern is external, load the weights and delays from a file in PyNN
        # FromFileConnector format and then create a FromListConnector connector. Some additional
        # preprocessing is performed here, which is why the FromFileConnector isn't used directly.
        elif connection.pattern == "Extension":
            proj_id = connection.args['id']
            if proj_id not in os.listdir(proj_dir):
                raise Exception("Connection id '{}' was not found in search path ({}).".
                                format(proj_id, proj_dir))
            connection_matrix = numpy.loadtxt(os.path.join(proj_dir, connection.args['id']))
            connection_matrix = numpy.ones((1, 4))
            if isinstance(weight_expr, float):
                connection_matrix[:, 2] = weight_expr
            if isinstance(delay_expr, float):
                connection_matrix[:, 3] = delay_expr
            # Get view onto delays in connection matrix for readability                    
            delays = connection_matrix[:, 3]
            below_min_indices = numpy.where(delays < cls.get_min_delay())
            if len(below_min_indices):
                if verbose:
                    warnings.warn("{} out of {} connections are below the minimum delay in "
                                  "projection '{}'. They will be bounded to the minimum delay "
                                  "({})".format(len(below_min_indices), len(delays), label,
                                                cls.get_min_delay()))
                # Bound loaded delays by specified minimum delay                        
                delays[below_min_indices] = cls.get_min_delay()
            connector = cls._pyNN_module.connectors.FromListConnector(connection_matrix,
                                                                       **other_connector_args)
        # Use in-built pyNN connectors for simple patterns such as AllToAll and OneToOne
        # NB: At this stage the pattern name is tied to the connector name in pyNN but could be
        # decoupled from this at some point (but I am not sure you would want to)
        elif connection.pattern == 'Clone':
            orig_proj_id = connection.args['projection']
            try:
                orig_proj = already_created_projections[orig_proj_id]
            except KeyError:
                raise cls.ProjectionToCloneNotCreatedYetException(orig_proj_id)
            connector = cls._pyNN_module.connectors.CloneConnector(orig_proj, **other_connector_args)
        elif connection.pattern + 'Connector' in dir(pyNN.connectors):
            ConnectorClass = getattr(cls._pyNN_module.connectors,
                                     '{}Connector'.format(connection.pattern))
            connection.args.update(other_connector_args)
            connector = ConnectorClass(**connection.args)
        else:
            raise Exception("Unrecognised pattern type '{}'".format(connection.pattern))
        # Initialise the rest of the projection object and return
        if synapse_family == 'Chemical':
            synapse = cls._pyNN_module.StaticSynapse(weight=weight_expr, delay=delay_expr)
            source_terminal = source.terminal
            if target.synapse is None:
                receptor_type = 'excitatory'
            else:
                receptor_type = cls._get_target_str(target.synapse, target.segment)
        elif synapse_family == 'Electrical':    
            synapse = cls._pyNN_module.ElectricalSynapse(weight=weight_expr)
            source_terminal = source.segment + '_seg'
            receptor_type = target.segment + '_seg.gap'
        else:
            raise Exception("Unrecognised synapse family type '{}'".format(synapse_family))
        projection = cls(pre, dest, connector, synapse_type=synapse, source=source_terminal,
                         receptor_type=receptor_type, label=label)
        return projection   
    
    @classmethod
    def _get_target_str(cls, synapse, segment=None):
        if not segment:
            segment = "source_section"
        return NineCell.seg_varname(segment) + "." + synapse
    
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
                GeometricExpression = getattr(nine.trees.point2point, expr_name)
                try:
                    param_expr = pyNN.connectors.DisplacementDependentProbabilityConnector.\
                                     DisplacementExpression(GeometricExpression(min_value=min_value,
                                     **cls._convert_all_units(param.args)))
                except TypeError as e:
                    raise Exception("Could not initialise distance expression class '{}' from "
                                    "given arguments '{}' for projection '{}'\n('{}')"
                                    .format(expr_name, param.args, label, e))
            else:
                raise Exception("Invalid parameter pattern ('{}') for projection '{}'".
                                format(param.pattern, label))
        else:
            raise Exception("Could not parse parameter specification '{}' for projection '{}'"
                            .format(param, label))
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
        raise NotImplementedError("_convert_units needs to be implemented by simulator specific " 
                                  "Network class")

    @classmethod
    def _convert_all_units(cls, values_dict):
        for key, val in values_dict.items():
            values_dict[key] = cls._convert_units(val)
        return values_dict    

