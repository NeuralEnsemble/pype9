import os
import sys
import logging
import operator
import cPickle as pkl
import sympy
from sympy import sympify
from numpy import array, sum, abs, argmin
import quantities as pq
import diophantine
from nineml import units as un
from nineml.abstraction.ports import SendPortBase
from nineml.abstraction.dynamics.visitors import DynamicsDimensionResolver
import atexit


logger = logging.getLogger('PyPe9')

_CACHE_FILENAME = '.unit_mapping_cache.pkl'


def load_basis_matrices_and_cache(basis, directory):
    assert all(u.offset == 0 for u in basis), (
        "Non-zero offsets found in basis units")
    # Get matrix of basis unit dimensions
    A = array([list(b.dimension) for b in basis]).T
    # Get cache path from file path of subclass
    cache_path = os.path.join(directory, _CACHE_FILENAME)
    try:
        with open(cache_path) as f:
            cache, loaded_A = pkl.load(f)
            # If the dimension matrix has been changed since the cache was
            # generated, reset the cache
            if (loaded_A != A).all():
                cache = {}
    except (IOError, EOFError):
        logger.warning("Could not load unit conversion cache from file "
                       "'{}'".format(cache_path))
        cache = {}
    def save_cache():  # @IgnorePep8
        try:
            with open(cache_path, 'w') as f:
                pkl.dump((cache, A), f)
        except IOError:
            logger.warning("Could not save unit conversion cache to file '{}'"
                           .format(cache_path))
    atexit.register(save_cache)
    si_lengths = [sum(abs(si) for si in d.dimension) for d in basis]
    return A, cache, si_lengths


class BaseDimensionToUnitMapper(object):

    

    def __init__(self):
        assert all(u.offset == 0 for u in self.basis), (
            "Non-zero offsets found in basis units")
        # Get matrix of basis unit dimensions
        self.A = array([list(b.dimension) for b in self.basis]).T
        # Get cache path from file path of subclass
        self._cache_path = os.path.join(
            os.path.dirname(sys.modules[self.__module__].__file__),
            self._CACHE_FILENAME)
        try:
            with open(self._cache_path) as f:
                self._cache, loaded_A = pkl.load(f)
                # If the dimension matrix has been changed since the cache was
                # generated, reset the cache
                if (loaded_A != self.A).all():
                    self._cache = {}
        except (IOError, EOFError):
            logger.warning("Could not load unit conversion cache from file "
                           "'{}'".format(self._cache_path))
            self._cache = {}
        self.si_lengths = [sum(abs(si) for si in d.dimension)
                           for d in self.basis]

    def save_cache(self):
        try:
            with open(self._cache_path, 'w') as f:
                pkl.dump((self._cache, self.A), f)
        except IOError:
            logger.warning("Could not save unit conversion cache to file '{}'"
                           .format(self._cache_path))

    def map_to_units(self, dimension):
        """
        Projects a given unit onto a list of units that span the space of
        dimensions present in the unit to project.

        Returns a list of the basis units with their associated powers and the
        scale of the presented units.
        """
        if dimension == 1:
            return un.unitless
        if isinstance(dimension, sympy.Basic):
            dimension = un.Dimension.from_sympy(dimension)
        else:
            assert isinstance(dimension, un.Dimension), (
                "'{}' is not a Dimension".format(dimension))
        try:
            # Check to see if unit dimension is in basis
            base_unit = next(u for u in self.basis
                             if u.dimension == dimension)
            compound = [(base_unit, 1)]
            exponent = -base_unit.power
        except StopIteration:
            try:
                # Check cache for precalculated compounds
                min_x = self._cache[tuple(dimension)]
            except KeyError:
                # Get projection of dimension onto basis units
                b = array(list(dimension))
                xs = diophantine.solve(self.A, b)
                min_x = self._minium_combination(xs)
                self._cache[tuple(dimension)] = min_x
            # Get list of compound units with the powers
            compound = [(u, p) for u, p in zip(self.basis, min_x) if p]
            # Calculate the appropriate scale for the new compound quantity
            exponent = -min_x.dot([b.power for b in self.basis])
        return exponent, compound

    def _minium_combination(self, xs):
        # Find the number of units in each of the compounds
        lengths = [sum(abs(x)) for x in xs]
        min_length = min(lengths)
        min_length_xs = [x for x, l in zip(xs, lengths) if l == min_length]
        # If there are multiple compounds of equal length pick the compound
        # with the smallest number of base units
        if len(min_length_xs) > 1:
            si_length_sums = [x.dot(self.si_lengths) for x in min_length_xs]
            min_x = min_length_xs[argmin(si_length_sums)]
        else:
            min_x = min_length_xs[0]
        return min_x

    @classmethod
    def to_quantity(cls, value, units):
        dim = units.dimension
        return (value * 10 ** units.power + units.offset) * (
            pq.s ** dim.t * pq.kg ** dim.m * pq.m ** dim.l * pq.mole ** dim.n *
            pq.K ** dim.k * pq.cd ** dim.j * pq.A ** dim.i)

    @classmethod
    def scale_to(cls, units, target_units):
        assert units.dimension == target_units.dimension
        return units.power - target_units.power


