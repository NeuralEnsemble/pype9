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
import pype9.network.common
from pyNN.common.control import build_state_queries
import pyNN.neuron.simulator as simulator
import pyNN.models
from pype9.cells.neuron import Pype9CellMetaClass, basic_nineml_translations
import logging

logger = logging.getLogger("PyNN")

get_current_time, get_time_step, get_min_delay, \
    get_max_delay, num_processes, rank = build_state_queries(simulator)


class Pype9PyNNCell(
        pyNN.models.BaseCellType, pype9.network.common.cells.Pype9PyNNCell):

    """
    Extends the vanilla Pype9Cell to include all the PyNN requirements
    """
    pass


class Pype9PyNNCellMetaClass(pype9.network.common.cells.Pype9PyNNCellMetaClass):

    _basic_nineml_translations = basic_nineml_translations
    loaded_celltypes = {}

    def __new__(cls, nineml_model, name, build_mode='lazy', silent=False,
                solver_name=None, standalone=False):  # @UnusedVariable
        try:
            celltype = cls.loaded_celltypes[
                (nineml_model.name, nineml_model.url)]
        except KeyError:
            model = Pype9CellMetaClass(nineml_model, name,
                                      build_mode=build_mode, silent=silent,
                                      solver_name=solver_name,
                                      standalone=False)
            dct = {'model': model}
            celltype = super(Pype9PyNNCellMetaClass, cls).__new__(
                cls, name, (Pype9PyNNCell,), dct)
            assert sorted(celltype.recordable) == sorted(
                model().recordable.keys()), \
                ("Mismatch of recordable keys between Pype9CellPyNN and "
                 "Pype9Cell class '{}'".format(name))
            # If the url where the celltype is defined is specified save the
            # celltype to be retried later
            if nineml_model.url is not None:
                cls.loaded_celltypes[(name, nineml_model.url)] = celltype
        return celltype
