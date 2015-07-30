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
from pype9.exceptions import Pype9RuntimeError
from pype9.utils import load_9ml_prototype
from itertools import chain
import time
import os.path
import neo
import quantities as pq
from datetime import datetime
import nineml
from pype9.utils import convert_to_property


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

    def __init__(self, *properties, **kwprops):
        # Combine keyword and non-keyword properties into a single list
        if len(properties) == 1 and isinstance(properties, dict):
            kwprops.update(properties)
            properties = []
        else:
            properties = list(properties)
        for name, qty in kwprops.iteritems():
            properties.append(convert_to_property(name, qty))
        # Init the 9ML component of the cell
        self._nineml = nineml.user.DynamicsProperties(
            self.prototype.name, self.prototype, properties)
        # Set up references from parameter names to internal variables and set
        # parameters
        for prop in self.properties:
            self.set(prop)
        # Flag to determine whether the cell has been initialised or not
        # (it makes a difference to how the state of the cell is updated,
        # either saved until the 'initialze' method is called or directly
        # set to the state)
        self._initialized = False
        self._initial_state = None

    def set(self, prop):
        """
        Sets the properties of the cell, should be overrided/extended to set
        the simulator specific properties as well
        """
        self._nineml.set(prop)

    def __dir__(self):
        """
        Append the property names to the list of attributes of a cell object
        """
        return list(set(chain(
            dir(super(self.__class__, self)), self.property_names,
            self.state_variable_names)))

    @property
    def properties(self):
        """
        The set of componentclass properties (parameter values).
        """
        return self._nineml.properties

    @property
    def property_names(self):
        return self._nineml.property_names

    @property
    def state_variable_names(self):
        return self._nineml.component_class.state_variable_names

    def __repr__(self):
        return '{}(component_class="{}")'.format(
            self.__class__.__name__, self._nineml.component_class.name)

    def to_xml(self):
        return self._nineml.to_xml()

    @property
    def used_units(self):
        return self._nineml.used_units

    def update_state(self, state):
        if self._initialized:
            self._set_state(state)
        else:
            super(Cell, self).__setattr__('_initial_state', state)

    def _set_state(self, state):
        for k, q in state.iteritems():
            setattr(self, k, q)  # FIXME: Need to convert units

    def initialize(self):
        if self._initial_state is None:
            raise Pype9RuntimeError("Initial state not set for '{}' cell"
                                    .format(self.name))
        self._set_state(self._initial_state)
        super(Cell, self).__setattr__('_initialized', True)

    def write(self, file):  # @ReservedAssignment
        self._nineml.write(file)

    def run(self, simulation_time, reset=True, timestep='cvode', rtol=None,
            atol=None):
        if self not in (c() for c in self._controller.registered_cells):
            raise Pype9RuntimeError(
                "PyPe9 Cell '{}' is not being recorded".format(self.name))
        self._controller.run(simulation_time=simulation_time, reset=reset,
                                  timestep=timestep, rtol=rtol, atol=atol)

    def reset_recordings(self):
        """
        Resets the recordings for the cell and the NEURON simulator (assumes
        that only one cell is instantiated)
        """
        for rec in self._recordings.itervalues():
            rec.resize(0)

    def clear_recorders(self):
        """
        Clears all recorders and recordings
        """
        super(Cell, self).__setattr__('_recorders', {})
        super(Cell, self).__setattr__('_recordings', {})
        self._controller.deregister_cell(self)

    def _initialise_local_recording(self):
        if not hasattr(self, '_recorders'):
            self.clear_recorders()
            self._controller.register_cell(self)

    def recording(self, variables=None, segnames=None, components=None,
                  in_block=False):
        """
        Gets a recording or recordings of previously recorded variable

        `variables`  -- the name of the variable or a list of names of
                        variables to return [str | list(str)]
        `segnames`   -- the segment name the variable is located or a list of
                        segment names (in which case length must match number
                        of variables) [str | list(str)]. "None" variables will
                        be translated to the 'source_section' segment
        `components` -- the component name the variable is part of or a list
                        of components names (in which case length must match
                        number of variables) [str | list(str)]. "None"
                        variables will be translated as segment variables
                        (i.e. no component)
        `in_block`   -- returns a neo.Block object instead of a neo.SpikeTrain
                        neo.AnalogSignal object (or list of for multiple
                        variable names)
        """
        return_single = False
        if variables is None:
            if segnames is None:
                raise Exception("As no variables were provided all recordings "
                                "will be returned, soit doesn't make sense to "
                                "provide segnames")
            if components is None:
                raise Exception("As no variables were provided all recordings "
                                "will be returned, so it doesn't make sense to"
                                " provide components")
            variables, segnames, components = zip(*self._recordings.keys())
        else:
            if isinstance(variables, basestring):
                variables = [variables]
                return_single = True
            if isinstance(segnames, basestring) or segnames is None:
                segnames = [segnames] * len(variables)
            if isinstance(components, basestring) or components is None:
                components = [components] * len(segnames)
        if in_block:
            segment = neo.Segment(rec_datetime=datetime.now())
        else:
            recordings = []
        for key in zip(variables, segnames, components):
            if key[0] == 'spikes':
                spike_train = neo.SpikeTrain(
                    self._recordings[key], t_start=0.0 * pq.ms,
                    t_stop=self._controller.dt * pq.ms, units='ms')
                if in_block:
                    segment.spiketrains.append(spike_train)
                else:
                    recordings.append(spike_train)
            else:
                if key[0] == 'v':
                    units = 'mV'
                else:
                    units = 'nA'
                try:
                    analog_signal = neo.AnalogSignal(
                        self._recordings[key],
                        sampling_period=self._controller.dt * pq.ms,
                        t_start=0.0 * pq.ms, units=units,
                        name='.'.join([x for x in key if x is not None]))
                except KeyError:
                    raise Pype9RuntimeError(
                        "No recording for '{}'{}{} in cell '{}'"
                        .format(key[0],
                                (" in component '{}'".format(key[2])
                                 if key[2] is not None else ''),
                                (" on segment '{}'".format(key[1])
                                 if key[1] is not None else ''),
                                self.name))
                if in_block:
                    segment.analogsignals.append(analog_signal)
                else:
                    recordings.append(analog_signal)
        if in_block:
            data = neo.Block(
                description="Recording from PyPe9 '{}' cell".format(self.name))
            data.segments = [segment]
            return data
        elif return_single:
            return recordings[0]
        else:
            return recordings

    # This has to go last to avoid clobbering the property decorators
    def property(self, name):
        return self._nineml.property(name)


class DummyNinemlModel(object):

    def __init__(self, name, url, model):
        self.name = name
        self.url = url
        self.model = model
        self.parameters = []
