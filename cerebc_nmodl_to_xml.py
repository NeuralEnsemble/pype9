#!/usr/bin/env python
import btmorph
import nineml
import pype9
import pype9.cells
import pype9.hpc
import pype9.importer
import pype9.arguments
import pype9.cells.build
import pype9.cells.code_gen
#import pype9.test
import os
os.chdir(os.getcwd()+'/test/unittests/')


#execfile('test_neuron_build.py')
#test neuron build means building neuron code from XML.
execfile('test_neuron_import.py')
