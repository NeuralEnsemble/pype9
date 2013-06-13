"""

  This package combines the common.ncml with existing pyNN classes

  @file ncml.py
  @author Tom Close

"""

#######################################################################################
#
#    Copyright 2012 Okinawa Institute of Science and Technology (OIST), Okinawa, Japan
#
#######################################################################################

import sys
import os.path
from collections import defaultdict
import nest
import pyNN.nest
import pyNN.standardmodels
from pyNN.parameters import ParameterSpace
from ninemlp.common.ncml import BaseNCMLCell, BaseNCMLMetaClass, read_NCML, read_MorphML, group_varname
from ninemlp import DEFAULT_BUILD_MODE
from ninemlp.nest.build import build_celltype_files

loaded_cell_types = {}

_RELATIVE_NEST_BUILD_DIR = os.path.join('build', 'nest')

class NCMLCell(BaseNCMLCell, pyNN.standardmodels.StandardCellType):

    def __init__(self, **parameters):
        BaseNCMLCell.__init__(self)
        pyNN.standardmodels.StandardCellType.__init__(self, **parameters)

    def memb_init(self):
        # Initialisation of member states goes here
        print "WARNING, membrane initialization function has not been implemented"
        pass
    
    def translate(self, parameters):
        """
        Translate standardized model parameters to simulator-specific parameters. Overrides the
        the method in StandardModelType to provide a simpler translation that avoids the evaluation 
        of the 'dots' in the standard name
        """
        native_parameters = {}
        for name in parameters.keys():
            # A hack before Ivan implements this as a parameter
            if name != 'all_segs.Ra':
                try:
                    native_parameters[self.translations[name]['translated_name']] = parameters[name]
                except KeyError:
                    print "Omitting parameter '{}'".format(name)
        return ParameterSpace(native_parameters, schema=None, shape=parameters.shape)

    def get_receptor_type(self, name):
        return nest.GetDefaults(self.nest_model)["receptor_types"][name]

class NCMLMetaClass(BaseNCMLMetaClass):
    """
    Metaclass for compiling NineMLCellType subclases
    Called by nineml_celltype_from_model
    """
    def __new__(cls, name, bases, dct):
        dct['nest_name'] = {"on_grid": name, "off_grid": name}
        dct['translations'] = cls._construct_translations(dct['ncml_model'], 
                                                          dct["component_translations"])
        cell_type = super(NCMLMetaClass, cls).__new__(cls, name, bases, dct)
        cell_type.model = super(NCMLMetaClass, cls).__new__(cls, name, bases, dct)
        return cell_type

    @classmethod
    def _construct_translations(cls, ncml_model, component_translations):
        comp_groups = defaultdict(list)
        for comp in ncml_model.mechanisms:
            comp_groups[str(comp.id)].append(group_varname(comp.group_id))
        translations = []
        for comp, params in component_translations.iteritems():
            if comp != 'Extracellular':
                for param, native_n_val in params.iteritems():
                    # These are hacks just to get it to work initially, which will be removed once
                    # the neuron version of the cell respects these components at which point they
                    # should be accessed via
                    if comp in ('Geometry', 'Membrane'):
                        if comp == 'Geometry':
                            standard_name = 'soma_group.' + str(param)
                        elif comp == 'Membrane':
                            standard_name = 'all_segs.' + str(param)
                        translations.append((standard_name, native_n_val[0]))
                    else:
                        for seg_group in comp_groups[comp]:
                            standard_name = '{}.{}.{}'.format(seg_group, comp, param)
                            translations.append((standard_name, native_n_val[0]))
        return pyNN.standardmodels.build_translations(*translations)
        


def load_cell_type(celltype_name, ncml_path, morph_id=None, build_mode=DEFAULT_BUILD_MODE, 
                   silent=False, solver_name='cvode'):
    """
    Loads a PyNN cell type for NEST from an XML description, compiling the necessary module files
    
    @param celltype_name [str]: Name of the cell class to extract from the xml file
    @param ncml_path [str]: The location of the NCML XML file
    @param morph_id [str]: Currently unused but kept for consistency with NEURON version of this function
    @param build_mode [str]: Control the automatic building of required modules
    @param silent [bool]: Whether or not to suppress build output
    """
    if loaded_cell_types.has_key(celltype_name):
        # Select the previously loaded cell type
        cell_type, old_ncml_path = loaded_cell_types[celltype_name]
        # Check to see whether the nineml directories match between the requested and loaded cell types
        if ncml_path != old_ncml_path:
            raise Exception ('Name conflict in NEST modules ''{typename}'' attempted to be loaded \
''{dir}'' but was already loaded from ''{old_dir}'''.format(typename=celltype_name, dir=ncml_path,
                                                                            old_dir=old_ncml_path))
    else:
        dct = {}
        install_dir, dct['component_translations'] = build_celltype_files(celltype_name, ncml_path,
                                                                        build_mode=build_mode,
                                                                        method=solver_name)
        lib_dir = os.path.join(install_dir, 'lib', 'nest')
        if sys.platform.startswith('linux') or \
                                    sys.platform in ['os2', 'os2emx', 'cygwin', 'atheos', 'ricos']:
            lib_path_key = 'LD_LIBRARY_PATH'
        elif sys.platform == 'darwin':
            lib_path_key = 'DLYD_LIBRARY_PATH'
        elif sys.platform == 'win32':
            lib_path_key = 'PATH'
        if os.environ.has_key(lib_path_key):
            os.environ[lib_path_key] += os.pathsep + lib_dir
        else:
            os.environ[lib_path_key] = lib_dir
        # Add module install directory to NEST path
        nest.sli_run('({}) addpath'.format(os.path.join(install_dir, 'share', 'nest'))) 
        # Install nest module
        nest.Install(celltype_name + 'Loader')
        dct['ncml_model'] = read_NCML(celltype_name, ncml_path)
        dct['morphml_model'] = read_MorphML(celltype_name, ncml_path)
        dct['nest_model'] = celltype_name
        # Add the loaded cell type to the list of cell types that have been loaded
        cell_type = NCMLMetaClass(str(celltype_name), (NCMLCell,), dct)
        # Added the loaded cell_type to the dictionary of previously loaded cell types
        loaded_cell_types[celltype_name] = (cell_type, ncml_path)
    return cell_type
