import os.path
from nineml import units as un
from pype9.base.utils import BaseUnitAssigner


class UnitAssigner(BaseUnitAssigner):

    basis = [un.ms, un.mV, un.nA, un.mM, un.nF, un.um, un.uS, un.K, un.cd]
    compounds = [un.uF_per_cm2, un.S_per_cm2]
    unit_name_map = {un.ms: 'ms', un.mV: 'mV', un.nA: 'nA', un.mM: 'mM',
                     un.nF: 'nF', un.um: 'um', un.uS: 'uS', un.K: 'K',
                     un.cd: 'cd', un.uF_per_cm2: 'uF/cm2',
                     un.S_per_cm2: 'S/cm2'}

    A, cache, si_lengths = BaseUnitAssigner._load_basis_matrices_and_cache(
        basis, os.path.dirname(__file__))

    def _compound_units_to_str(self, units):
        """
        Converts a compound unit list into an NMODL representation
        """
        if not units:
            unit_str = '1'
        else:
            unit_str = ' '.join(
                '{}{}'.format(self.unit_name_map[u], p if p > 1 else '')
                for u, p in units if p > 0)
            denominator = [
                '{}{}'.format(self.unit_name_map[u], -p if p < -1 else '')
                for u, p in units if p < 0]
            if denominator:
                unit_str += '/' + ' '.join(denominator)
        return unit_str
