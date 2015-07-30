import os
import sys
import logging
import cPickle as pkl
from numpy import array, sum, abs, argmin
import quantities as pq
import diophantine
from nineml.abstraction.dynamics.visitors import DynamicsDimensionResolver


logger = logging.getLogger('PyPe9')


class BaseDimensionToUnitMapper(object):

    _CACHE_FILENAME = '.unit_conversion_cache.pkl'

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
                if loaded_A != self.A:
                    self._cache = {}
        except (IOError, EOFError):
            logger.warning("Could not load unit conversion cache from file "
                           "'{}'".format(self._cache_path))
            self._cache = {}

    def __del__(self):
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
                min_x = xs[argmin(sum(abs(x)) for x in xs)]
                self._cache[tuple(dimension)] = min_x
            # Get list of compound units with the powers
            compound = [(u, p) for u, p in zip(self.basis, min_x) if p]
            # Calculate the appropriate scale for the new compound quantity
            exponent = -min_x.dot([b.power for b in self.basis])
        return exponent, compound

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


class ExpressionUnitScaler(DynamicsDimensionResolver):

    def __init__(self, component_class):
        super(ExpressionUnitScaler, self).__init__(component_class)
        self._scaled = {}

    def _flatten_boolean(self, expr):  # @UnusedVariable
        units = self._mapper.map_to_units(
            super(ExpressionUnitScaler, self)._flatten_boolean(expr))
        scaled_expr = type(expr)(*(self._flatten(a)[0] for a in expr.args))
        return scaled_expr, units

    def _flatten_constant(self, expr):  # @UnusedVariable
        units = self._mapper.map_to_units(
            super(ExpressionUnitScaler, self)._flatten_constant(expr))
        return expr, units

    def _flatten_reserved(self, expr):
        return expr, self.reserved_symbol_dims[expr]

    def _flatten_function(self, expr):  # @UnusedVariable
        units = self._mapper.map_to_units(
            super(ExpressionUnitScaler, self)._flatten_function(expr))
        scaled_expr = type(expr)(*(self._flatten(a)[0] for a in expr.args))
        return scaled_expr, units

    def _flatten_matching(self, expr):
        units = self._mapper.map_to_units(
            super(ExpressionUnitScaler, self)._flatten_matching(expr))
        scaled_expr = type(expr)(*(self._flatten(a)[0] for a in expr.args))
        return scaled_expr, units

    def _flatten_multiplied(self, expr):
        units = self._mapper.map_to_units(
            super(ExpressionUnitScaler, self)._flatten_multiplied(expr))
        arg_power = sum(self._mapper.map_to_units(self._flatten(a)[1]).power
                        for a in expr.args)
        scale = units.power - arg_power
        return type(expr)(*((10 ** scale,) + expr.args)), units

    def _flatten_power(self, expr):
        units = self._mapper.map_to_units(
            super(ExpressionUnitScaler, self)._flatten_power(expr))
        scaled_expr = type(expr)(*(self._flatten(a)[0] for a in expr.args))
        return scaled_expr, units

    def _flatten_symbol(self, expr):
        units = self._mapper.map_to_units(
            super(ExpressionUnitScaler, self)._flatten_symbol(expr))
        scaled_expr = type(expr)(*(self._flatten(a)[0] for a in expr.args))
        return scaled_expr, units

    def _set_dims(self, expr, flattened):
        super(ExpressionUnitScaler, self)._set_dims(
            expr, flattened[1].dimension)
