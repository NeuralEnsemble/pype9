"""
  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
import os
import errno
import numpy
from pype9.exceptions import Pype9RuntimeError
import nineml
from nineml import (
    Unit, Dynamics, ConnectionRule, RandomDistribution,
    DynamicsProperties, ConnectionRuleProperties,
    RandomDistributionProperties, Definition)
from nineml.user import Property
from copy import copy
from nineml.exceptions import NineMLMissingElementError


def remove_ignore_missing(path):
    try:
        os.remove(path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def ensure_camel_case(name):
    if len(name) < 2:
        raise Exception("The name ('{}') needs to be at least 2 letters long"
                        "to enable the capitalized version to be different "
                        "from upper case version".format(name))
    if name == name.lower() or name == name.upper():
        name = name.title()
    return name


class abstractclassmethod(classmethod):

    __isabstractmethod__ = True

    def __init__(self, callable_method):
        callable_method.__isabstractmethod__ = True
        super(abstractclassmethod, self).__init__(callable_method)


class classproperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


def load_9ml_prototype(url_or_comp, default_value=0.0, override_name=None,
                       saved_name=None, **kwargs):  # @UnusedVariable
    """
    Reads a component from file, checking to see if there is only one
    component or component class in the file (or not reading from file at
    all if component is already a component or component class).
    """
    if isinstance(url_or_comp, str):
        # Interpret the given prototype as a URL of a NineML prototype
        url = url_or_comp
        # Read NineML description
        document = nineml.read(url)
        if saved_name is not None:
            try:
                prototype = document[saved_name]
            except NineMLMissingElementError:
                raise Pype9RuntimeError(
                    "Could not find a component named '{}' at the url '{}' "
                    "(found '{}')."
                    .format(saved_name, url,
                            "', '".join(nineml.read(url).iterkeys())))
        else:
            components = list(document.components)
            if len(components) == 1:
                prototype = components[0]
            else:
                if len(components) > 1:
                    component_classes = set((c.component_class
                                            for c in components))
                else:
                    component_classes = list(document.component_classes)
                if len(component_classes) == 1:
                    prototype = component_classes[0]
                elif len(component_classes) > 1:
                    raise Pype9RuntimeError(
                        "Multiple component and or classes ('{}') loaded "
                        "from nineml path '{}'"
                        .format("', '".join(
                            c.name for c in document.components), url))
                else:
                    raise Pype9RuntimeError(
                        "No components or component classes loaded from "
                        "nineml" " path '{}'".format(url))
    elif isinstance(url_or_comp, nineml.abstraction.Dynamics):
        component_class = url_or_comp
        definition = Definition(component_class)
        properties = []
        for param in component_class.parameters:
            properties.append(Property(
                name=param.name, value=default_value,
                units=Unit(
                    ('unit' + param.dimension.name),
                    dimension=param.dimension, power=0)))
        if isinstance(component_class, Dynamics):
            ComponentType = DynamicsProperties
        elif isinstance(component_class, ConnectionRule):
            ComponentType = ConnectionRuleProperties
        elif isinstance(component_class, RandomDistribution):
            ComponentType = RandomDistributionProperties
        prototype = ComponentType(name=component_class.name + 'Properties',
                                  definition=definition,
                                  properties=properties)
    elif isinstance(url_or_comp, nineml.user.Component):
        prototype = copy(url_or_comp)
    else:
        raise Pype9RuntimeError(
            "Can't load 9ML prototype from '{}' object".format(url_or_comp))
    if override_name is not None:
        prototype.name = override_name
    return prototype