class BaseExpressionUnitScaler(DynamicsDimensionResolver):

    def __init__(self, component_class):
        self._scaled = {}
        for a in component_class.attributes_with_dimension:
            if not isinstance(a, SendPortBase):
                self._scaled[sympify(a)] = sympify(a)
        for a in component_class.attributes_with_units:
            self._scaled[sympify(a)] = sympify(a)
        super(BaseExpressionUnitScaler, self).__init__(component_class)

    def scale_expression(self, element):
        assert element in self.component_class
        scaled_expr, dims = self._flatten(sympify(element))
        _, units = self._mapper.map_to_units(dims)
        return scaled_expr, units

    def _flatten_symbol(self, sym):
        try:
            scaled_expr = self._scaled[sym]
            dims = self._dims[sym]
        except KeyError:
            element = self._find_element(sym)
            scaled_expr, dims = self._flatten(element.rhs)
            self._scaled[sym] = scaled_expr
            self._dims[sym] = dims
        return scaled_expr, dims

    def _flatten_boolean(self, expr):  # @UnusedVariable
        dims = super(BaseExpressionUnitScaler, self)._flatten_boolean(expr)
        scaled_expr = type(expr)(*(self._flatten(a)[0] for a in expr.args))
        return scaled_expr, dims

    def _flatten_constant(self, expr):  # @UnusedVariable
        dims = super(BaseExpressionUnitScaler, self)._flatten_constant(expr)
        return expr, dims

    def _flatten_reserved(self, expr):
        return expr, self.reserved_symbol_dims[expr]

    def _flatten_function(self, expr):  # @UnusedVariable
        dims = super(BaseExpressionUnitScaler, self)._flatten_function(expr)
        scaled_expr = type(expr)(*(self._flatten(a) for a in expr.args))
        return scaled_expr, dims

    def _flatten_matching(self, expr):
        arg_exprs, arg_dims = zip(*[self._flatten(a) for a in expr.args])
        scaled_expr = type(expr)(*arg_exprs)
        return scaled_expr, arg_dims[0]

    def _flatten_multiplied(self, expr):
        arg_exprs, arg_dims = zip(*[self._flatten(a) for a in expr.args])
        dims = reduce(operator.mul, arg_dims)
        if isinstance(dims, sympy.Basic):
            dims = dims.powsimp()  # Simplify the expression
        power, _ = self._mapper.map_to_units(un.Dimension.from_sympy(dims))
        arg_power = sum(
            self._mapper.map_to_units(self._flatten(a)[1])[0]
            for a in arg_exprs)
        scale = power - arg_power
        return 10 ** scale * type(expr)(*expr.args), dims

    def _flatten_power(self, expr):
        base, exponent = expr.args
        scaled_base, dims = self._flatten(base)
        return scaled_base ** exponent, dims ** exponent
