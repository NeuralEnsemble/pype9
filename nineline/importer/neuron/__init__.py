import os
import re
from nineml.exceptions import NineMLMathParseError
from .hoc import HocImporter
from .nmodl import NMODLImporter


class NeuronImporter(object):

    known_components = ['IClamp', 'Ra', 'cm']

    def __init__(self, import_dir, hoc_files=['main.hoc'], hoc_cmds=[]):
        self.import_dir = import_dir
        self.hoc_importer = HocImporter(import_dir, hoc_files=hoc_files,
                                        hoc_cmds=hoc_cmds)
        self._scan_dir_for_mod_files()
        self._create_nmodl_importers()

    def write_ion_current_files(self, output_dir):
        for imptr in self.nmodl_importers.itervalues():
            compclass = imptr.get_component()
            compclass.write(os.path.join(output_dir, compclass.name + '.xml'))

    def _scan_dir_for_mod_files(self):
        self.available_mods = {}
        for fname in os.listdir(self.import_dir):
            if fname.endswith('.mod'):
                with open(os.path.join(self.import_dir, fname)) as f:
                    contents = f.read()
                match = re.search(r'SUFFIX (\w+)', contents)
                if not match:
                    match = re.search(r'POINT_PROCESS (\w+)', contents)
                    if not match:
                        match = re.search(r'ARTIFICIAL_CELL (\w+)', contents)
                        if not match:
                            raise Exception("Could not determine name from "
                                            "'{}' mod file (missing 'SUFFIX', "
                                            "'POINT_PROCESS or ARTIFICIAL_CELL"
                                            "' declaration)")
                self.available_mods[match.group(1)] = fname

    def _create_nmodl_importers(self):
        self.nmodl_importers = {}
        for comp in self.hoc_importer.model.components.itervalues():
            class_name = comp.class_name
            if not class_name.endswith('_ion'):
                try:
                    nmodl_file = os.path.join(self.import_dir,
                                              self.available_mods[class_name])
                except KeyError:
                    if class_name not in self.known_components:
                        print ("Could not find '{}' nmodl file"
                               .format(class_name))
                    continue
#                 try:
                self.nmodl_importers[comp.name] = NMODLImporter(nmodl_file)
#                 except NineMLMathParseError as e:
#                     print ("Could not parse '{}' mod file because of "
#                            "'{}' maths expression".format(nmodl_file, e))
