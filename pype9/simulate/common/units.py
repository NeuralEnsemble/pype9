from __future__ import division
import os
import logging
import operator
from itertools import chain
from operator import xor
import cPickle as pkl
from abc import ABCMeta, abstractmethod
import sympy
from sympy import sympify
import numpy
from numpy import array, sum, abs, argmin, log10, nonzero
import quantities as pq
import diophantine
from nineml import units as un
from nineml.user.component import Quantity
from nineml.abstraction import Expression
from nineml.abstraction.dynamics.visitors import DynamicsDimensionResolver
import atexit
from pype9.exceptions import Pype9RuntimeError
from pype9.utils import classproperty
from fractions import gcd
numpy.seterr(all='raise')


logger = logging.getLogger('PyPe9')


class UnitHandler(DynamicsDimensionResolver):
    """
    Base class for simulator-specific "unit assigners", which map dynamics
    class dimensions onto a set of "basis" unit compounds that the simulator
    expects
    """

    __metaclass__ = ABCMeta

    _pq_si_to_dim = {pq.UnitMass: 'm', pq.UnitLength: 'l', pq.UnitTime: 't',
                     pq.UnitCurrent: 'i', pq.UnitLuminousIntensity: 'j',
                     pq.UnitSubstance: 'n', pq.UnitTemperature: 'k'}

    _CACHE_FILENAME = '.unit_handler_cache.pkl'

    def assign_units_to_alias(self, alias):
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
        if isinstance(constant, basestring):
            constant = self.component_class[constant]
        exponent, compound = self.dimension_to_units_compound(
            constant.units.dimension)
        scale = constant.units.power - exponent
        return (10 ** scale * constant.value,
                self._units_for_code_gen(compound))

    def assign_units_to_constants(self, constants):
        for const in constants:
            yield (const,) + self.assign_units_to_constant(const)

    def assign_units_to_random_variable(self, random_variable):
        if isinstance(random_variable, basestring):
            random_variable = self.component_class[random_variable]
        exponent, compound = self.dimension_to_units_compound(
            random_variable.units.dimension)
        scale = random_variable.units.power - exponent
        return (10 ** scale, self._units_for_code_gen(compound))

    def assign_units_to_random_variables(self, constants):
        for const in constants:
            yield (const,) + self.assign_units_to_random_variable(const)

    def assign_units_to_variable(self, variable, derivative_of=False):
        if isinstance(variable, basestring):
            variable = self.component_class.element(variable)
        _, compound = self.dimension_to_units_compound(variable.dimension)
        if derivative_of:
            compound.append((un.ms, -1))
        return self._units_for_code_gen(compound)

    def assign_units_to_variables(self, parameters):
        for param in parameters:
            yield param, self.assign_units_to_variable(param)

    def scale_expr(self, expr):
        scaled, dims = self._flatten(sympify(expr))
        units_str = self._units_for_code_gen(
            self.dimension_to_units_compound(dims)[1])
        return Expression(scaled), units_str

    def scale_alias(self, element):
        if isinstance(element, basestring):
            element = self.component_class.element(element)
        scaled, dims = self._flatten(sympify(element.rhs))
        units_str = self._units_for_code_gen(
            self.dimension_to_units_compound(dims)[1])
        return Expression(scaled), units_str

    def scale_aliases(self, elements):
        for elem in elements:
            scaled, units_str = self.scale_alias(elem)
            yield elem, scaled, units_str

    def scale_time_derivative(self, element):
        """
        Scales the time derivative, ensuring that the overall expression is in
        the same units as the state variable divided by the time units
        """
        if isinstance(element, basestring):
            element = self.component_class[element]
        expr, dims = self._flatten(sympify(element.rhs))
        state_var_dims = self.component_class.state_variable(
            element.variable).dimension
        assert dims == state_var_dims / un.time
        exp = self.dimension_to_units_compound(dims)[0]
        target_exp, compound = self.dimension_to_units_compound(state_var_dims)
        # Divide the state variable units by the time units to get the target
        # compound
        try:
            time_unit, power = compound.pop(
                next(i for i, (u, _) in enumerate(compound)
                     if u.dimension == un.time))
            compound.append((time_unit, power - 1))
        except StopIteration:
            compound.append((self.time_units, -1))
        target_exp -= self.time_units.power
        scale = exp - target_exp
        # Scale expression to match target expression
        expr = 10 ** scale * expr
        units_str = self._units_for_code_gen(compound)
        return Expression(expr), units_str

    def scale_time_derivatives(self, elements):
        for elem in elements:
            scaled, units_str = self.scale_time_derivative(elem)
            yield elem, scaled, units_str

    @classproperty
    @classmethod
    def time_units(cls):
        try:
            return next(u for u in cls.basis if u.dimension == un.time)
        except StopIteration:
            assert False, "No time dimension in basis"

    @abstractmethod
    def _units_for_code_gen(self, unit):
        pass

    @classproperty
    @classmethod
    def specified_units(cls):
        return chain(cls.basis, cls.compounds)

    @classmethod
    def dimension_to_units_compound(cls, dimension):
        """
        Projects a given unit onto a list of units that span the space of
        dimensions present in the unit to project.

        Returns a list of the basis units with their associated powers and the
        scale of the presented units.
        """
        if dimension == 1 or dimension == un.dimensionless:
            return 0, []
        if isinstance(dimension, sympy.Basic):
            dimension = un.Dimension.from_sympy(dimension)
        else:
            assert isinstance(dimension, un.Dimension), (
                "'{}' is not a Dimension".format(dimension))
        # Check to see if unit dimension, or some integer power thereof,
        # has been stored in the cache (the basis and compounds are preloaded)
        dim_vector = array(list(dimension), dtype='float')
        # mask of units in compound
        mask = (dim_vector != 0)
        # Get the coefficients required to transform the basis dim elements
        # into the provided dimension, and test to see if they are constant
        with_scalars = [(x, numpy.unique(dim_vector[mask] /
                                         numpy.asarray(d)[mask]))
                        for d, x in cls.cache.iteritems()
                        if ((numpy.asarray(d) != 0) == mask).all()]
        matches = [(u, int(s[0])) for u, s in with_scalars
                   if len(s) == 1 and float(s[0]).is_integer()]
        assert len(matches) <= 1, (
            "There should not be matches for multiple basis/compound units, "
            "the dimension vector of one must be a factor of an another")
        # If there is a match and the scalar is an integer then use that unit
        # basis/compound.
        if matches and float(matches[0][1]).is_integer():
            base_x, scalar = matches[0]
            scalar = int(scalar)
            num_compounds = len(nonzero(x[len(cls.basis):])[0])
            assert num_compounds <= 1, (
                "Multiple compound indices matched (x={})".format(x))
            assert xor(x[:len(cls.basis)].any(), num_compounds != 0), (
                "Mix of basis vectors and compounds (x={})".format(x))
            x = base_x * scalar
        # If there is not a direct relationship to a basis vector or special
        # compound, project the dimension onto the basis vectors, finding
        # the "minimal" solution (see _select_best_compound)
        else:
            # Get projection of dimension onto basis units
            b = array(list(dimension))
            xs = diophantine.solve(cls.A, b)
            min_x = cls._select_best_compound(xs)
            x = numpy.concatenate((min_x, numpy.zeros(len(cls.compounds),
                                                      dtype='int')))
            cls.cache[tuple(dimension)] = x / int(abs(reduce(gcd, x)))
        # Get list of compound units with the powers
        compound = [(u, p) for u, p in zip(cls.specified_units, x) if p]
        # Calculate the appropriate scale for the new compound quantity
        exponent = int(x.dot([b.power for b in cls.specified_units]))
        return exponent, compound

    @classmethod
    def dimension_to_units(cls, dimension):
        """
        Returns the units associated with the given dimension
        """
        exponent, compound = cls.dimension_to_units_compound(dimension)
        unit_name = cls._unit_name_from_compound(compound)
        if isinstance(dimension, sympy.Basic):
            dimension = un.Dimension.from_sympy(dimension)
        return un.Unit(unit_name, dimension=dimension, power=exponent)

    @classmethod
    def compound_to_units_str(cls, compound, pow_symbol='**', mult_symbol='*',
                              use_parentheses=True):
        """
        Converts a compound unit list into a string representation
        """
        numerator = [(u, p) for u, p in compound if p > 0]
        denominator = [(u, -p) for u, p in compound if p < 0]
        num_str, den_str = [
            mult_symbol.join(
                cls.unit_name_map[u] + (pow_symbol + str(int(p))
                                        if p > 1 else '')
                for u, p in num_den)
            for num_den in (numerator, denominator)]
        if num_str:
            unit_str = num_str
        else:
            unit_str = '1'
        if den_str:
            if use_parentheses and len(denominator) > 1:
                den_str = '(' + den_str + ')'
            unit_str += '/' + den_str
        return unit_str

    @classmethod
    def dimension_to_unit_str(cls, dimension, one_as_dimensionless=False):
        """
        Returns the units associated with the given dimension
        """
        unit_str = cls.compound_to_units_str(
            cls.dimension_to_units_compound(dimension)[1])
        if one_as_dimensionless and unit_str == '1':
            unit_str = 'dimensionless'
        return unit_str

    @classmethod
    def scale_value(cls, qty):
        if isinstance(qty, pq.Quantity):
            value = numpy.asarray(qty)
            # Get the first or only value of the quantity
            try:
                elem = qty[0]
            except IndexError:
                elem = qty
            units = cls.from_pq_quantity(elem).units
        else:
            try:
                units = qty.units
                if qty.value.nineml_type == 'SingleValue':
                    value = float(qty.value)
                elif qty.value.nineml_type == 'ArrayValue':
                    value = numpy.array(qty.value)
                else:
                    if cls.scalar(units) == 1:
                        return qty.value
                    else:
                        # FIXME: Should be not supported error??
                        raise NotImplementedError(
                            "RandomDistributionValue quantities cannot be scaled at this "
                            "time ({})".format(qty))
            except AttributeError:
                return qty  # Float or int value quantity
        scaled = value * cls.scalar(units)
        return scaled

    @classmethod
    def scalar(cls, units):
        exponent, _ = cls.dimension_to_units_compound(units.dimension)
        return 10 ** (units.power - exponent)

    @classmethod
    def assign_units(cls, value, dimension):
        _, compound = cls.dimension_to_units_compound(dimension)
        return pq.Quantity(value, cls.compound_to_units_str(compound))

    @classmethod
    def to_pq_quantity(cls, qty):
        exponent, compound = cls.dimension_to_units_compound(
            qty.units.dimension)
        scale = qty.units.power - exponent
        units_str = cls.compound_to_units_str(compound)
        return pq.Quantity(10 ** scale * float(qty.value), units_str)

    @classmethod
    def from_pq_quantity(cls, qty):
        if isinstance(qty, Quantity):
            return qty  # If already a 9ML quantity
        elif isinstance(qty, (int, float)):
            units = un.unitless
        elif isinstance(qty, pq.Quantity):
            unit_name = str(qty.units).split()[1].replace(
                '/', '_per_').replace('**', '').replace('*', '_').replace(
                    '(', '').replace(')', '')
            if unit_name.startswith('_per_'):
                unit_name = unit_name[1:]  # strip leading underscore
            powers = dict(
                (cls._pq_si_to_dim[type(u)], p)
                for u, p in qty.units.simplified._dimensionality.iteritems())
            dimension = un.Dimension(unit_name + 'Dimension', **powers)
            units = un.Unit(unit_name, dimension=dimension,
                            power=int(log10(float(qty.units.simplified))))
        else:
            raise Pype9RuntimeError(
                "Cannot '{}' to nineml.Quantity (can only convert "
                "quantities.Quantity and numeric objects)"
                .format(qty))
        return Quantity(float(qty), units)

    @classmethod
    def _load_basis_matrices_and_cache(cls, basis, compounds, directory):
        """
        Creates matrix corresponding to unit basis and loads cache of
        previously calculated mappings from dimensions onto this basis.
        """
        assert all(u.offset == 0 for u in basis), (
            "Non-zero offsets found in basis units")
        assert any(u.dimension == un.time for u in basis), (
            "No pure time dimension found in basis units")
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
        except:
            logger.info("Building unit conversion cache in file '{}'"
                        .format(cache_path))
            cache = cls._init_cache(basis, compounds)
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
        return A, cache, cache_path, si_lengths

    @classmethod
    def _init_cache(cls, basis, compounds):
        """
        Removes the existing cache of unit projections and creates a new one in
        its place
        """
        # Get the length of the "x" vectors, which hold the combination of
        # basis vectors required to represent a given dimension
        num_units = len(basis) + len(compounds)
        # Create a new cache with the basis units and specified compound units
        # entered into it
        cache = {}
        for i, unit in enumerate(chain(basis, compounds)):
            x = numpy.zeros(num_units, dtype='int')
            x[i] = 1
            cache[tuple(unit.dimension)] = x
        return cache

    @classmethod
    def clear_cache(cls):
        """
        Removes the existing cache of unit projections and creates a new one in
        its place
        """
        # Removed saved version of cache
        if os.path.exists(cls.cache_path):
            os.remove(cls.cache_path)
        # Create a new cache with the specified units entered into it
        cls.cache = cls._init_cache(cls.basis, cls.compounds)

    @classmethod
    def _select_best_compound(cls, xs):
        """
        Selects the "best" combination of units based on the number of units
        in the compound, then the ones with the smallest number of SI units,
        then the ones with the lowest indices in the basis list
        """
        # Convert xs to numpy arrays
        xs = [numpy.asarray(list(x), dtype='int') for x in xs]
        # Find the number of units in each of the compounds
        lengths = [sum(abs(x)) for x in xs]
        min_length = min(lengths)
        min_length_xs = [x for x, l in zip(xs, lengths) if l == min_length]
        # If there are multiple compounds of equal length pick the compound
        # with the smallest number of base units
        if len(min_length_xs) == 1:
            min_x = min_length_xs[0]
        else:
            si_length_sums = [abs(x).dot(cls.si_lengths)
                              for x in min_length_xs]
            min_si_length_sum = min(si_length_sums)
            min_si_length_sums = [x for x, l in zip(min_length_xs,
                                                    si_length_sums)
                                  if l == min_si_length_sum]
            if len(min_si_length_sums) == 1:
                min_x = min_si_length_sums[0]
            else:
                index_sums = [nonzero(x)[0].sum() for x in min_si_length_sums]
                min_x = min_si_length_sums[argmin(index_sums)]
        return min_x

    @classmethod
    def _unit_name_from_compound(cls, compound):
        numerator = '_'.join(u.name + (str(p) if p > 1 else '')
                             for u, p in compound if p > 0)
        denominator = '_'.join(u.name + (str(-p) if p < -1 else '')
                               for u, p in compound if p < 0)
        if denominator and numerator:
            unit_name = numerator + '_per_' + denominator
        elif numerator:
            unit_name = numerator
        elif denominator:
            unit_name = 'per_' + denominator
        else:
            unit_name = 'unitless'
        return unit_name

    # Override DynamicsDimensionResolver methods to include the scaling of
    # sub expressions where it is required (i.e. when there is a change of
    # units and the new units power is different)

    def _flatten_symbol(self, sym, **kwargs):  # @UnusedVariable
        try:
            dims = self._dims[sym]
        except KeyError:
            element = self._find_element(sym)
            try:
                dims = self._flatten(element.rhs)[1]
            except AttributeError:
                assert False, (
                    "Dimensions or units of {} were not set in __init__ "
                    "method".format(element))
            self._dims[sym] = dims
        return sym, dims

    def _flatten_boolean(self, expr, **kwargs):  # @UnusedVariable
        dims = super(DynamicsDimensionResolver, self)._flatten_boolean(
            expr, **kwargs)
        scaled_expr = type(expr)(*(self._flatten(a)[0] for a in expr.args))
        return scaled_expr, dims

    def _flatten_constant(self, expr, **kwargs):  # @UnusedVariable
        dims = super(DynamicsDimensionResolver, self)._flatten_constant(
            expr, **kwargs)
        return expr, dims

    def _flatten_reserved(self, expr, **kwargs):  # @UnusedVariable
        return expr, self.reserved_symbol_dims[expr]

    def _flatten_function(self, expr, **kwargs):  # @UnusedVariable
        dims = super(DynamicsDimensionResolver, self)._flatten_function(
            expr, **kwargs)
        scaled_expr = type(expr)(*(self._flatten(a)[0] for a in expr.args))
        return scaled_expr, dims

    def _flatten_matching(self, expr, **kwargs):  # @UnusedVariable
        arg_exprs, arg_dims = zip(*[self._flatten(a) for a in expr.args])
        scaled_expr = type(expr)(*arg_exprs)
        return scaled_expr, arg_dims[0]

    def _flatten_multiplied(self, expr, **kwargs):  # @UnusedVariable
        arg_dims = [self._flatten(a)[1] for a in expr.args]
        dims = reduce(operator.mul, arg_dims)
        if isinstance(dims, sympy.Basic):
            dims = dims.powsimp()  # Simplify the expression
        power = self.dimension_to_units_compound(dims)[0]
        arg_power = sum(self.dimension_to_units_compound(d)[0]
                        for d in arg_dims)
        scale = int(arg_power - power)
        return 10 ** scale * type(expr)(*expr.args), dims

    def _flatten_power(self, expr, **kwargs):  # @UnusedVariable
        base, exponent = expr.args
        scaled_base, dims = self._flatten(base)
        return scaled_base ** exponent, dims ** exponent
