from lxml import etree
import os.path
from lxml import etree
from pype9.importer.neuron import NeuronImporter
from pype9.importer.neuron.hoc import HocImporter
from pype9.importer.neuron.nmodl import NMODLImporter

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

test_cn_dir = os.path.join(os.path.dirname(__file__) , '..', '..', '..',
                        'cerebellarnuclei')

test_gr_dir = os.path.join(os.path.dirname(__file__) , '..', '..', '..',
                        'kbrain', 'external', 'fabios_network')

class TestHocImporter(unittest.TestCase):

    def test_hoc_import(self):
        importer = HocImporter(test_cn_dir,
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
        in_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'nmodl')
        out_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'nmodl',
                                'imported')
        for fname in os.listdir(in_path):
            if fname.endswith('.mod'):
                importer = NMODLImporter(os.path.join(in_path, fname))
                class_fname = out_path + '/' + fname[:-4] + 'Class.xml'
                comp_fname = out_path + '/' + fname[:-4] + '.xml'
                componentclass = importer.get_component_class()
                componentclass.write(class_fname)
                component = importer.get_component(class_fname)
                component.write(comp_fname)
                print "Converted '{}' to '{}'".format(fname, comp_fname)
#         reference_tree = etree.fromstring(self.ref_xml)
#         self.assertEqual(etree.tostring(imported_tree),
#                          etree.tostring(reference_tree))


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
        importer = NeuronImporter(test_gr_dir,
                                   ['load_sergios_golgi.hoc'])
        importer.write_ion_current_files(class_dir=(os.path.join(test_gr_dir,
                                                    '9ml/classes')),
                                         comp_dir=(os.path.join(test_gr_dir,
                                                   '9ml/components')))
if __name__ == '__main__':
    test = TestNMODLImporter()
    test.test_nmodl_import()
#     test = TestNeuronImporter()
#     test.test_neuron_import()
    print "done"
