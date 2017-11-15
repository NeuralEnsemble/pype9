from __future__ import division
from __future__ import print_function
import ninemlcatalog
from nineml.abstraction import Parameter, TimeDerivative, StateVariable
import nineml.units as un
from pype9.simulate.nest import CellMetaClass
from pype9.simulate.common.cells.with_synapses import WithSynapses
from pype9.exceptions import Pype9BuildMismatchError
from unittest import TestCase  # @Reimport
import pype9.utils.logging.handlers.sysout  # @UnusedImport


class TestSeeding(TestCase):

    def test_build_name_conflict(self):
        izhi = ninemlcatalog.load('neuron/Izhikevich.xml#Izhikevich')
        izhi2 = izhi.clone()

        izhi2.add(StateVariable('Z', dimension=un.dimensionless))
        izhi2.regime('subthreshold_regime').add(TimeDerivative('Z', '1 / zp'))
        izhi2.add(Parameter('zp', dimension=un.time))

        izhi_wrap = WithSynapses.wrap(izhi)
        izhi2_wrap = WithSynapses.wrap(izhi2)

        CellMetaClass(izhi_wrap)
        self.assertRaises(
            Pype9BuildMismatchError,
            CellMetaClass,
            izhi2_wrap)
