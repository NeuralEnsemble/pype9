import os
import numpy
import warnings
import pyNN.connectors
import nineline.pyNN.connectors
import nineline.forests.point2point
import nineline.forests.morphology
from nineline.cells import NineCell

class Projection(object):
    
    class ProjectionToCloneNotCreatedYetException(Exception):
        
        def __init__(self, orig_proj_id):
            self.orig_proj_id = orig_proj_id
            
    created_projections = []
    
    @classmethod
    def factory(cls, nineml_model, proj_dir, rng=None, verbose=False):
        ConnectorClass = getattr(nineline.pyNN.connectors, 
                                 nineml_model.rule.definition.component.name)
        connector = ConnectorClass(nineml_model.rule.parameters, rng)
        
        SynapseClass = getattr(nineline.pyNN.synapses, nineml_model.connection_type.component.name)
        
        # Set expressions for connection weights and delays
        weight_expr = cls._get_connection_param_expr(label, weight)
        if synapse_family == 'Electrical':
            allow_self_connections='NoMutual'
        else:
            delay_expr = cls._get_connection_param_expr(label, delay,
                                                         min_value=cls.get_min_delay())
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
                GeometricExpression = getattr(nineline.forests.point2point, expr_name)
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

