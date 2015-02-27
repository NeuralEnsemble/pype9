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
from abc import ABCMeta
from copy import deepcopy
from pype9.exceptions import Pype9RuntimeError


class Pype9CellMetaClass(type):

    """
    Metaclass for building NineMLPype9CellType subclasses Called by
    nineml_celltype_from_model
    """

    __metaclass__ = ABCMeta

    def __new__(cls, component, name=None, **kwargs):
        """
        `component` -- Either a parsed lib9ml SpikingNode object or a url
                       to a 9ml file
        `name`      -- Either the name of a component within the given url
                       or a name to call the class built with the specified
                       build options (passed in kwargs).
        """
        # Extract out build directives
        build_mode = kwargs.pop('build_mode', 'lazy')
        verbose = kwargs.pop('verbose', False)
        if isinstance(component, basestring):
            url = component
        else:
            url = component.url
            if name is None:
                name = component.name
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
            component, instl_dir = cls.CodeGenerator().generate(
                component, name, build_mode=build_mode, verbose=verbose,
                **kwargs)
            name = component.name
            # Load newly build model
            cls.load_model(name, instl_dir)
            # Create class member dict of new class
            dct = {'component': component,
                   'install_dir': instl_dir}
            # Create new class using Type.__new__ method
            Cell = super(Pype9CellMetaClass, cls).__new__(
                cls, name, (cls.BaseCellClass,), dct)
            # Save Cell class to allow it to save it being built again
            cls._built_types[(name, component.url)] = Cell, kwargs
        return Cell

    def __init__(cls, component, name=None, **kwargs):
        """
        This initialiser is empty, but since I have changed the signature of
        the __new__ method in the deriving metaclasses it complains otherwise
        (not sure if there is a more elegant way to do this).
        """
        pass


class Pype9Cell(object):

    __metaclass__ = ABCMeta

    def __init__(self, model=None):
        """
        `model` -- A "Tree" object derived from the same source as the default
                   model used to create the class. This default model can be
                   accessed via the 'copy_of_default_model' method. Providing
                   the model here is provided here to allow the modification of
                   morphology and distribution of ion channels programmatically
        """
        if model:
            if model._source is not self._default_model._source:
                raise Exception("Only models derived from the same source as "
                                "the default model can be used to instantiate "
                                "the cell with.")
            self._model = model
        else:
            self._model = self._default_model

    @classmethod
    def copy_of_default_model(cls):
        return deepcopy(cls._default_model)


class DummyNinemlModel(object):

    def __init__(self, name, url, model):
        self.name = name
        self.url = url
        self.model = model
        self.parameters = []
