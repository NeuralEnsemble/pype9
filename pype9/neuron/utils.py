from nineml import units as un
import pype9.common.utils


class UnitConverter(pype9.common.utils.UnitConverter):

    basis = [un.ms, un.mV, un.mA / un.cm ** 2, un.nA, un.mM,
             un.uF / un.cm ** 2, un.um, un.S / un.cm ** 2, un.uS,
             un.ohm * un.cm, un.ohm, un.degC, un.cd]
