import os
import re
from nineml.exceptions import NineMLRuntimeError
from .hoc import HocImporter
from .nmodl import NMODLImporter
from nineml.exceptions import NineMLDimensionError


class NeuronImporter(object):

    known_components = ['IClamp', 'Ra', 'cm', 'Exp2Syn']

    def __init__(self, import_dir, model_files=['main.hoc'], hoc_cmds=[]):
        self.import_dir = import_dir
        self.hoc_importer = HocImporter(import_dir, model_files=model_files,
                                        hoc_cmds=hoc_cmds)
        self._scan_dir_for_mod_files()
        self._create_nmodl_importers()

    def write_ion_current_files(self, class_dir, comp_dir):
        class_dir = os.path.abspath(class_dir)
        comp_dir = os.path.abspath(comp_dir)
        class_paths = {}
        for component in self.hoc_importer.model.components.itervalues():
            class_name = component.class_name
            if (class_name in self.known_components or
                    class_name.endswith('_ion')):
                continue
            nmodl_imptr = self.nmodl_importers[class_name]
            if class_name not in class_paths:
                try:
                    try:
                        class9ml = nmodl_imptr.get_component_class()
                    except NineMLDimensionError:
                        class9ml = nmodl_imptr.get_component_class(
                            validate_dimensions=False)
                        print ("Warning '{}' was imported despite failing "
                               "dimensionality checks"
                               .format(nmodl_imptr.component_name))
                    class_path = os.path.join(
                        class_dir, nmodl_imptr.component_name + '.xml')
                    class9ml.write(class_path)
                    class_paths[class_name] = class_path
                except NineMLRuntimeError as e:
                    nmodl_imptr.print_members()
                    print ("\nCould not write '{}' component because of:\n{}"
                           .format(nmodl_imptr.component_name, e))
                    continue
            comp9ml = nmodl_imptr.get_component(
                class_paths[class_name], hoc_properties=component.parameters,
                name=component.name)
            comp9ml.write(os.path.join(comp_dir, component.name + '.xml'))

    def write_model(self, output_path, comp_dir):
        self.hoc_importer.model.to_9ml(comp_dir).write(output_path)

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
        to_import = set()
        for comp in self.hoc_importer.model.components.itervalues():
            class_name = comp.class_name
            if not class_name.endswith('_ion'):
                if class_name in self.available_mods:
                    to_import.add(class_name)
                elif class_name not in self.known_components:
                    print "Could not find '{}' nmodl file".format(class_name)
        for class_name in to_import:
            nmodl_file = os.path.join(self.import_dir,
                                      self.available_mods[class_name])
            try:
                self.nmodl_importers[class_name] = NMODLImporter(nmodl_file)
            except Exception as e:
                print ("Could not parse '{}' mod file because of {} error: "
                       "'{}'".format(nmodl_file, e.__class__.__name__, e))
