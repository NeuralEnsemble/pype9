from nineml import units as un
from pype9.base.utils import BaseUnitAssigner


class _DimensionToUnitMapper(BaseUnitAssigner):

    basis = [un.ms, un.mV, un.pA, un.mM, un.uF, un.um, un.uS, un.K, un.cd]
