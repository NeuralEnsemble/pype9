from copy import copy
from abc import ABCMeta
import numpy
import quantities as pq
import nineml.user_layer

_numpy_constants_functions = set(['pi', 'exp', 'sin', 'cos', 'log', 'log10', 'pow', 'sinh', 'cosh', 
                                  'tanh', 'sqrt', 'mod', 'sum', 'atan', 'asin', 'acos', 'asinh', 
                                  'acosh', 'atanh', 'atan2'])

def create_anonymous_function(nineml_model):
    assert isinstance(nineml_model, nineml.user_layer.AnonymousFunction)
    # Copy the expression string to allow it to be modified safely (in case it is used again)
    expression_str = copy(nineml_model.inline_function).strip()
    # Replace escape sequences that would otherwise interfere with xml parsing
    expression_str = expression_str.replace('&lt;', '<')
    expression_str = expression_str.replace('&gt;', '>')
    expression_str = expression_str.replace('^', '**')
    # Prepend numpy namespace to math functions
    for sym in _numpy_constants_functions:
        expression_str = expression_str.replace(sym, 'numpy.' + sym)
    # Create arguments list and replace any aliases
    args = []
    for name, alias in nineml_model.arguments.iteritems():
        if alias.strip():
            expression_str = expression_str.replace(name, alias.strip())
            args.append(alias.strip())
        else:
            args.append(name)
    # Instantiate the required constants
    local_vars = { 'numpy':numpy }
    for name, p in nineml_model.constants.iteritems():
        local_vars[name] = pq.Quantity(p.value, p.unit) if p.unit != 'dimensionless' else p.value
        # This is a little hackish, whereby the constants are saved in the lambda function as defaults
        # of optional parameters
        args.append(name+'='+name)
    # Create the lambda function of the expression
    function = eval('lambda {args}: {expr}'.format(args=', '.join(args), expr=expression_str), 
                    globals(), local_vars)
    return function

