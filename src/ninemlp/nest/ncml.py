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
import nest
import pyNN.nest
from ninemlp.common.ncml import BaseNCMLCell, BaseNCMLMetaClass, read_NCML, read_MorphML
from ninemlp import DEFAULT_BUILD_MODE
from ninemlp.nest.build import build_celltype_files

loaded_cell_types = {}

_RELATIVE_NEST_BUILD_DIR = os.path.join('build', 'nest')

class NCMLCell(BaseNCMLCell, pyNN.nest.NativeCellType):

    def __init__(self, parameters):
        BaseNCMLCell.__init__(self)
        pyNN.nest.NativeCellType.__init__(self, parameters)

    def memb_init(self):
        # Initialisation of member states goes here
        print "WARNING, membrane initialization function has not been implemented"
        pass

class NCMLMetaClass(BaseNCMLMetaClass):
    """
    Metaclass for compileing NineMLCellType subclasses
    Called by nineml_celltype_from_model
    """
    def __new__(cls, name, bases, dct):
        #The __init__ function for the created class  
        def cellclass__init__(self, parameters={}):
            pyNN.models.BaseCellType.__init__(self, parameters)
            NCMLCell.__init__(self, **parameters)
        def modelclass__init__(self, **parameters):
            cellclass__init__(self, parameters)
        dct['__init__'] = cellclass__init__
        cell_type = super(NCMLMetaClass, cls).__new__(cls, name, bases, dct)
        dct['__init__'] = modelclass__init__
        cell_type.model = super(NCMLMetaClass, cls).__new__(cls, name, bases, dct)
        return cell_type

def load_cell_type(celltype_name, ncml_path, morph_id=None, build_mode=DEFAULT_BUILD_MODE, 
                   silent=False, nest_method='gsl'):
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
        install_dir, dct['component_parameters'] = build_celltype_files(celltype_name, ncml_path,
                                                                        build_mode=build_mode,
                                                                        method=nest_method)
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
        nest.sli_run('({}) addpath'.format(install_dir))
        # Install nest module
        nest.Install(celltype_name)
        dct['ncml_model'] = read_NCML(celltype_name, ncml_path)
        dct['morphml_model'] = read_MorphML(celltype_name, ncml_path)
        dct['nest_model'] = celltype_name
        # Add the loaded cell type to the list of cell types that have been loaded
        cell_type = NCMLMetaClass(str(celltype_name), (pyNN.models.BaseCellType, NCMLCell), dct)
        # Added the loaded cell_type to the dictionary of previously loaded cell types
        loaded_cell_types[celltype_name] = (cell_type, ncml_path)
    return cell_type
