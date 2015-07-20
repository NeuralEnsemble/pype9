from numpy import array, sum, abs, argmin
from .diophantine import solve


class UnitConverter(object):

    def project_onto(self, unit, basis_units):
        A = array([list(b.dimension) for b in basis_units]).T
        b = array(list(unit.dimension))
        solve(A, b)

    def scale(self, unit, basis_units):
        """
        Projects a given unit onto a list of units that span the space of
        dimensions present in the unit to project.

        Returns a list of the basis units with their associated powers and the
        scale of the presented units.
        """
        xs = self.get_projections(unit, basis_units)
        min_x = xs[argmin(sum(abs(x)) for x in xs)]
        scale = 10 ** -min_x.dot([b.power for b in basis_units])
        return scale, [(u, p) for u, p in zip(basis_units, min_x) if p]
