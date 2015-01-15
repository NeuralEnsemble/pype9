#!/usr/bin/env
import btmorph
import nineml
import nineline
import nineline.cells
import nineline.hpc
import nineline.importer
import nineline.arguments
import nineline.cells.build
import nineline.cells.code_gen
#import nineline.test
import os
os.chdir(os.getcwd()+'/test/unittests/')


#execfile('test_neuron_build.py')
#test neuron build means building neuron code from XML.
execfile('test_neuron_import.py')
