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
from ninemlp.nest.build import build_cellclass

loaded_cell_types = {}

_RELATIVE_NEST_BUILD_DIR = os.path.join('build', 'nest')

class NCMLCell(BaseNCMLCell, pyNN.nest.NativeCellType):

    def __init__(self, parameters):
        BaseNCMLCell.__init__(self)
        pyNN.nest.NativeCellType.__init__(self, parameters)

    def memb_init(self):
        # Initialisation of member states goes here        
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

def load_cell_type(cell_typename, ncml_path, build_mode=DEFAULT_BUILD_MODE, silent=False):
    if loaded_cell_types.has_key(cell_typename):
        # Select the previously loaded cell type
        cell_type, old_ncml_path = loaded_cell_types[cell_typename]
        # Check to see whether the nineml directories match between the requested and loaded cell types
        if ncml_path != old_ncml_path:
            raise Exception ('Name conflict in NEST modules ''{typename}'' attempted to be loaded \
''{dir}'' but was already loaded from ''{old_dir}'''.format(typename=cell_typename, dir=ncml_path,
                                                                            old_dir=old_ncml_path))
    else:
        # Add module install directory to LD_LIBRARY_PATH
        module_build_dir = os.path.join(os.path.dirname(ncml_path), _RELATIVE_NEST_BUILD_DIR, 
                                                                                    cell_typename)
        install_dir = build_cellclass(cell_typename, ncml_path, module_build_dir, 
                                                                            build_mode=build_mode)
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
        nest.Install(cell_typename)
        dct['ncml_model'] = read_NCML(cell_typename, ncml_path)
        dct['morphml_model'] =read_MorphML(cell_typename, ncml_path)
        # Add the loaded cell type to the list of cell types that have been loaded
        cell_type = NCMLMetaClass(str(cell_typename), (pyNN.models.BaseCellType, NCMLCell),
                                                            {'nest_model' : cell_typename})
        # Added the loaded cell_type to the dictionary of previously loaded cell types
        loaded_cell_types[cell_typename] = (cell_type, ncml_path)
    return cell_type
