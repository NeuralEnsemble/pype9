from nineml import units as un
from pype9.common.utils import BaseDimensionToUnitMapper


class DimensionToUnitMapper(BaseDimensionToUnitMapper):

    basis = [un.ms, un.mV, un.nA, un.mM, un.nF, un.um, un.uS, un.K, un.cd]

    def scale_str(self, unit):
        exponent, _ = self.convert(unit)
        if exponent != 0:
            scale_str = '* 1e{} '.format(exponent)
        else:
            scale_str = ''
        return scale_str

    def unit_str(self, unit):
        _, compound = self.convert(unit)
        if unit == un.dimensionless:
            unit_str = '1'
        else:
            unit_str = (' '.join('{}{}'.format(u.name, p if p > 1 else '')
                                 for u, p in compound if p > 0) +
                        '/' +
                        ' '.join('{}{}'.format(u.name, -p if p < -1 else '')
                                 for u, p in compound if p < 0))
        return unit_str


unit_converter = DimensionToUnitMapper()

if __name__ == '__main__':
    conv = DimensionToUnitMapper()
    exponent, compound = conv.convert(un.A * un.uF / un.um ** 2)
    print conv.compound_str(compound)
