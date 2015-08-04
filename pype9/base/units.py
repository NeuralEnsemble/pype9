import os
import logging
import operator
from itertools import chain
import cPickle as pkl
from abc import ABCMeta, abstractmethod
import sympy
from sympy import sympify
from numpy import array, sum, abs, argmin, log10
import quantities as pq
import diophantine
from nineml import units as un
from nineml.user.component import Quantity
from nineml.abstraction.ports import SendPortBase
from nineml.abstraction.dynamics.visitors import DynamicsDimensionResolver
import atexit
from pype9.exceptions import Pype9RuntimeError


logger = logging.getLogger('PyPe9')


class UnitHandler(DynamicsDimensionResolver):
    """
    Base class for simulator-specific "unit assigners", which map dynamics
    class dimensions onto a set of "basis" unit compounds that the simulator
    expects
    """

    __metaclass__ = ABCMeta

    _CACHE_FILENAME = '.unit_handler_cache.pkl'

    def __init__(self, component_class):
        self._scaled = {}
        for a in component_class.attributes_with_dimension:
            if not isinstance(a, SendPortBase):
                self._scaled[sympify(a)] = sympify(a)
        for a in component_class.attributes_with_units:
            self._scaled[sympify(a)] = sympify(a)
        super(DynamicsDimensionResolver, self).__init__(component_class)

    def assign_units_to_alias(self, alias):
        assert alias in self.component_class
        dims = self._flatten(sympify(alias))[1]
        units = self.dimension_to_units_compound(dims)[1]
        return self._units_for_code_gen(units)

    def assign_units_to_aliases(self, aliases):
        """
        Iterate through a list of elements, yielding a scaled version along
        with a string representation of the units
        """
        # If list or tuple of elements, yield scaled expression and units
        # for each element in the list.
        for alias in aliases:
            yield alias, self.assign_units_to_alias(alias)

    def assign_units_to_constant(self, constant):
        exponent, compound = self.dimension_to_units_compound(
            constant.units.dimension)
        scale = exponent - constant.units.power
        return (10 ** scale * constant.value,
                self._units_for_code_gen(compound))

    def assign_units_to_constants(self, constants):
        for const in constants:
            yield (const,) + self.assign_units_to_constant(const)

    def assign_units_to_variable(self, parameter, derivative_of=False):
        _, compound = self.dimension_to_units_compound(parameter.dimension)
        if derivative_of:
            compound.append((un.ms, -1))
        return self._units_for_code_gen(compound)

    def assign_units_to_variables(self, parameters):
        for param in parameters:
            yield param, self.assign_units_to_variable(param)

    def scale_rhs(self, element):
        assert element in self.component_class
        scaled_expr, dims = self._flatten(sympify(element.rhs))
        units_str = self._units_for_code_gen(
            self.dimension_to_units_compound(dims)[1])
        return scaled_expr, units_str

    def scale_rhss(self, elements):
        for elem in elements:
            scaled_expr, units_str = self.scale_rhs(elem)
            yield elem, scaled_expr, units_str

    @abstractmethod
    def _units_for_code_gen(self, unit):
        pass

    @classmethod
    def dimension_to_units_compound(cls, dimension):
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
            exponent = min_x.dot([b.power for b in cls.basis])
        return exponent, compound

    @classmethod
    def dimension_to_units(cls, dimension):
        """
        Returns the units associated with the given dimension
        """
        exponent, compound = cls.dimension_to_units_compound(dimension)
        unit_name = cls._unit_name_from_compound(compound)
        return un.Unit(unit_name, dimension=dimension, power=-exponent)

    @classmethod
    def compound_to_units_str(cls, compound, mult_symbol='*'):
        """
        Converts a compound unit list into a string representation
        """
        if not compound:
            unit_str = '1'
        else:
            numerator = mult_symbol.join(
                '{}{}'.format(cls.unit_name_map[u], p if p > 1 else '')
                for u, p in compound if p > 0)
            denominator = mult_symbol.join(
                '{}{}'.format(cls.unit_name_map[u], -p if p < -1 else '')
                for u, p in compound if p < 0)
            if numerator and denominator:
                unit_str = numerator + '/' + denominator
            elif denominator:
                unit_str = '1/' + denominator
            else:
                unit_str = numerator
        return unit_str

    @classmethod
    def dimension_to_unit_str(cls, dimension):
        """
        Returns the units associated with the given dimension
        """
        return cls.compound_to_units_str(
            cls.dimension_to_units_compound(dimension)[1])

    @classmethod
    def scale_value(cls, qty):
        exponent, _ = cls.dimension_to_units_compound(qty.units.dimension)
        return 10 ** (exponent - qty.units.power) * qty.value

    @classmethod
    def assign_units(cls, value, dimension):
        _, compound = cls.dimension_to_units_compound(dimension)
        return pq.Quantity(value, cls.compound_to_units_str(compound))

    @classmethod
    def to_pq_quantity(cls, qty):
        exponent, compound = cls.dimension_to_units_compound(
            qty.units.dimension)
        scale = exponent - qty.units.power
        units_str = cls.compound_units_str(compound)
        return 10 ** scale * pq.Quantity(qty.value, units_str)

    @classmethod
    def from_pq_quantity(cls, qty):
        if isinstance(qty, (int, float)):
            units = un.unitless
        elif isinstance(qty, pq.Quantity):
            unit_name = str(qty.units).split()[1].replace(
                '/', '_per_').replace('*', '_')
            powers = {}
            for si_unit, power in \
                    qty.units.simplified._dimensionality.iteritems():
                if isinstance(si_unit, pq.UnitMass):
                    powers['m'] = power
                elif isinstance(si_unit, pq.UnitLength):
                    powers['l'] = power
                elif isinstance(si_unit, pq.UnitTime):
                    powers['t'] = power
                elif isinstance(si_unit, pq.UnitCurrent):
                    powers['i'] = power
                elif isinstance(si_unit, pq.UnitLuminousIntensity):
                    powers['j'] = power
                elif isinstance(si_unit, pq.UnitSubstance):
                    powers['n'] = power
                elif isinstance(si_unit, pq.UnitTemperature):
                    powers['k'] = power
                else:
                    assert False, "Unrecognised units '{}'".format(si_unit)
            dimension = un.Dimension(unit_name + 'Dimension', **powers)
            units = un.Unit(unit_name, dimension=dimension,
                            power=log10(float(qty.units.simplified)))
        else:
            raise Pype9RuntimeError(
                "Cannot '{}' to nineml.Quantity (can only convert "
                "quantities.Quantity and numeric objects)"
                .format(qty))
        return Quantity(float(qty), units)

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

    @classmethod
    def _unit_name_from_compound(cls, compound):
        numerator = '_'.join(u.name for u, p in compound if p > 0)
        denominator = '_'.join(u.name for u, p in compound if p < 0)
        if denominator and numerator:
            unit_name = numerator + '_per_' + denominator
        elif numerator:
            unit_name = numerator
        elif denominator:
            unit_name = 'per_' + denominator
        return unit_name

    # Override DynamicsDimensionResolver methods to include the scaling of
    # sub expressions where it is required (i.e. when there is a change of
    # units and the new units power is different)

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
        power, _ = self.dimension_to_units_compound(dims)
        arg_power = sum(
            self.dimension_to_units_compound(self._flatten(a)[1])[0]
            for a in arg_exprs)
        scale = power - arg_power
        return 10 ** scale * type(expr)(*expr.args), dims

    def _flatten_power(self, expr):
        base, exponent = expr.args
        scaled_base, dims = self._flatten(base)
        return scaled_base ** exponent, dims ** exponent
