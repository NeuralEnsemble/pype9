"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2017 Thomas G. Close.
  License: This file is part of the "Pype9" package, which is released under
           the MIT Licence, see LICENSE for details.
"""

# Import mpi4py here so it is always imported before Neuron, as otherwise
# Neuron can throw an error
from .version import __version__
from .utils.mpi import mpi_comm
