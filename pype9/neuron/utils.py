import os.path
from nineml import units as un
from pype9.base.utils import BaseUnitAssigner


class UnitAssigner(BaseUnitAssigner):

    basis = [un.ms, un.mV, un.nA, un.mM, un.nF, un.um, un.uS, un.K, un.cd]
    compounds = [un.uF_per_cm2, un.S_per_cm2]

    A, cache, si_lengths = BaseUnitAssigner._load_basis_matrices_and_cache(
        basis, os.path.dirname(__file__))

    def unit_to_str(self, unit):
        """
        Converts a compound unit list into an NMODL representation
        """
        _, compound = self.dimension_to_units(unit.dimension)
        if unit == un.dimensionless:
            unit_str = '1'
        else:
            unit_str = (' '.join('{}{}'.format(u.name, p if p > 1 else '')
                                 for u, p in compound if p > 0) +
                        '/' +
                        ' '.join('{}{}'.format(u.name, -p if p < -1 else '')
                                 for u, p in compound if p < 0))
        return unit_str

    def scale_str(self, unit):
        """
        Calculates the correct scaling that should be applied to quantity of
        the given unit to match its projection onto the basis units.
        """
        exponent, _ = self.dimension_to_units(unit.dimension)
        if exponent != 0:
            scale_str = '* 1e{} '.format(exponent)
        else:
            scale_str = ''
        return scale_str
