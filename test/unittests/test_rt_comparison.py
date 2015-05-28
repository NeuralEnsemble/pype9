import os.path
from pype9.importer.neuron import NeuronImporter
from pype9.importer.neuron.hoc import HocImporter
from pype9.importer.neuron.nmodl import NMODLImporter
import nineml
from nineml.abstraction import (
    units as un, AnalogSendPort, AnalogReceivePort, Parameter, DynamicsClass,
    Regime, TimeDerivative, Alias, StateVariable)
from utils import test_data_dir


nineml_file = os.path.join(os.path.dirname(__file__), '..', 'data', '9ml',
                           'Golgi_Solinas08.9ml')


if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport

test_cn_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..',
                           'cerebellarnuclei')

test_gr_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..',
                           'kbrain', 'external', 'fabios_network')


class TestHocImporter(TestCase):

    def test_hoc_import(self):
        importer = HocImporter(test_cn_dir,
                               ['DCN_params_axis.hoc', 'DCN_morph.hoc',
                                'DCN_mechs1.hoc'],
                               ['DCNmechs()'])
        print importer.model


class TestNMODLImporter(TestCase):

    naf_class = DynamicsClass(
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
#            if fname.endswith('.mod'):
            if fname.endswith('.mod') and fname == 'Golgi_SK2.mod':
                importer = NMODLImporter(os.path.join(in_path, fname))
                class_fname = out_path + '/' + fname[:-4] + 'Class.xml'
                comp_fname = out_path + '/' + fname[:-4] + '.xml'
                try:
                    componentclass = importer.get_component_class(flatten_kinetics=False)
                    importer.print_members()
                    
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


class TestNeuronImporter(TestCase):

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





        
class Compare_output_rt(TestCase):
    '''
    compares output from voltage clamp experiment after round trip.
    '''
    
    import os
    import neuron as h
    import matplotlib as plt
    h.dt = 0.025
    tstop = 5
    vinit = -65
    

    
 
         

    def initialize(self):
        h.finitialize(vinit)
        h.fcurrent()

    def integrate(self,tstop):
        while h.t< tstop:
            h.fadvance()
    
    
    def record(self):
        vec=h.Vector()
        vec['soma'].record(pre(0.5)._ref_v)
        vec['t'].record(h._ref_t)
 
    def run(self):
        self.initialize(h.vinit)
        #h.stdinit()
        self.integrate(h.tstop)

    
    def test_vc_output(self):
        soma = h.Section()
        soma.insert('pas')#Here insert the Kinetics Mechanism generated
        #From the test class above.
        stim = h.VClamp(h.soma(0.5))
        tstop=1000
        self.record()
        self.run()

    def before_conv(self):
        os.system('nrnivmodl')#compile the file Golgi_SK2.mod
        
    
    def after_conv(self):
        os.system('rm -r x_86')#compile the file Golgi_SK2.mod
        os.system('rm *.nmodl')#compile the file Golgi_SK2.mod
 
        
     #def plot(self):
     #   plt    



if __name__ == '__main__':
    test = TestNMODLImporter()
    test.test_nmodl_import()
    os.system('emacs /home/russell/git/pype9/test/unittests/../data/nmodl/imported/Golgi_SK2Class.xml')
    os.system('emacs /home/russell/git/pype9/test/unittests/../data/nmodl/imported/Golgi_SK2.xml')

    #co=Compare_output_rt
    #co.test_vc_output()
    #test = TestNeuronImporter()
    #test.test_neuron_import()
    print "done"
