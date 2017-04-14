import os.path
import operator
import sys
import logging
import sympy
import nineml.units
import ninemlcatalog
from argparse import ArgumentTypeError
from pype9.exceptions import Pype9UsageError, Pype9UnitStrError


def existing_file(fname):
    if not os.path.isfile(fname):
        raise ArgumentTypeError(
            "'{}' does not refer to an existing file".format(fname))
    return fname


def nineml_document(doc_path):
    if doc_path.startswith('//'):
        model = ninemlcatalog.load(doc_path[2:])
    else:
        if not doc_path.startswith('/') and not doc_path.startswith('.'):
            doc_path = './' + doc_path
        model = nineml.read(doc_path, relative_to=os.getcwd())
    return model


def nineml_model(model_path):
    model = nineml_document(model_path)
    if isinstance(model, nineml.Document):
        model = model.as_network(
            os.path.splitext(os.path.basename(model_path))[0])
    return model


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


logger = logging.getLogger('PyPe9')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
