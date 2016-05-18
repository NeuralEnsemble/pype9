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
from pype9.base.network.cell_wrapper import (
    PyNNCellWrapper as BasePyNNCellWrapper,
    PyNNCellWrapperMetaClass as BasePyNNCellWrapperMetaClass)
from ..units import UnitHandler
from pype9.annotations import (
    PYPE9_NS, MEMBRANE_VOLTAGE, MECH_TYPE, FULL_CELL_MECH)

logger = logging.getLogger("PyNN")


class PyNNCellWrapper(BasePyNNCellWrapper, pyNN.models.BaseCellType):

    """
    Extends the vanilla Cell to include all the PyNN requirements
    """
    UnitHandler = UnitHandler


class PyNNCellWrapperMetaClass(BasePyNNCellWrapperMetaClass):

    loaded_celltypes = {}
    UnitHandler = UnitHandler

    def __new__(cls, name, component_class, default_properties=None,
                initial_state=None, build_mode='lazy', silent=False,
                solver_name=None, standalone=False, **kwargs):  # @UnusedVariable @IgnorePep8
        try:
            celltype = cls.loaded_celltypes[
                (component_class.name, component_class.url)]
        except KeyError:
            model = CellMetaClass(component_class=component_class,
                                  default_properties=default_properties,
                                  initial_state=initial_state, name=name,
                                  build_mode=build_mode, silent=silent,
                                  solver_name=solver_name,
                                  standalone=False, **kwargs)
            dct = {'model': model,
                   'default_properties': default_properties,
                   'initial_state': initial_state}
            celltype = super(PyNNCellWrapperMetaClass, cls).__new__(
                cls, name, (PyNNCellWrapper,), dct)
            # Replace membrane voltage in recordables with 'v'
            # FIXME: This is a bit messy but has to do with conventions used in
            #        PyNN. Ideally I think that I will cherry pick the parts of
            #        PyNN I need and change the conventions so that they work
            #        with 9ML.
            annots = model.build_component_class.annotations[PYPE9_NS]
            if annots[MECH_TYPE] == FULL_CELL_MECH:
                celltype.recordable.remove(annots[MEMBRANE_VOLTAGE])
                celltype.recordable.append('v')
            assert set(celltype.recordable) == set(
                model().recordable.keys()), \
                ("Mismatch of recordable keys between CellPyNN ('{}') and "
                 "Cell class '{}' ('{}')".format(
                     "', '".join(sorted(celltype.recordable)), name,
                     "', '".join(sorted(model().recordable.keys()))))
            # If the url where the celltype is defined is specified save the
            # celltype to be retried later
            if component_class.url is not None:
                cls.loaded_celltypes[(name, component_class.url)] = celltype
        return celltype
