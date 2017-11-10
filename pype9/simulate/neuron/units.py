from nineml import units as un
from pype9.simulate.common.units import UnitHandler as BaseUnitHandler


class UnitHandler(BaseUnitHandler):

    basis = [un.ms, un.mV, un.nA, un.mM, un.nF, un.um, un.uS, un.K, un.cd]
    compounds = [un.mA_per_cm2, un.uF_per_cm2, un.S_per_cm2, un.ohm_cm]
    unit_name_map = {un.ms: 'ms', un.mV: 'mV', un.nA: 'nA', un.mM: 'mM',
                     un.nF: 'nF', un.um: 'um', un.uS: 'uS', un.K: 'K',
                     un.cd: 'cd', un.uF_per_cm2: 'uF/cm2',
                     un.S_per_cm2: 'S/cm2'}

    (A, cache, si_lengths) = BaseUnitHandler._init_matrices_and_cache(
        basis, compounds)

    def _units_for_code_gen(self, units):
        return self.compound_to_units_str(
            units, mult_symbol=' ', pow_symbol='', use_parentheses=False)
