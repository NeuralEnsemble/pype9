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
from pype9.simulate.neuron.cells import CellMetaClass
from pype9.simulate.common.network.cell_wrapper import (
    PyNNCellWrapper as BasePyNNCellWrapper,
    PyNNCellWrapperMetaClass as BasePyNNCellWrapperMetaClass)
from ..units import UnitHandler


class PyNNCellWrapper(BasePyNNCellWrapper, pyNN.models.BaseCellType):

    """
    Extends the vanilla Cell to include all the PyNN requirements
    """


class PyNNCellWrapperMetaClass(BasePyNNCellWrapperMetaClass):

    loaded_celltypes = {}

    def __new__(cls, component_class, default_properties,
                initial_state, initial_regime, **kwargs):  # @UnusedVariable @IgnorePep8
        model = CellMetaClass(component_class=component_class,
                              default_properties=default_properties,
                              initial_state=initial_state,
                              standalone=False, **kwargs)
        try:
            celltype = cls.loaded_celltypes[model.name]
        except KeyError:
            dct = {'model': model,
                   'default_properties': default_properties,
                   'initial_state': initial_state,
                   'initial_regime': initial_regime,
                   'extra_parameters': {'_in_array': True}}
            celltype = super(PyNNCellWrapperMetaClass, cls).__new__(
                cls, model.name, (PyNNCellWrapper,), dct)
            recordable_keys = list(model(default_properties,
                                         _in_array=True).recordable.keys())
            assert set(celltype.recordable) == set(recordable_keys), (
                "Mismatch of recordable keys between CellPyNN ('{}') and "
                "Cell class '{}' ('{}')".format(
                    "', '".join(set(celltype.recordable)), model.name,
                    "', '".join(set(recordable_keys))))
            cls.loaded_celltypes[model.name] = celltype
        return celltype
