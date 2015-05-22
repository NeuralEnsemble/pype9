import os.path
from pype9.importer.neuron import NMODLImporter

pynn_nmodl_dir = os.path.join(os.environ['HOME'], 'git', 'pynn', 'src',
                              'neuron', 'nmodl')

for fname in os.listdir(pynn_nmodl_dir):
    print "Importing '{}".format(fname)
    importer = NMODLImporter(os.path.join(pynn_nmodl_dir, fname))
    class_fname = os.path.join(os.getcwd(), fname[:-4] + 'Class.xml')
    importer.get_component_class().write(class_fname)
    importer.get_component(class_fname).write(
        os.path.join(os.getcwd(), fname[:-4] + '.xml'))
