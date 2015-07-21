from numpy import array, sum, abs, argmin
from .diophantine import solve


class UnitConverter(object):

    def __init__(self):
        self._cache = {}

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
            min_x = self._cache[tuple(unit.dimension)]
        except KeyError:
            xs = self.project_onto(unit, self.basis)
            min_x = xs[argmin(sum(abs(x)) for x in xs)]
            self._cache[tuple(unit.dimension)] = min_x
        compound = [(u, p) for u, p in zip(self.basis, min_x) if p]
        scale = -min_x.dot([b.power for b in self.basis])
        return scale, compound
