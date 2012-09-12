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

SRC_PATH_ENV_NAME = 'NINEMLP_SRC_PATH'
MPI_NAME = 'NINEMLP_MPI'

BUILD_MODE_OPTIONS = ['lazy', 'force', 'compile_only', 'require']
DEFAULT_BUILD_MODE = 'lazy'

if SRC_PATH_ENV_NAME in os.environ: # NINEMLP_SRC_PATH has been set as an environment variable use it
    SRC_PATH = os.environ[SRC_PATH_ENV_NAME]
else: # Otherwise determine from path to this module
    SRC_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

if MPI_NAME in os.environ:
    import mpi4py #@UnresolvedImport

