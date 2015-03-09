import os.path
from pype9.importer.neuron.nmodl import NMODLImporter
from utils import test_data_dir
from neuron import h
import pylab as plt
from pype9.cells.code_gen.neuron import CodeGenerator

if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport

test_cn_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..',
                           'cerebellarnuclei')

test_gr_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..',
                           'kbrain', 'external', 'fabios_network')


class TestKinetics(TestCase):

    def setUp(self):
        self.code_generator = CodeGenerator()

    def test_kinetics_roundtrip(self):
        in_path = os.path.join(test_data_dir, 'nmodl', 'Golgi_SK2.mod')
        out_path = os.path.join(os.path.dirname(__file__), '..', 'data',
                                'nmodl', 'imported', 'regenerated')
        importer = NMODLImporter(in_path)
        component = importer.get_component()
        self.code_generator.generate(
            component, name='Golgi_SK2_regenerated', build_dir=os.getcwd(),
            build_mode='force', verbose=True)


class Compare_output_rt(TestCase):
    '''
    compares output from voltage clamp experiment after round trip.
    '''
    #setUp, is an initialisation method inherited from TestCase
    #This initialisation is crucial, and allows you to never have to use global variables.

    def setUp(self):
        self.dt = h.dt = 0.025
        self.tstop = 10000
        self.vinit = -65
        self.soma = h.Section()
        self.vec = {}

    def initialize(self):
        h.finitialize(self.vinit)
        h.fcurrent()

    def integrate(self):
        while h.t< self.tstop:
            h.fadvance()

    def record(self):
        self.vec['soma'] =h.Vector()
        self.vec['t'] =h.Vector()
        self.vec['soma'].record(self.soma(0.5)._ref_v)
        self.vec['t'].record(h._ref_t)
 
    def run(self):
        self.initialize()
        #h.stdinit()
        self.integrate()

    
    def test_vc_output(self):
        #soma.insert('pas')
        #self.soma.insert('Golgi_SK2')
        self.soma.insert('GRC_NA')
        self.soma.insert('Golgi_Ca_HVA')#compile the file Golgi_SK2.mod
        self.soma.insert('Golgi_Ca_LVA')
        #self.soma.insert('Golgi_SK2')#Here insert the Kinetics Mechanism generated
        #From the test class above.
        
        stim = h.SEClamp(self.soma(0.5),delay = 1000,duration = 100,amplitude = 25)
        #stim2 = h.SEClamp(self.soma(0.5),delay = 1200,duration = 100,amplitude = 25)

        # sets current pulse delay =  600 mS
        # sets current pulse duration = 100 mS
        # sets current pulse amplitude = 25 nA

        self.record()
        self.run()
        plt.figure()
        plt.plot(self.vec['t'].to_python(),self.vec['soma'].to_python())
        plt.title('Section inserted Ca_HVA,Ca_LVA, GRC_NA')#'Golgi_SK2'
        plt.xlabel('ms')
        plt.ylabel('mV')
        plt.savefig('bf_9ml_trans.png')
        
    
    def before_conv(self):
         
        nineml_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'nmodl','imported')
        #os.chdir(nineml_dir)
        #os.chdir('/home/russell/git/pype9/test/data/nmodl')
     
    
    def after_conv(self):
        os.system('rm -r x_86')#compile the file Golgi_SK2.mod
        os.system('rm *.nmodl')#compile the file Golgi_SK2.mod
 
     



if __name__ == '__main__':
    co=Compare_output_rt()
    #co.before_conv()
    #co.test_vc_output()
  
    test = TestKinetics()
    test.test_kinetics_roundtrip()
    #os.system('emacs ../data/nmodl/imported/Golgi_SK2Class.xml')
    #os.system('emacs /home/russell/git/pype9/test/unittests/../data/nmodl/imported/Golgi_SK2.xml')

    #test = TestNeuronImporter()
    #test.test_neuron_import()
    print "done"
