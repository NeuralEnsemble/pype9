from numpy import array, sum, abs, argmin
import os
import sys
import quantities as pq
import cPickle as pkl
import logging
from diophantine import solve

logger = logging.getLogger('PyPe9')


class UnitConverter(object):

    _CACHE_FILENAME = '.unit_conversion_cache.pkl'

    def __init__(self):
        # Get cache path from file path of subclass
        self._cache_path = os.path.join(
            os.path.dirname(sys.modules[self.__module__].__file__),
            self._CACHE_FILENAME)
        try:
            with open(self._cache_path) as f:
                self._cache = pkl.load(f)
        except IOError:
            logger.warning("Could not load unit conversion cache from file "
                           "'{}'".format(self._cache_path))
            self._cache = {}

    def __del__(self):
        try:
            with open(self._cache_path, 'w') as f:
                pkl.dump(self._cache, f)
        except IOError:
            logger.warning("Could not save unit conversion cache to file '{}'"
                           .format(self._cache_path))

    def project_onto(self, unit, basis_units):
        A = array([list(b.dimension) for b in basis_units]).T
        b = array(list(unit.dimension))
        return solve(A, b)

    def scale(self, unit):
        """
        Projects a given unit onto a list of units that span the space of
        dimensions present in the unit to project.

        Returns a list of the basis units with their associated powers and the
        scale of the presented units.
        """
        try:
            # Check to see if unit dimension is in basis
            base_unit = next(u for u in self.basis
                             if u.dimension == unit.dimension)
            compound = [(base_unit, 1)]
            exponent = unit.power - base_unit.power
        except StopIteration:
            try:
                # Check cache for precalculated compounds
                min_x = self._cache[tuple(unit.dimension)]
            except KeyError:
                # Get projection of unit dimension onto basis units
                xs = self.project_onto(unit, self.basis)
                min_x = xs[argmin(sum(abs(x)) for x in xs)]
                self._cache[tuple(unit.dimension)] = min_x
            # Get list of compound units with the powers
            compound = [(u, p) for u, p in zip(self.basis, min_x) if p]
            # Calculate the appropriate scale for the new compound quantity
            exponent = -min_x.dot([b.power for b in self.basis])
        return exponent, compound

    @classmethod
    def to_quantity(cls, value, units):
        dim = units.dimension
        return value * 10 ** units.power * (
            pq.s ** dim.t * pq.kg ** dim.m * pq.m ** dim.l * pq.mole ** dim.n *
            pq.K ** dim.k * pq.cd ** dim.j * pq.A ** dim.i)

    @classmethod
    def scale_to(cls, units, target_units):
        assert units.dimension == target_units.dimension
        return units.power - target_units.power
