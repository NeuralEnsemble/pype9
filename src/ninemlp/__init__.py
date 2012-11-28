"""

  This package aims to contain all extensions to the pyNN package required for interpreting 
  networks specified in NINEML+. It is possible that some changes will need to be made in the 
  pyNN package itself (although as of 13/6/2012 this hasn't been necessary).
  
  @file ncml.py
  @author Tom Close

"""

#######################################################################################
#
#    Copyright 2012 Okinawa Institute of Science and Technology (OIST), Okinawa, Japan
#
#######################################################################################

import os
import xml.sax

__version__ = "0.0.1"

SRC_PATH_ENV_NAME = 'NINEMLP_SRC_PATH'
MPI_NAME = 'NINEMLP_MPI'

BUILD_MODE_OPTIONS = ['lazy', 'force', 'build_only', 'require', 'compile_only']
DEFAULT_BUILD_MODE = 'lazy'
pyNN_build_mode = DEFAULT_BUILD_MODE

if SRC_PATH_ENV_NAME in os.environ: # NINEMLP_SRC_PATH has been set as an environment variable use it
    SRC_PATH = os.environ[SRC_PATH_ENV_NAME]
else: # Otherwise determine from path to this module
    SRC_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

if MPI_NAME in os.environ:
    import mpi4py #@UnresolvedImport


class XMLHandler(xml.sax.handler.ContentHandler):

    def __init__(self):
        self._open_components = []
        self._required_attrs = []

    def characters(self, data):
        pass

    def endElement(self, name):
        """
        Closes a component, removing its name from the _open_components list. 
        
        WARNING! Will break if there are two tags with the same name, with one inside the other and 
        only the outer tag is opened and the inside tag is differentiated by its parents
        and attributes (this would seem an unlikely scenario though). The solution in this case is 
        to open the inside tag and do nothing. Otherwise opening and closing all components 
        explicitly is an option.
        """
        if self._open_components and name == self._open_components[-1]:
            self._open_components.pop()
            self._required_attrs.pop()

    def _opening(self, tag_name, attr, ref_name, parents=[], required_attrs=[]):
        if tag_name == ref_name and self._parents_match(parents, self._open_components) and \
                all([(attr[key] == val or val == None) for key, val in required_attrs]):
            self._open_components.append(ref_name)
            self._required_attrs.append(required_attrs)
            return True
        else:
            return False

    def _closing(self, tag_name, ref_name, parents=[], required_attrs=[]):
        if tag_name == ref_name and self._parents_match(parents, self._open_components[:-1]) and \
                self._required_attrs[-1] == required_attrs:
            return True
        else:
            return False
        
    def _parents_match(self, required_parents, open_parents):
        if len(required_parents) > open_parents:
            return False
        for required, open in zip(reversed(required_parents), reversed(open_parents)):
            if isinstance(required, str):
                if required != open:
                    return False
            else:
                try:
                    if not any([ open == r for r in required]):
                        return False
                except TypeError:
                    raise Exception("Elements of the 'required_parents' argument need to be " \
                                    "either strings or lists/tuples of strings") 
        return True
                
                
                
                
                
                
                
                
                
                
                
                
                
        
