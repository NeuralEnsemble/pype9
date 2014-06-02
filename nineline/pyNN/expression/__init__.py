"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the GPL v2, see LICENSE for details.
"""
from __future__ import absolute_import
from abc import ABCMeta
import numpy
import nineml.user_layer
from nineline.pyNN import convert_to_pyNN_units

_numpy_constants_functions = set(['pi', 'exp', 'sin', 'cos', 'log', 'log10',
                                  'pow', 'sinh', 'cosh', 'tanh', 'sqrt',
                                  'mod', 'sum', 'atan', 'asin', 'acos',
                                  'asinh', 'acosh', 'atanh', 'atan2'])


def create_anonymous_function(nineml_model):
    assert isinstance(nineml_model, nineml.user_layer.AnonymousFunction)
    # Replace multiple whitespaces by single space
    expression_str = ' '.join((nineml_model.inline_function).split())
    # Create arguments list and replace any aliases
    args = []
    for name, alias in nineml_model.arguments.iteritems():
        if alias.strip():
            expression_str = expression_str.replace(name, alias.strip())
            args.append(alias.strip())
        else:
            args.append(name)
    args.sort()
    # Instantiate the required constants
    for name, p in nineml_model.constants.iteritems():
        if p.unit == 'dimensionless':
            value = p.value
        else:
            value, units = convert_to_pyNN_units(
                p.value, p.unit)  # @UnusedVariable
        expression_str = expression_str.replace(name, str(value))
    # Replace escape sequences that would otherwise interfere with xml parsing
    expression_str = expression_str.replace('&lt;', '<')
    expression_str = expression_str.replace('&gt;', '>')
    expression_str = expression_str.replace('^', '**')
    # Prepend numpy namespace to math functions
    for sym in _numpy_constants_functions:
        expression_str = expression_str.replace(sym, 'numpy.' + sym)
    # Create the lambda function of the expression
    func = eval('lambda {args}: {expr}'.format(
        args=', '.join(args), expr=expression_str))
    # Save the expression in the lambda function for pretty display
    func.str = 'f({args}) -> {expr}'.format(args=', '.join(args),
                                            expr=expression_str)
    return func
