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

DEFAULT_V_INIT = -65

class NineCell(object):
    
    class Parameter(object):
        
        def __init__(self, varname, segments, default_value):
            self.varname = varname
            self.segments = segments
            self.value = default_value
            
        def set(self, value):
            for seg in self.segments:
                setattr(seg, self.varname, value)

    def memb_init(self):
        # Initialisation of member states goes here        
        raise NotImplementedError("'memb_init' should be implemented by the derived class.")


class NineCellMetaClass(type):
    

    def __init__(cls, celltype_name, nineml_path, morph_id=None, build_mode=None, #@NoSelf
                   silent=None, solver_name=None):
        """
        This initialiser is empty, but since I have changed the signature of the __new__ method in 
        the deriving metaclasses it complains otherwise (not sure if there is a more elegant way 
        to do this).
        """
        pass
    
if __name__ == "__main__":
    print "doing nothing"




