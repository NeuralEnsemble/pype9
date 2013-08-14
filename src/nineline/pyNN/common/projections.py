import pyNN.connectors
import nineline.pyNN.connectors
import nineline.forests.point2point
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
        
        SynapseClass = getattr(nineline.pyNN.synapses, 
                               nineml_model.connection_type.definition.component.name)
        synapse = SynapseClass(nineml_model.connection_type.parameters)
        
        projection = cls(nineml_model.source.population, nineml_model.target.population, 
                         connector, synapse_type=synapse, source=nineml_model.source.segment,
                         receptor_type=nineml_model.synaptic_response, label=nineml_model.name)
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

