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

from __future__ import absolute_import
import sys
import os.path
import nest
from .build.nest import build_celltype_files
import nineline.cells

basic_nineml_translations = {'Voltage': 'V_m', 'Diameter': 'diam', 'Length':'L'}

class NineCell(nineline.cells.NineCell):
    pass

class NineCellMetaClass(nineline.cells.NineCellMetaClass):
    
    loaded_celltypes = {}
    
    def __new__(cls, nineml_model, celltype_name, morph_id=None, build_mode='lazy', silent=False, #@UnusedVariable 
                solver_name='cvode'):
        """
        Loads a PyNN cell type for NEST from an XML description, compiling the necessary module files
        
        @param nineml_model [str]: The parsed 9ML biophysical cell model
        @param celltype_name [str]: Name of the cell class to extract from the xml file
        @param morph_id [str]: Currently unused but kept for consistency with NEURON version of this function
        @param build_mode [str]: Control the automatic building of required modules
        @param silent [bool]: Whether or not to suppress build output
        """
        try:
            celltype = cls.loaded_celltypes[(celltype_name, nineml_model.url)]
        except KeyError:
            dct = {}
            install_dir, dct['component_translations'] = build_celltype_files(celltype_name,
                                                                              nineml_model.biophysics.name,
                                                                              nineml_model.url,
                                                                              build_mode=build_mode,
                                                                              method=solver_name)
            lib_dir = os.path.join(install_dir, 'lib', 'nest')
            if sys.platform.startswith('linux') or \
                                        sys.platform in ['os2', 'os2emx', 'cygwin', 'atheos', 'ricos']:
                lib_path_key = 'LD_LIBRARY_PATH'
            elif sys.platform == 'darwin':
                lib_path_key = 'DYLD_LIBRARY_PATH'
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
            dct['nineml_model'] = nineml_model
            # Add the loaded cell type to the list of cell types that have been loaded
            celltype = super(NineCellMetaClass, cls).__new__(cls, nineml_model, celltype_name,
                                                             (NineCell,), dct)
            # Added the loaded celltype to the dictionary of previously loaded cell types
            cls.loaded_celltypes[(celltype_name, nineml_model.url)] = celltype
        return celltype
    
    
    
    
