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

import os.path
import nest
import pyNN.nest
from ninemlp.common.ncml import BaseNCMLCell, BaseNCMLMetaClass
from ninemlp import DEFAULT_BUILD_MODE

installed_modules = []

RELATIVE_NMODL_DIR = 'build/nest'

def load_module(module_name):
    if not module_name in installed_modules:
        nest.Install(module_name)
        installed_modules.append(module_name)


class NCMLCell(BaseNCMLCell, pyNN.nest.NativeCellType):

    def __init__(self, parameters):
        BaseNCMLCell.__init__(self)
        pyNN.nest.NativeCellType.__init__(self, parameters)

    def memb_init(self):
        # Initialisation of member states goes here        
        pass

def load_cell_type(cell_typename, nineml_dir, build_mode=DEFAULT_BUILD_MODE):
    load_module(os.path.join(nineml_dir, RELATIVE_NMODL_DIR, cell_typename))
    cell_type = type(cell_typename, (pyNN.nest.NativeCellType, NCMLCell,),
                                                        {'nest_model' : cell_typename})

    return cell_type


class NCMLMetaClass(BaseNCMLMetaClass):
    """
    Metaclass for compileing NineMLCellType subclasses
    Called by nineml_celltype_from_model
    """
    def __new__(cls, name, bases, dct):
        #The __init__ function for the created class  
        def __init__(self, parameters={}):
            pyNN.nest.NativeCellType.__init__(self, parameters)
            NCMLCell.__init__(self)
        dct['__init__'] = __init__
        cell_type = super(NCMLMetaClass, cls).__new__(cls, name, bases, dct)
        cell_type.model = cell_type
        return cell_type


