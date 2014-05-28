from __future__ import absolute_import
try:
    from mpi4py import MPI  # @UnresolvedImport @UnusedImport
except:
    pass
import nineline.pyNN.common
from neuron import h
from pyNN.common.control import build_state_queries
import pyNN.neuron.simulator as simulator
import pyNN.models
from nineline.cells.neuron import NineCellMetaClass, basic_nineml_translations
import logging

logger = logging.getLogger("PyNN")

get_current_time, get_time_step, get_min_delay, \
        get_max_delay, num_processes, rank = build_state_queries(simulator)


class NinePyNNCell(pyNN.models.BaseCellType, nineline.pyNN.common.cells.NinePyNNCell):
    """
    Extends the vanilla NineCell to include all the PyNN requirements
    """
    pass


class NinePyNNCellMetaClass(nineline.pyNN.common.cells.NinePyNNCellMetaClass):

    _basic_nineml_translations = basic_nineml_translations
    loaded_celltypes = {}

    def __new__(cls, nineml_model, name, build_mode='lazy', silent=False, 
                solver_name=None, standalone=False):
        try:
            celltype = cls.loaded_celltypes[(nineml_model.name, nineml_model.url)]
        except KeyError:
            model = NineCellMetaClass(nineml_model, name, build_mode=build_mode, silent=silent,
                                      solver_name=solver_name, standalone=False)
            dct = {'model': model}
            celltype = super(NinePyNNCellMetaClass, cls).__new__(cls, name, (NinePyNNCell,), dct)
            assert sorted(celltype.recordable) == sorted(model().recordable.keys()), \
                    ("Mismatch of recordable keys between NineCellPyNN and NineCell class '{}'"
                     .format(name))
            # If the url where the celltype is defined is specified save the celltype to be retried
            # later
            if nineml_model.url is not None:
                cls.loaded_celltypes[(name, nineml_model.url)] = celltype
        return celltype
