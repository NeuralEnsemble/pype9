from copy import copy
from abc import ABCMeta
import numpy
import quantities as pq
import nineml.user_layer


_math_constants = set(['pi'])

_functions = set(['exp', 'sin', 'cos', 'log', 'log10', 'pow',
                'sinh', 'cosh', 'tanh', 'sqrt', 'mod', 'sum',
                'atan', 'asin', 'acos', 'asinh', 'acosh', 'atanh', 'atan2'])


def create_anonymous_function(nineml_params):
    # Copy the expression string to allow it to be modified safely (in case it is used again)
    expression_str = copy(nineml_params.inline_function)
    # Replace escape sequences that would otherwise interfere with xml parsing
    expression_str = expression_str.replace('&lt;', '<')
    expression_str = expression_str.replace('&gt;', '>')
    expression_str = expression_str.replace('^', '**')
    # Append numpy namespace to math functions
    for sym in _math_constants + _functions:
        expression_str = expression_str.replace(sym, 'numpy.' + sym)
    # Create arguments list and replace any aliases
    args = []
    for name, alias in nineml_params.args.iteritems():
        if alias.strip():
            expression_str = expression_str.replace(name, alias.strip())
            args.append(alias.strip())
        else:
            args.append(name)
    # Instantiate the required constants
    consts = {}
    for name, p in nineml_params.consts.iteritems():
        consts[name] = pq.Quantity(p.value, p.unit) if p.unit != 'dimensionless' else p.value
    # Create the lambda function of the expression
    return eval('lambda {args}: {expr}'.format(args=args, expr=expression_str), locals=consts)

