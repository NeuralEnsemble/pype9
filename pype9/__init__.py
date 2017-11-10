"""

  This package aims to contain all extensions to the pyNN package required for
  interpreting networks specified in NINEML+. It is possible that some changes
  will need to be made in the pyNN package itself (although as of 13/6/2012
  this hasn't been necessary).

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""

# Import mpi4py here so it is always imported before Neuron, as otherwise
# Neuron can throw an error
from .mpi import mpi_comm

__version__ = "0.1"
