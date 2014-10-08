import tempfile
import os.path
from lxml import etree
from nineline.importer.neuron import NeuronImporter
from nineline.importer.neuron.hoc import HocImporter
from nineline.importer.neuron.nmodl import NMODLImporter

if __name__ == '__main__':

    class unittest(object):

        class TestCase(object):

            def __init__(self):
                try:
                    self.setUp()
                except AttributeError:
                    pass

            def assertEqual(self, first, second):
                print 'are{} equal'.format(' not' if first != second else '')
else:
    try:
        import unittest2 as unittest
    except ImportError:
        import unittest


class TestHocImporter(unittest.TestCase):

    def test_hoc_import(self):
        importer = HocImporter('/home/tclose/git/cerebellarnuclei/',
                               ['DCN_params_axis.hoc', 'DCN_morph.hoc',
                                'DCN_mechs1.hoc'],
                               ['DCNmechs()'])
        print importer.model


class TestNMODLImporter(unittest.TestCase):

    ref_xml = (
        """<?xml version='1.0' encoding='UTF-8'?>
        <NineML xmlns="http://nineml.org/9ML/0.3">
          <ComponentClass name="NaF">
            <AnalogPort mode="send" dimension="dimensionless" name="m"/>
            <AnalogPort mode="send" dimension="dimensionless" name="h"/>
            <AnalogPort mode="recv" dimension="voltage" name="ena"/>
            <AnalogPort mode="send" dimension="membrane_current" name="ina"/>
            <AnalogPort mode="recv" dimension="voltage" name="v"/>
            <Parameter dimension="dimensionless" name="qdeltat"/>
            <Parameter dimension="membrane_conductance" name="gbar"/>
            <Dynamics>
              <Regime name="states">
                <TimeDerivative variable="m">
                  <MathInline>(minf_v - m)/taum_v</MathInline>
                </TimeDerivative>
                <TimeDerivative variable="h">
                  <MathInline>(hinf_v - h)/tauh_v</MathInline>
                </TimeDerivative>
              </Regime>
              <Alias name="tauh_v__tmp">
                <MathInline>
                    16.67 / (exp((v - 8.3) / -29) + exp((v + 66) / 9)) + 0.2
                </MathInline>
              </Alias>
              <Alias name="taum_v">
                <MathInline>taum_v__tmp / qdeltat</MathInline>
              </Alias>
              <Alias name="tauh_v">
                <MathInline>tauh_v__tmp / qdeltat</MathInline>
              </Alias>
              <Alias name="minf_v">
                <MathInline>1 / (1 + exp((v + 45) / -7.3))</MathInline>
              </Alias>
              <Alias name="hinf_v">
                <MathInline>1 / (1 + exp((v + 42) / 5.9))</MathInline>
              </Alias>
              <Alias name="ina">
                <MathInline>gbar * m*m*m * h * (v - ena)</MathInline>
              </Alias>
              <Alias name="taum_v__tmp">
                <MathInline>
                    5.83 / (exp((v - (6.4)) / -9) + exp((v + 97) / 17)) + 0.025
                </MathInline>
              </Alias>
              <StateVariable dimension="dimensionless" name="h"/>
              <StateVariable dimension="dimensionless" name="m"/>
            </Dynamics>
          </ComponentClass>
        </NineML>""")

    def test_nmodl_import(self):
        importer = NMODLImporter('/home/tclose/git/kbrain/external/'
                                 'fabios_network/Golgi_hcn2.mod')
        component, componentclass = importer.get_component_class('/tmp')
#         imported_tree = etree.parse(fname)
#         reference_tree = etree.fromstring(self.ref_xml)
#         self.assertEqual(imported_tree, reference_tree)


class TestNeuronImporter(unittest.TestCase):

    def test_neuron_import(self):
#         importer = NeuronImporter('/home/tclose/git/cerebellarnuclei/',
#                                    ['DCN_params_axis.hoc', 'DCN_morph.hoc',
#                                     'DCN_mechs1.hoc'],
#                                    ['DCNmechs()'])
#         importer.write_ion_current_files('/home/tclose/git/cerebellarnuclei/'
#                                          '9ml/ion_channels')
#         importer = NeuronImporter('/home/tclose/git/purkinje/model/'
#                                   'Haroon_active_reduced_model',
#                                    ['for_import.py'])
#         importer.write_ion_current_files('/home/tclose/git/purkinje/model/'
#                                          'Haroon_active_reduced_model/9ml')
        importer = NeuronImporter('/home/tclose/git/kbrain/external/'
                                  'fabios_network',
                                   ['load_sergios_golgi.hoc'])
        importer.write_ion_current_files(class_dir=('/home/tclose/git/kbrain/'
                                                    'external/fabios_network/'
                                                    '9ml/classes'),
                                         comp_dir=('/home/tclose/git/kbrain/'
                                                   'external/fabios_network/'
                                                   '9ml/components'))
if __name__ == '__main__':
#     test = TestNMODLImporter()
#     test.test_nmodl_import()
    test = TestNeuronImporter()
    test.test_neuron_import()
    print "done"
