"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
from pype9.base.network.cell_wrapper import (
    PyNNCellWrapper as BasePyNNCellWrapper,
    PyNNCellWrapperMetaClass as BasePyNNCellWrapperMetaClass)
from pype9.exceptions import Pype9BuildOptionMismatchException
from pyNN.parameters import ParameterSpace
import pyNN.standardmodels
import nest
from pype9.nest.cells import CellMetaClass


class PyNNCellWrapper(BasePyNNCellWrapper,
                      pyNN.standardmodels.StandardCellType):

    standard_receptor_type = None

    def __init__(self, **parameters):
        BasePyNNCellWrapper.__init__(self)
        pyNN.standardmodels.StandardCellType.__init__(self, **parameters)

    def memb_init(self):
        # Initialisation of member states goes here
        print ("WARNING, membrane initialization function has not been "
               "implemented")

    def translate(self, parameters):
        """
        Translate standardized model parameters to simulator-specific
        parameters. Overrides the the method in StandardModelType to provide a
        simpler translation that avoids the evaluation of the 'dots' in the
        standard name
        """
        native_parameters = {}
        for name in parameters.keys():
            native_parameters[
                self.translations[name]['translated_name']] = parameters[name]
        return ParameterSpace(
            native_parameters, schema=None, shape=parameters.shape)

    def get_receptor_type(self, name):
        if name.startswith('{'):
            name = name[name.find('}') + 1:]
        return nest.GetDefaults(self.nest_model)["receptor_types"][name]


class PyNNCellWrapperMetaClass(BasePyNNCellWrapperMetaClass):

    """
    Metaclass for compiling NineMLCellType subclases Called by
    nineml_celltype_from_model
    """

    loaded_celltypes = {}

    def __new__(cls, name, component_class, default_properties=None,
                initial_state=None, **kwargs):  # @UnusedVariable
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
            celltype = super(PyNNCellWrapperMetaClass, cls).__new__(
                cls, name, (PyNNCellWrapper,), dct)
            # If the url where the celltype is defined is specified save the
            # celltype to be retried later
            if component_class.url is not None:
                cls.loaded_celltypes[(name, component_class.url)] = (celltype,
                                                                     kwargs)
        return celltype
