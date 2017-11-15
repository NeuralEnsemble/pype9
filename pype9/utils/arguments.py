"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from builtins import str
import time
import os.path
import shutil
from pype9.mpi import mpi_comm


class inputpath(str):

    def __new__(cls, arg):
        path = cls(arg)
        path.references = []
        if path.endswith('.9ml'):
            # TODO: find dependents
            pass
        return path

    def copy_to(self, dest_dir):
        shutil.copy2(self, os.path.join(dest_dir, os.path.basename(self)))


def outputpath(arg):
    return str(arg)


class randomseed(int):

    """
    Automatically generates unique random seeds if none are provided, as well
    as ensuring that unique seeds are passed to each MPI process

    Parameters
    ----------
    arg : int
        An existing seed to use
    mirror_mpi: bool
        Flags whether the seeds should be the same on different
        MPI nodes or not
    """
    counter = 0

    def __new__(cls, arg=None, mirror_mpi=False):
        if arg is None or arg == 'None' or int(arg) == 0:
            seed = int(time.time() * 256) + cls.counter
            cls.counter += 1
        else:
            seed = int(arg)
        # Ensure a different seed gets used on each MPI node
        if not mirror_mpi:
            seed = seed * mpi_comm.size + mpi_comm.rank
        return cls(seed)
