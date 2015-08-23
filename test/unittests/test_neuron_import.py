"""
Test the import of NMODL and Hoc models into 9ML

NB: Currently disabled until suitable test data is found and the imported files
    are compared with simulated output.
"""
import os.path
from pype9.neuron.importer import NeuronImporter, HocImporter, NMODLImporter
import nineml
from nineml import units as un
import pyNN
from nineml.abstraction import (
    AnalogSendPort, AnalogReceivePort, Parameter, Dynamics,
    TimeDerivative, Alias, StateVariable, Regime)
from utils import test_data_dir
from pype9.exceptions import Pype9ImportError
if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport


test_cn_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..',
                           'cerebellarnuclei')

test_gr_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..',
                           'kbrain', 'external', 'fabios_network')


pynn_nmodl_dir = os.path.join(os.path.dirname(pyNN.__file__), 'neuron',
                              'nmodl')


class TestHocImporter(object):

    def test_hoc_import(self):
        importer = HocImporter(test_cn_dir,
                               ['DCN_params_axis.hoc', 'DCN_morph.hoc',
                                'DCN_mechs1.hoc'],
                               ['DCNmechs()'])
        print importer.model


class TestNMODLImporter(object):

    naf_class = Dynamics(
        name="NaF",
        parameters=[Parameter("qdeltat", un.dimensionless),
                    Parameter("gbar", un.conductance)],
        analog_ports=[
            AnalogSendPort("m", un.dimensionless),
            AnalogSendPort("h", un.dimensionless),
            AnalogReceivePort("ena", un.voltage),
            AnalogSendPort("ina", un.current),
            AnalogReceivePort("v", un.voltage)],
        regimes=[Regime(name="default",
                        time_derivatives=[
                            TimeDerivative('m', '(minf_v - m)/taum_v'),
                            TimeDerivative('h', '(hinf_v - h)/tauh_v')])],
        aliases=[Alias('tauh_v__tmp',
                       '16.67 / '
                       '(exp((v - 8.3) / -29) + exp((v + 66) / 9)) + 0.2'),
                 Alias('taum_v', 'taum_v__tmp / qdeltat'),
                 Alias('tauh_v', 'taum_v__tmp / qdeltat'),
                 Alias('minf_v', '1 / (1 + exp((v + 45) / -7.3))'),
                 Alias('hinf_v', '1 / (1 + exp((v + 42) / 5.9))'),
                 Alias('ina', 'gbar * m*m*m * h * (v - ena)'),
                 Alias('taum_v__tmp',
                       '5.83 / (exp((v - (6.4)) / -9) + '
                       'exp((v + 97) / 17)) + 0.025')],
        state_variables=[StateVariable('m', un.dimensionless),
                          StateVariable('h', un.dimensionless)])

    def test_nmodl_import(self):
        in_path = os.path.join(test_data_dir, 'nmodl')
        out_path = os.path.join(os.path.dirname(__file__), '..', 'data',
                                'nmodl', 'imported')
        for fname in os.listdir(in_path):
            if fname.endswith('.mod'):
                importer = NMODLImporter(os.path.join(in_path, fname))
                class_fname = out_path + '/' + fname[:-4] + 'Class.xml'
                comp_fname = out_path + '/' + fname[:-4] + '.xml'
                try:
                    componentclass = importer.get_component_class()
                except:
                    print "Could not import '{}' mod file".format(fname)
                    raise
                nineml.write(componentclass, class_fname)
                component = importer.get_component(class_fname)
                nineml.write(component, comp_fname)
                print "Converted '{}' to '{}'".format(fname, comp_fname)
#         reference_tree = etree.fromstring(self.ref_xml)
#         self.assertEqual(etree.tostring(imported_tree),
#                          etree.tostring(reference_tree))


class TestNeuronImporter(object):

    def test_neuron_import(self):
        importer = NeuronImporter('/home/tclose/git/cerebellarnuclei/',
                                   ['DCN_params_axis.hoc', 'DCN_morph.hoc',
                                    'DCN_mechs1.hoc'],
                                   ['DCNmechs()'])
        importer.write_ion_current_files('/home/tclose/git/cerebellarnuclei/'
                                         '9ml/ion_channels')
        importer = NeuronImporter('/home/tclose/git/purkinje/model/'
                                  'Haroon_active_reduced_model',
                                   ['for_import.py'])
        importer.write_ion_current_files('/home/tclose/git/purkinje/model/'
                                         'Haroon_active_reduced_model/9ml')
        importer = NeuronImporter(test_gr_dir,
                                   ['load_sergios_golgi.hoc'])
        importer.write_ion_current_files(class_dir=(os.path.join(test_gr_dir,
                                                    '9ml/classes')),
                                         comp_dir=(os.path.join(test_gr_dir,
                                                   '9ml/components')))

if __name__ == '__main__':
    test = TestNMODLImporter()
    test.test_nmodl_import()
    test = TestNeuronImporter()
    test.test_neuron_import()
    fnames = os.listdir(pynn_nmodl_dir)

    for fname in fnames:
        if fname.endswith('.mod'):
            try:
                importer = NMODLImporter(os.path.join(pynn_nmodl_dir, fname))
                class_fname = os.path.join(os.getcwd(), fname[:-4] +
                                           'Class.xml')
                importer.get_component_class().write(class_fname)
                importer.get_component(class_fname).write(
                    os.path.join(os.getcwd(), fname[:-4] + '.xml'))
                print "Imported '{}".format(fname)
            except Pype9ImportError, e:
                print "Failed to import '{}': {}".format(fname, e)

    print "done"
