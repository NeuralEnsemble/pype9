from nineml import units as un
from pype9.common.utils import BaseDimensionToUnitMapper


class DimensionToUnitMapper(BaseDimensionToUnitMapper):

    basis = [un.ms, un.mV, un.pA, un.mM, un.uF, un.um, un.uS, un.K, un.cd]


unit_converter = DimensionToUnitMapper()
