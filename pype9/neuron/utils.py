from nineml import units as un
from pype9.base.utils import (
    BaseDimensionToUnitMapper, BaseExpressionUnitScaler)
import cPickle as pkl  # @UnusedImport
import atexit


class _DimensionToUnitMapper(BaseDimensionToUnitMapper):

    basis = [un.ms, un.mV, un.nA, un.mM, un.nF, un.um, un.uS, un.K, un.cd]

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


unit_mapper = _DimensionToUnitMapper()
del _DimensionToUnitMapper  # To ensure only one version of the mapper exists
atexit.register(unit_mapper.save_cache)


class ExpressionUnitScaler(BaseExpressionUnitScaler):

    _mapper = unit_mapper
