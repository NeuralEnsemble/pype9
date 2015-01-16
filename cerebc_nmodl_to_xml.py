#!/bin/python
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
#import os
#os.path.join(in_path, '/test/unittests')
os.chdir(os.getcwd()+'/test/unittests')
print os.getcwd()
execfile('test_neuron_build.py')
execfile('test_neuron_import.py')
