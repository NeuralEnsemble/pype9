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

__version__ = "0.0.1"

BUILD_MODE_OPTIONS = ['lazy', 'force', 'compile_only']

SRC_PATH_ENV_NAME = 'NINEMLP_SRC_PATH'
BUILD_MODE_NAME = 'NINEMLP_BUILD_MODE'
MPI_NAME = 'NINEMLP_MPI'

if SRC_PATH_ENV_NAME in os.environ: # NINEMLP_SRC_PATH has been set as an environment variable use it
    SRC_PATH = os.environ[SRC_PATH_ENV_NAME]
else: # Otherwise determine from path to this module
    SRC_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

def set_build_mode(build_mode):
    """
    Sets the build mode for the whole system (including pyNN components) 
    """
    if build_mode != 'lazy' and build_mode != 'compile_only' and build_mode != 'force':
        raise Exception("Unrecognised build mode '%s' (valid options are 'lazy', 'compile_only' or 'force')" % build_mode)
    _BUILD_MODE = build_mode
    
def get_build_mode():
    return _BUILD_MODE

if BUILD_MODE_NAME in os.environ:
    _BUILD_MODE = set_build_mode(os.environ[BUILD_MODE_NAME])
else:
    _BUILD_MODE = 'lazy'
    
print _BUILD_MODE

if MPI_NAME in os.environ:
    import mpi4py #@UnresolvedImport

