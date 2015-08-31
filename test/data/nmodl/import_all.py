"""
Imports all mod files in directory to 9ML
"""
import os.path
from pype9.importer.neuron import NMODLImporter
import nineml

in_path = os.path.dirname(__file__)
out_path = os.path.join(in_path, 'imported')

for fname in os.listdir(in_path):
    if fname.endswith('.mod'):
        importer = NMODLImporter(os.path.join(in_path, fname))
        class_fname = out_path + '/' + fname[:-4] + 'Class.xml'
        comp_fname = out_path + '/' + fname[:-4] + '.xml'
        component_class = importer.get_component_class()
        nineml.write(component_class, class_fname)
        component = importer.get_component(class_fname)
        nineml.write(component, comp_fname)
        print "Converted '{}' to '{}'".format(fname, comp_fname)
