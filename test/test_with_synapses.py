from nineml import MultiDynamics, Document
from nineml.serialization.xml import XMLUnserializer
import ninemlcatalog
from pype9.simulate.common.cells.with_synapses import (
    WithSynapses, ConnectionParameterSet, class_map)

if __name__ == '__main__':
    from pype9.utils.testing import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport


class TestWithSynapses(TestCase):

    def setUp(self):
        # Perform comparison in subprocess
        iaf = ninemlcatalog.load(
            'neuron/LeakyIntegrateAndFire#PyNNLeakyIntegrateAndFire')
        alpha_psr = ninemlcatalog.load(
            'postsynapticresponse/Alpha#PyNNAlpha')
        static = ninemlcatalog.load(
            'plasticity/Static', 'Static')
        iaf_alpha = MultiDynamics(
            name='IafAlpha',
            sub_components={
                'cell': iaf,
                'syn': MultiDynamics(
                    name="IafAlaphSyn",
                    sub_components={'psr': alpha_psr, 'pls': static},
                    port_connections=[
                        ('pls', 'fixed_weight', 'psr', 'q')],
                    port_exposures=[('psr', 'i_synaptic'),
                                    ('psr', 'spike')])},
            port_connections=[
                ('syn', 'i_synaptic__psr', 'cell', 'i_synaptic')],
            port_exposures=[('syn', 'spike__psr', 'spike')])
        self.model = WithSynapses.wrap(
            iaf_alpha,
            connection_parameter_sets=[
                ConnectionParameterSet(
                    'spike', [iaf_alpha.parameter('weight__pls__syn')])])

    def test_clone(self):
        clone = self.model.clone()
        self.assertEqual(self.model, clone,
                         clone.find_mismatch(self.model))

    def test_xml_roundtrip(self):
        doc = Document(self.model)
        xml = doc.serialize(version=2)
        reread = XMLUnserializer(root=xml, class_map=class_map).unserialize()
        self.assertEqual(doc, reread,
                         doc.find_mismatch(reread))
