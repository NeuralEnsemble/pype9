
#try:
#    import unittest2 as unittest
#except ImportError:
#    import unittest
    
if __name__ == '__main__':
     from utils import DummyTestCase as TestCase  # @UnusedImport
else:
     from unittest import TestCase  # @Reimport
from pype9.cells.code_gen.neuron import CodeGenerator
from os import path
from utils import test_data_dir    
    
import btmorph
import nineml
import nineml.abstraction_layer
from pype9.importer.neuron import nmodl
#/home/russell/git/Pype9/pype9/importer/neuron/nmodl.py

import nineml
#from Kinetic_Extension import NMODLImporter
import os
import glob
from nineml.extensions import kinetics
from nineml.extensions.kinetics import KineticsClass, Constraint, KineticState



class TestKinetics(TestCase):
 
    def setUp(self):
        self.code_generator = CodeGenerator()
    #os.chdir('/home/russell/git/modfile')
    
    
    def import_nm_comp(self):
        os.chdir('/home/russell/git/pype9/test/unittests')
        list=glob.glob('*.mod')
        lcomponentcs=[]
        for i in xrange(0,len(list)):
            #print i
            #print list[i]
            comp = nmodl.NMODLImporter(list[i])
            comp.contents
            print type(comp.kinetics)
            
            #print nmodl.NMODLImporter(list[i]).parameters
            compc=nmodl.NMODLImporter.get_component_class(comp, flatten_kinetics=0)
            print compc
            #help(compc)
            lcomponentcs.append(nmodl.NMODLImporter(list[i]))


    
            
test = TestKinetics() #End brackets are very important here, without end paranthesis 
#The class 
test.import_nm_comp()


# if __name__ == '__main__':
#     from utils import DummyTestCase as TestCase  # @UnusedImport
# else:
#     from unittest import TestCase  # @Reimport
# from pype9.cells.code_gen.neuron import CodeGenerator
# from os import path
# from utils import test_data_dir
# 
# print test_data_dir, ' test_data'
# class TestNeuronBuild(TestCase):
# 
#     def setUp(self):
#         self.code_generator = CodeGenerator()
# 
#     def test_neuron_build(self):
#         component_file = path.join(test_data_dir, 'xml', 'Izhikevich.xml')
#         self.code_generator.generate(component_file,
#                                      build_mode='force',
#                                      ode_solver='derivimplicit',
#                                      membrane_voltage='V',
#                                      membrane_capacitance='Cm')
# 
#     def test_kinetics_build(self):
#         component_file = path.join(test_data_dir, 'xml', 'kinetic_mechanism.xml')
#         self.code_generator.generate(component_file,
#                                      build_mode='force',
#                                      ode_solver='derivimplicit')#sparse
# 
# if __name__ == '__main__':
#     t = TestNeuronBuild()
#     t.test_kinetics_build()
    