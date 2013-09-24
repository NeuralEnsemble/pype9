from __future__ import absolute_import 
try:
    from mpi4py import MPI # @UnresolvedImport @UnusedImport
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
    
    def __new__(cls, name, nineml_model, build_mode='lazy', silent=False, solver_name=None):
        try:
            celltype = cls.loaded_celltypes[(nineml_model.name, nineml_model.url)]
        except KeyError:
            model = NineCellMetaClass(name, nineml_model, build_mode=build_mode, silent=silent, 
                                      solver_name=solver_name)
            dct = {'model': model,
                   'recordable': model().recordable.keys()}
            celltype = super(NinePyNNCellMetaClass, cls).__new__(cls, name, (NinePyNNCell,), dct)
            # If the url where the celltype is defined is specified save the celltype to be retried later
            if nineml_model.url is not None: 
                cls.loaded_celltypes[(name, nineml_model.url)] = celltype
        return celltype
    