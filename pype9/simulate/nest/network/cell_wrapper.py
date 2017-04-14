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
from pype9.exceptions import Pype9BuildOptionMismatchException
import pyNN.standardmodels
from pype9.simulate.nest.cells import CellMetaClass
from ..units import UnitHandler
from logging import Logger


logger = Logger('Pype9')


class PyNNCellWrapper(BasePyNNCellWrapper,
                      pyNN.standardmodels.StandardCellType):

    standard_receptor_type = None
    UnitHandler = UnitHandler

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
    UnitHandler = UnitHandler

    def __new__(cls, name, component_class, default_properties,
                initial_state, initial_regime, **kwargs):  # @UnusedVariable
        try:
            celltype, build_options = cls.loaded_celltypes[
                (component_class.name, component_class.url)]
            if build_options != kwargs:
                raise Pype9BuildOptionMismatchException()
        except (KeyError, Pype9BuildOptionMismatchException):
            dct = {'model': CellMetaClass(component_class=component_class,
                                          name=name, **kwargs)}
            dct['nest_name'] = {"on_grid": name, "off_grid": name}
            dct['nest_model'] = name
            dct['default_properties'] = default_properties
            dct['initial_state'] = initial_state
            dct['initial_regime'] = initial_regime
            celltype = super(PyNNCellWrapperMetaClass, cls).__new__(
                cls, name, (PyNNCellWrapper,), dct)
            # If the url where the celltype is defined is specified save the
            # celltype to be retried later
            if component_class.url is not None:
                cls.loaded_celltypes[(name, component_class.url)] = (celltype,
                                                                     kwargs)
        return celltype
