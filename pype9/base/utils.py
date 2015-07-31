import os
import logging
import operator
from itertools import chain
import collections
import cPickle as pkl
from abc import ABCMeta, abstractmethod
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


class BaseUnitAssigner(DynamicsDimensionResolver):
    """
    Base class for simulator-specific "unit assigners", which map dynamics
    class dimensions onto a set of "basis" unit compounds that the simulator
    expects
    """

    __metaclass__ = ABCMeta

    _CACHE_FILENAME = '.unit_mapping_cache.pkl'

    def __init__(self, component_class):
        self._scaled = {}
        for a in component_class.attributes_with_dimension:
            if not isinstance(a, SendPortBase):
                self._scaled[sympify(a)] = sympify(a)
        for a in component_class.attributes_with_units:
            self._scaled[sympify(a)] = sympify(a)
        super(DynamicsDimensionResolver, self).__init__(component_class)

    def _assign_units(self, element):
        assert element in self.component_class
        scaled_expr, dims = self._flatten(sympify(element))
        _, units = self.dimension_to_units(dims)
        return scaled_expr, self.unit_to_str(units)

    def assign_units(self, elements):
        """
        Iterate through a list of elements, yielding a scaled version along
        with a string representation of the units
        """
        if isinstance(elements, collections.Iterable):
            # If list or tuple of elements, yield scaled expression and units
            # for each element in the list.
            for elem in elements:
                yield elem, self.scale_expression(elem)
        else:  # A single element to provide units for
            return self._assign_units(elements)

    @abstractmethod
    def unit_to_str(self, unit):
        pass

    @classmethod
    def dimension_to_units(cls, dimension):
        """
        Projects a given unit onto a list of units that span the space of
        dimensions present in the unit to project.

        Returns a list of the basis units with their associated powers and the
        scale of the presented units.
        """
        if dimension == 1:
            return 1, []
        if isinstance(dimension, sympy.Basic):
            dimension = un.Dimension.from_sympy(dimension)
        else:
            assert isinstance(dimension, un.Dimension), (
                "'{}' is not a Dimension".format(dimension))
        try:
            # Check to see if unit dimension is in basis units or specific
            # compounds
            base_unit = next(u for u in chain(cls.basis, cls.compounds)
                             if u.dimension == dimension)
            compound = [(base_unit, 1)]
            exponent = -base_unit.power
        except StopIteration:
            try:
                # Check cache for precalculated compounds
                min_x = cls.cache[tuple(dimension)]
            except KeyError:
                # Get projection of dimension onto basis units
                b = array(list(dimension))
                xs = diophantine.solve(cls.A, b)
                min_x = cls._minium_combination(xs)
                cls.cache[tuple(dimension)] = min_x
            # Get list of compound units with the powers
            compound = [(u, p) for u, p in zip(cls.basis, min_x) if p]
            # Calculate the appropriate scale for the new compound quantity
            exponent = -min_x.dot([b.power for b in cls.basis])
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

    @classmethod
    def _load_basis_matrices_and_cache(cls, basis, directory):
        """
        Creates matrix corresponding to unit basis and loads cache of
        previously calculated mappings from dimensions onto this basis.
        """
        assert all(u.offset == 0 for u in basis), (
            "Non-zero offsets found in basis units")
        # Get matrix of basis unit dimensions
        A = array([list(b.dimension) for b in basis]).T
        # Get cache path from file path of subclass
        cache_path = os.path.join(directory, cls._CACHE_FILENAME)
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
                logger.warning("Could not save unit conversion cache to file "
                               "'{}'".format(cache_path))
        atexit.register(save_cache)
        # The lengths in terms of SI dimension bases of each of the unit
        # basis compounds.
        si_lengths = [sum(abs(si) for si in d.dimension) for d in basis]
        return A, cache, si_lengths

    @classmethod
    def _minium_combination(cls, xs):
        # Find the number of units in each of the compounds
        lengths = [sum(abs(x)) for x in xs]
        min_length = min(lengths)
        min_length_xs = [x for x, l in zip(xs, lengths) if l == min_length]
        # If there are multiple compounds of equal length pick the compound
        # with the smallest number of base units
        if len(min_length_xs) > 1:
            si_length_sums = [x.dot(cls.si_lengths) for x in min_length_xs]
            min_x = min_length_xs[argmin(si_length_sums)]
        else:
            min_x = min_length_xs[0]
        return min_x

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
        dims = super(DynamicsDimensionResolver, self)._flatten_boolean(expr)
        scaled_expr = type(expr)(*(self._flatten(a)[0] for a in expr.args))
        return scaled_expr, dims

    def _flatten_constant(self, expr):  # @UnusedVariable
        dims = super(DynamicsDimensionResolver, self)._flatten_constant(expr)
        return expr, dims

    def _flatten_reserved(self, expr):
        return expr, self.reserved_symbol_dims[expr]

    def _flatten_function(self, expr):  # @UnusedVariable
        dims = super(DynamicsDimensionResolver, self)._flatten_function(expr)
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
        power, _ = self.dimension_to_units(dims)
        arg_power = sum(self.dimension_to_units(self._flatten(a)[1])[0]
                        for a in arg_exprs)
        scale = power - arg_power
        return 10 ** scale * type(expr)(*expr.args), dims

    def _flatten_power(self, expr):
        base, exponent = expr.args
        scaled_base, dims = self._flatten(base)
        return scaled_base ** exponent, dims ** exponent
