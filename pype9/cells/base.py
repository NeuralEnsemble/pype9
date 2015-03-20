"""

  This package contains the XML handlers to read the NineML files and related
  functions/classes, the NineML base meta-class (a meta-class is a factory that
  generates classes) to generate a class for each NineML cell description (eg.
  a 'Purkinje' class for an NineML containing a declaration of a Purkinje
  cell), and the base class for each of the generated cell classes.

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from copy import deepcopy
from pype9.exceptions import Pype9RuntimeError
from pype9.utils import load_9ml_prototype
import time
import os.path


class CellMetaClass(type):

    """
    Metaclass for building NineMLCellType subclasses Called by
    nineml_celltype_from_model
    """

    def __new__(cls, component, name=None, saved_name=None, **kwargs):
        """
        `component`  -- Either a parsed lib9ml SpikingNode object or a url
                        to a 9ml file
        `name`       -- The name to call the class built with the specified
                        build options (passed in kwargs).
        `saved_name` -- The name of a component within the given url
        """
        if name is None:
            name = saved_name
        # Extract out build directives
        build_mode = kwargs.pop('build_mode', 'lazy')
        verbose = kwargs.pop('verbose', False)
        prototype = load_9ml_prototype(component, default_value=0.0,
                                       override_name=name,
                                       saved_name=saved_name)
        name = prototype.name
        url = prototype.url
        try:
            Cell, build_options = cls._built_types[(name, url)]
            if build_options != kwargs:
                raise Pype9RuntimeError(
                    "Build options '{}' do not match previously built '{}' "
                    "cell class with same name ('{}'). Please specify a "
                    "different name (using a loaded nineml.Component instead "
                    "of a URL)."
                    .format(kwargs, name, build_options))
        except KeyError:
            # Initialise code generator
            code_gen = cls.CodeGenerator()
            build_prototype = code_gen.transform_for_build(prototype, **kwargs)
            # Set build dir default from original prototype url if not
            # explicitly provided
            build_dir = kwargs.pop('build_dir', None)
            if build_dir is None:
                build_dir = code_gen.get_build_dir(prototype.url, name)
            mod_time = time.ctime(os.path.getmtime(url))
            instl_dir = code_gen.generate(
                build_prototype, build_mode=build_mode, verbose=verbose,
                build_dir=build_dir, mod_time=mod_time, **kwargs)
            # Load newly build model
            cls.load_libraries(name, instl_dir)
            # Create class member dict of new class
            dct = {'name': name,
                   'componentclass': prototype.component_class,
                   'prototype': prototype,
                   'install_dir': instl_dir,
                   'build_prototype': build_prototype,
                   'build_componentclass': build_prototype.component_class,
                   'build_options': kwargs}
            # Create new class using Type.__new__ method
            Cell = super(CellMetaClass, cls).__new__(
                cls, name, (cls.BaseCellClass,), dct)
            # Save Cell class to allow it to save it being built again
            cls._built_types[(name, url)] = Cell, kwargs
        return Cell

    def __init__(cls, component, name=None, **kwargs):
        """
        This initialiser is empty, but since I have changed the signature of
        the __new__ method in the deriving metaclasses it complains otherwise
        (not sure if there is a more elegant way to do this).
        """
        pass

    def load_libraries(self, name, install_dir, **kwargs):
        """
        To be overridden by derived classes to allow the model to be loaded
        from compiled external libraries
        """
        pass

    def transform_for_build(self, component, **kwargs):  # @UnusedVariable
        """
        To be overridden by derived classes to transform the model into a
        format that better suits the simulator implementation
        """
        transformed_elems = {}
        return component, transformed_elems


class Cell(object):

    def __init__(self, model=None):
        """
        `model` -- A "Tree" object derived from the same source as the default
                   model used to create the class. This default model can be
                   accessed via the 'copy_of_default_model' method. Providing
                   the model here is provided here to allow the modification of
                   morphology and distribution of ion channels programmatically
        """
#     if model:
#         if model._source is not self._default_model._source:
#             raise Exception("Only models derived from the same source as "
#                             "the default model can be used to instantiate "
#                             "the cell with.")
#         self._model = model
#     else:
#         self._model = self.prototype
        pass

    @classmethod
    def copy_of_default_model(cls):
        return deepcopy(cls._default_model)


class DummyNinemlModel(object):

    def __init__(self, name, url, model):
        self.name = name
        self.url = url
        self.model = model
        self.parameters = []
