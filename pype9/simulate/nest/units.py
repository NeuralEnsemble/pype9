import os.path
from nineml import units as un
from pype9.simulate.common.units import UnitHandler as BaseUnitHandler


class UnitHandler(BaseUnitHandler):

    basis = [un.ms, un.mV, un.pA, un.mM, un.pF, un.um, un.nS, un.K, un.cd]
    compounds = []

    unit_name_map = {un.ms: 'ms', un.mV: 'mV', un.pA: 'pA', un.mM: 'mM',
                     un.pF: 'pF', un.um: 'um', un.nS: 'nS', un.K: 'K',
                     un.cd: 'cd'}

    (A, cache,
     cache_path, si_lengths) = BaseUnitHandler._load_basis_matrices_and_cache(
        basis, compounds, os.path.dirname(__file__))

    def _units_for_code_gen(self, units):
        return self.compound_to_units_str(
            units, mult_symbol='*', pow_symbol='^', use_parentheses=False)
