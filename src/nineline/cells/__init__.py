"""

  This package contains the XML handlers to read the NCML files and related functions/classes, 
  the NCML base meta-class (a meta-class is a factory that generates classes) to generate a class
  for each NCML cell description (eg. a 'Purkinje' class for an NCML containing a declaration of 
  a Purkinje cell), and the base class for each of the generated cell classes.

  @file ncml.py
  @author Tom Close

"""

#######################################################################################
#
#    Copyright 2012 Okinawa Institute of Science and Technology (OIST), Okinawa, Japan
#
#######################################################################################
from __future__ import absolute_import
import collections
import math
from itertools import chain

# DEFAULT_V_INIT = -65

class NineCell(object):
    
    pass


class NineCellMetaClass(type):
    
    def __new__(cls, celltype_name, nineml_model, bases, dct):
        dct['parameter_names'] = [p.name for p in nineml_model.parameters]
        return super(NineCellMetaClass, cls).__new__(cls, celltype_name, bases, dct)

    def __init__(cls, celltype_name, nineml_model, morph_id=None, build_mode=None, #@NoSelf
                   silent=None, solver_name=None):
        """
        This initialiser is empty, but since I have changed the signature of the __new__ method in 
        the deriving metaclasses it complains otherwise (not sure if there is a more elegant way 
        to do this).
        """
        pass
    
    
if __name__ == "__main__":
    print "doing nothing"




