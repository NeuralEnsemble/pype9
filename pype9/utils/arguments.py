"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
# from pype9.utils.mpi import mpi_comm
import os.path
import nineml
import ninemlcatalog
from argparse import ArgumentTypeError
import pype9.utils.logging.handlers.sysout  # @UnusedImport

CATALOG_PREFIX = 'catalog://'


def existing_file(fname):
    if not os.path.isfile(fname):
        raise ArgumentTypeError(
            "'{}' does not refer to an existing file".format(fname))
    return fname


def nineml_document(doc_path):
    if doc_path.startswith(CATALOG_PREFIX):
        model = ninemlcatalog.load(doc_path[len(CATALOG_PREFIX):])
    else:
        if (not doc_path.startswith('/') and
            not doc_path.startswith('./') and
                not doc_path.startswith('../')):
            doc_path = './' + doc_path
        model = nineml.read(doc_path, relative_to=os.getcwd())
    return model


def nineml_model(model_path):
    model = nineml_document(model_path)
    if isinstance(model, nineml.Document):
        model = model.as_network(
            os.path.splitext(os.path.basename(model_path))[0])
    return model

# Might be useful so have kept it here
#
# class randomseed(int):
#
#     """
#     Automatically generates unique random seeds if none are provided, as well
#     as ensuring that unique seeds are passed to each MPI process
#
#     Parameters
#     ----------
#     arg : int
#         An existing seed to use
#     mirror_mpi: bool
#         Flags whether the seeds should be the same on different
#         MPI nodes or not
#     """
#     counter = 0
#
#     def __new__(cls, arg=None, mirror_mpi=False):
#         if arg is None or arg == 'None' or int(arg) == 0:
#             seed = int(time.time() * 256) + cls.counter
#             cls.counter += 1
#         else:
#             seed = int(arg)
#         # Ensure a different seed gets used on each MPI node
#         if not mirror_mpi:
#             seed = seed * mpi_comm.size + mpi_comm.rank
#         return cls(seed)
