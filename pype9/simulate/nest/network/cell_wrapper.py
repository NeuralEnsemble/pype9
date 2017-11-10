"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
import nest
from pype9.simulate.common.network.cell_wrapper import (
    PyNNCellWrapper as BasePyNNCellWrapper,
    PyNNCellWrapperMetaClass as BasePyNNCellWrapperMetaClass)
from pype9.exceptions import Pype9BuildMismatchError
import pyNN.standardmodels
from pype9.simulate.nest.cells import CellMetaClass
from logging import Logger


logger = Logger('Pype9')


class PyNNCellWrapper(BasePyNNCellWrapper,
                      pyNN.standardmodels.StandardCellType):

    standard_receptor_type = None

    def __init__(self, **parameters):
        BasePyNNCellWrapper.__init__(self)
        pyNN.standardmodels.StandardCellType.__init__(self, **parameters)

    def memb_init(self):
        # Initialisation of member states goes here
        logger.warning("Membrane initialization function has not been "
                       "implemented")

    def get_receptor_type(self, receptor_name):
        return nest.GetDefaults(
            self.nest_model)["receptor_types"][receptor_name]


class PyNNCellWrapperMetaClass(BasePyNNCellWrapperMetaClass):

    """
    Metaclass for compiling NineMLCellType subclases Called by
    nineml_celltype_from_model
    """

    loaded_celltypes = {}

    def __new__(cls, component_class, default_properties,
                initial_state, initial_regime, **kwargs):  # @UnusedVariable
        # Get the basic Pype9 cell class
        model = CellMetaClass(component_class=component_class)
        try:
            celltype = cls.loaded_celltypes[model.name]
        except (KeyError, Pype9BuildMismatchError):
            dct = {'model': model}
            dct['nest_name'] = {"on_grid": model.name, "off_grid": model.name}
            dct['nest_model'] = model.name
            dct['default_properties'] = default_properties
            dct['initial_state'] = initial_state
            dct['initial_regime'] = initial_regime
            celltype = super(PyNNCellWrapperMetaClass, cls).__new__(
                cls, model.name, (PyNNCellWrapper,), dct)
            cls.loaded_celltypes[model.name] = celltype
        return celltype
