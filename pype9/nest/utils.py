from nineml import units as un
from pype9.base.utils import BaseDimensionToUnitMapper
import cPickle as pkl  # @UnusedImport
import atexit


class _DimensionToUnitMapper(BaseDimensionToUnitMapper):

    basis = [un.ms, un.mV, un.pA, un.mM, un.uF, un.um, un.uS, un.K, un.cd]


unit_mapper = _DimensionToUnitMapper()
del _DimensionToUnitMapper  # Delete class to ensure only one instance
atexit.register(unit_mapper.save_cache)
