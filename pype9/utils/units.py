from builtins import str
import operator
import sympy
import nineml.units
from pype9.exceptions import Pype9UsageError, Pype9UnitStrError
from functools import reduce
import pype9.utils.logging.handlers.sysout  # @UnusedImport


# Get all standard units defined in nineml.units
standard_units = {}
for obj_name in dir(nineml.units):
    obj = getattr(nineml.units, obj_name)
    if isinstance(obj, nineml.units.Unit):
        standard_units[obj.name] = obj


def parse_units(unit_str):
    # TODO: Should donate this function to the nineml.units module
    try:
        unit_expr = sympy.sympify(unit_str)
    except:
        raise Pype9UsageError(
            "Unit expression '{}' is not a valid expression".format(unit_str))
    try:
        return _parse_subexpr(unit_expr)
    except Pype9UnitStrError:
        raise Pype9UsageError(
            "Unit expression '{}' contains operators other than "
            "multiplication and division".format(unit_str))


def _parse_subexpr(expr):
    """parse_units helper function"""
    try:
        return standard_units[str(expr)]
    except KeyError:
        if isinstance(expr, sympy.Symbol):
            raise Pype9UsageError(
                "Unrecognised unit '{}'".format(expr))
        elif isinstance(expr, (sympy.Mul, sympy.Pow)):
            op = operator.mul if isinstance(expr, sympy.Mul) else operator.pow
            return reduce(op, (_parse_subexpr(a) for a in expr.args))
        elif isinstance(expr, sympy.Integer):
            return int(expr)
        else:
            raise Pype9UnitStrError
