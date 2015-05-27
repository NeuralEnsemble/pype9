import os.path
from pype9.importer.neuron import NMODLImporter
from pype9.exceptions import Pype9ImportError

pynn_nmodl_dir = os.path.join(os.environ['HOME'], 'git', 'pynn', 'src',
                              'neuron', 'nmodl')

fnames = os.listdir(pynn_nmodl_dir)
# fnames = ['alphaisyn.mod']  # debugging

for fname in fnames:
    if fname.endswith('.mod'):
        try:
            importer = NMODLImporter(os.path.join(pynn_nmodl_dir, fname))
            class_fname = os.path.join(os.getcwd(), fname[:-4] + 'Class.xml')
            importer.get_component_class().write(class_fname)
            importer.get_component(class_fname).write(
                os.path.join(os.getcwd(), fname[:-4] + '.xml'))
            print "Imported '{}".format(fname)
        except Pype9ImportError, e:
            print "Failed to import '{}': {}".format(fname, e)
