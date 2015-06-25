"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
try:
    from mpi4py import MPI  # @UnresolvedImport @UnusedImport
except:
    pass
import pyNN.models
from pype9.neuron.cells import CellMetaClass
import logging
from pype9.common.network.wrapper import (
    PyNNCellWrapper as BasePyNNCellWrapper,
    PyNNCellWrapperMetaClass as BasePyNNCellWrapperMetaClass)

logger = logging.getLogger("PyNN")


class PyNNCellWrapper(BasePyNNCellWrapper, pyNN.models.BaseCellType):

    """
    Extends the vanilla Cell to include all the PyNN requirements
    """
    pass


class PyNNCellWrapperMetaClass(BasePyNNCellWrapperMetaClass):

    _basic_nineml_translations = basic_nineml_translations
    loaded_celltypes = {}

    def __new__(cls, nineml_model, name, build_mode='lazy', silent=False,
                solver_name=None, standalone=False):  # @UnusedVariable
        try:
            celltype = cls.loaded_celltypes[
                (nineml_model.name, nineml_model.url)]
        except KeyError:
            model = CellMetaClass(nineml_model, name,
                                       build_mode=build_mode, silent=silent,
                                       solver_name=solver_name,
                                       standalone=False)
            dct = {'model': model}
            celltype = super(PyNNCellWrapperMetaClass, cls).__new__(
                cls, name, (PyNNCellWrapper,), dct)
            assert sorted(celltype.recordable) == sorted(
                model().recordable.keys()), \
                ("Mismatch of recordable keys between CellPyNN and "
                 "Cell class '{}'".format(name))
            # If the url where the celltype is defined is specified save the
            # celltype to be retried later
            if nineml_model.url is not None:
                cls.loaded_celltypes[(name, nineml_model.url)] = celltype
        return celltype
