from nineml import units as un
import pype9.common.utils


class UnitConverter(pype9.common.utils.UnitConverter):

    basis = [un.ms, un.mV, un.nA, un.mM, un.uF, un.um, un.uS, un.ohm,
             un.K, un.cd]
