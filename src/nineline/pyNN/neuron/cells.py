from __future__ import absolute_import 
try:
    from mpi4py import MPI # @UnresolvedImport @UnusedImport
except:
    pass
import nineline.pyNN.common
from pyNN.common.control import build_state_queries
import pyNN.neuron.simulator as simulator
import pyNN.models
from nineline.cells.neuron import NineCellMetaClass
import logging

logger = logging.getLogger("PyNN")

get_current_time, get_time_step, get_min_delay, \
        get_max_delay, num_processes, rank = build_state_queries(simulator)


class NinePyNNCell(pyNN.models.BaseCellType, nineline.pyNN.common.cells.NinePyNNCell):   
    """
    At this stage it doesn't appear necessary to include this cell type but will keep it for now.
    """
    pass


class NinePyNNCellMetaClass(nineline.pyNN.common.cells.NinePyNNCellMetaClass):
    
    loaded_celltypes = {}
    
    def __new__(cls, name, nineml_path, morph_id=None, build_mode='lazy', silent=False, 
                solver_name=None):
        if cls.loaded_celltypes.has_key((name, nineml_path)):
            celltype = cls.loaded_celltypes((name, nineml_path))
        else:
            model = NineCellMetaClass(name, nineml_path, morph_id=morph_id, build_mode=build_mode, 
                                      silent=silent, solver_name=solver_name)
            dct = {'model': model,
                   'recordable': model().recordable.keys()}
            celltype = super(NinePyNNCellMetaClass, cls).__new__(cls, name, (NinePyNNCell,), dct)
            cls.loaded_celltypes[(name, nineml_path)] = celltype
        return celltype
    