from numpy import array
from .diophantine import solve


def project_unit_onto_basis(unit, basis_units):
    """
    Projects a given unit onto a list of units that span the space of
    dimensions present in the unit to project.

    Returns a list of the basis units with their associated powers and the
    scale of the presented units.
    """
    A = array([list(b.dimension) for b in basis_units]).T
    b = array(list(unit.dimension))
    x = solve(A, b)
    scale = 10 ** -x.dot(b.power for b in basis_units)
    return [(u, p) for u, p in zip(basis_units, x) if p], scale
