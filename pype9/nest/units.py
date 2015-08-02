import os.path
from nineml import units as un
from pype9.base.units import UnitHandler as BaseUnitHandler


class UnitHandler(BaseUnitHandler):

    basis = [un.ms, un.mV, un.pA, un.mM, un.uF, un.um, un.uS, un.K, un.cd]
    compounds = []

    unit_name_map = {un.ms: 'ms', un.mV: 'mV', un.pA: 'pA', un.mM: 'mM',
                     un.uF: 'uF', un.um: 'um', un.uS: 'uS', un.K: 'K',
                     un.cd: 'cd'}

    A, cache, si_lengths = BaseUnitHandler._load_basis_matrices_and_cache(
        basis, os.path.dirname(__file__))

    def _compound_units_to_str(self, units):
        """
        Converts a compound unit list into an NMODL representation
        """
        if not units:
            unit_str = 'dimensionless'
        else:
            unit_str = '*'.join(
                '{}{}'.format(self.unit_name_map[u], p if p > 1 else '')
                for u, p in units if p > 0)
            denominator = '*'.join(
                '{}{}'.format(self.unit_name_map[u], -p if p < -1 else '')
                for u, p in units if p < 0)
            if denominator:
                unit_str += '/' + denominator
        return unit_str
