import os.path
from nineml import units as un
from pype9.base.utils import BaseUnitAssigner


class UnitAssigner(BaseUnitAssigner):

    basis = [un.ms, un.mV, un.nA, un.mM, un.nF, un.um, un.uS, un.K, un.cd]

    A, cache, si_lengths = BaseUnitAssigner._load_basis_matrices_and_cache(
        basis, os.path.dirname(__file__))

    def scale_str(self, unit):
        exponent, _ = self.map_to_units(unit)
        if exponent != 0:
            scale_str = '* 1e{} '.format(exponent)
        else:
            scale_str = ''
        return scale_str

    def unit_str(self, unit):
        _, compound = self.map_to_units(unit)
        if unit == un.dimensionless:
            unit_str = '1'
        else:
            unit_str = (' '.join('{}{}'.format(u.name, p if p > 1 else '')
                                 for u, p in compound if p > 0) +
                        '/' +
                        ' '.join('{}{}'.format(u.name, -p if p < -1 else '')
                                 for u, p in compound if p < 0))
        return unit_str
