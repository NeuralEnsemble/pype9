"""

  This package combines the common.ncml with existing pyNN classes

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
from datetime import datetime
import weakref
import numpy
# MPI may not be required but NEURON sometimes needs to be initialised after
# MPI so I am doing it here just to be safe (and to save me headaches in the
# future)
try:
    from mpi4py import MPI  # @UnusedImport @IgnorePep8 This is imported before NEURON to avoid a bug in NEURON
except ImportError:
    pass
from neuron import h, nrn, load_mechanisms
import neo
import quantities as pq
import nineml
import os.path
from pype9.cells.code_gen.neuron import CodeGenerator
from pype9.cells.tree import (
    in_units, IonConcentrationModel)
from ... import create_unit_conversions, convert_units
from pyNN.neuron.cells import VectorSpikeSource
from itertools import chain
from .. import base
from pype9.utils import convert_to_property, convert_to_quantity

basic_nineml_translations = {'Voltage': 'v', 'Diameter': 'diam', 'Length': 'L'}

import logging

logger = logging.getLogger("NineLine")


_basic_SI_to_neuron_conversions = (('s', 'ms'),
                                   ('V', 'mV'),
                                   ('A', 'nA'),
                                   ('S', 'uS'),
                                   ('F', 'nF'),
                                   ('m', 'um'),
                                   ('Hz', 'Hz'),
                                   ('Ohm', 'MOhm'),
                                   ('M', 'mM'))

_compound_SI_to_neuron_conversions = (((('A', 1), ('m', -2)),
                                       (('mA', 1), ('cm', -2))),
                                      ((('F', 1), ('m', -2)),
                                       (('uF', 1), ('cm', -2))),
                                      ((('S', 1), ('m', -2)),
                                       (('S', 1), ('cm', -2))),
                                      ((('Ohm', 1), ('m', 1)),
                                       (('Ohm', 1), ('cm', 1))))


_basic_unit_dict, _compound_unit_dict = create_unit_conversions(
    _basic_SI_to_neuron_conversions, _compound_SI_to_neuron_conversions)


def convert_to_neuron_units(value, unit_str):
    return convert_units(
        value, unit_str, _basic_unit_dict, _compound_unit_dict)


class Cell(base.Cell):

    def __init__(self, *properties, **kwprops):
        """
        `propertes/kwprops` --  Can accept a single parameter, which is a
                                dictionary of parameters or kwarg parameters,
                                or a list of nineml.Property objects
        """
        if len(properties) == 1 and isinstance(properties, dict):
            kwprops.update(properties)
            properties = []
        for name, qty in kwprops.iteritems():
            properties.append(convert_to_property(name, qty))
        self._nineml = nineml.user_layer.Dynamics(
            self.default_parameters.name,
            self.default_parameters, properties)
        base.Cell.__init__(self)
        # Construct all the NEURON structures
        self.source_section = self
        self.nrn_object = getattr(h, self.componentclass.name)(0.5, sec=self)
        # Setup variables required by pyNN
        self.source = self.source_section(0.5)._ref_v
        # for recording Once NEST supports sections, it might be an idea to
        # drop this in favour of a more explicit scheme
        self.recordable = {'spikes': None, 'v': self.source_section._ref_v}
        self.spike_times = h.Vector(0)
        self.traces = {}
        self.gsyn_trace = {}
        self.recording_time = 0
        self.rec = h.NetCon(self.source, None, sec=self.source_section)
        # Set up references from parameter names to internal variables and set
        # parameters
        for prop in self.properties:
            self.set(prop)

    def get_threshold(self):
        return in_units(self._model.spike_threshold, 'mV')

    def memb_init(self):
        if 'initial_v' in self.parameters:
            for seg in self.segments.itervalues():
                seg.v = self.parameters['initial_v']
        for param in self._parameters.itervalues():
            if isinstance(param, self.InitialState):
                param.initialize_state()

    def __getattr__(self, varname):
        """
        To support the access to components on particular segments in PyNN the
        segment name can be prepended enclosed in curly brackets (i.e. '{}').

        @param var [str]: var of the attribute, with optional segment segment
                          name enclosed with {} and prepended
        """
        if varname.startswith('prop.'):
            varname = varname[5:]
        try:
            return convert_to_quantity(self._nineml.property(varname))
        except KeyError:
            raise AttributeError(varname)

    def __setattr__(self, varname, val):
        """
        Any '.'s in the attribute var are treated as delimeters of a nested
        varspace lookup. This is done to allow pyNN's population.tset method to
        set attributes of cell components.

        @param var [str]: var of the attribute or '.' delimeted string of
                          segment, component and attribute vars
        @param val [*]: val of the attribute
        """
        if varname.startswith('prop.'):
            varname = varname[5:]
        if varname in self._nineml.property_names:
            nineml.Dynamics.set(self, convert_to_property(varname, val))
            setattr(self.nrn_object, varname + self._suffix,
                    convert_to_neuron_units(val))
        else:
            super(Cell, self).__setattr__(varname, val)

    def __dir__(self):
        return set(chain(dir(super(Cell, self)), self.property_names))

    def record(self, variable):
        self._record(self.source_section, variable, key=variable)

    def _record(self, seg, variable, key):
        self._initialise_local_recording()
        if variable == 'spikes':
            self._recorders[key] = recorder = h.NetCon(
                seg._ref_v, None, self.get_threshold(), 0.0, 1.0, sec=seg)
            self._recordings[key] = recording = h.Vector()
            recorder.record(recording)
        else:
            pointer = nrn.Section.__getattr__(seg, '_ref_' + variable)
            self._recordings[key] = recording = h.Vector()
            recording.record(pointer)

    def get_recording(self, variables=None, segnames=None, components=None,
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
                    t_stop=h.t * pq.ms, units='ms')
                if in_block:
                    segment.spiketrains.append(spike_train)
                else:
                    recordings.append(spike_train)
            else:
                if key[0] == 'v':
                    units = 'mV'
                else:
                    units = 'nA'
                analog_signal = neo.AnalogSignal(
                    self._recordings[key], sampling_period=h.dt * pq.ms,
                    t_start=0.0 * pq.ms, units=units,
                    name='.'.join([x for x in key if x is not None]))
                if in_block:
                    segment.analogsignals.append(analog_signal)
                else:
                    recordings.append(analog_signal)
        if in_block:
            data = neo.Block(description="Recording from NineLine stand-alone "
                                         "cell")
            data.segments = [segment]
            return data
        elif return_single:
            return recordings[0]
        else:
            return recordings

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
        self._recorders = {}
        self._recordings = {}

    def _initialise_local_recording(self):
        if not hasattr(self, '_recorders'):
            self._recorders = {}
            self._recordings = {}
            simulation_controller.register_cell(self)

    @property
    def properties(self):
        """
        The set of componentclass properties (parameter values).
        """
        return self._nineml.properties

    @property
    def property_names(self):
        return self._nineml.property_names

    def set(self, prop):
        self._nineml.set(prop)

    @property
    def attributes_with_units(self):
        return self._nineml.attributes_with_units

    def __repr__(self):
        return ('NeuronCell(name="%s", componentclass="%s")' %
                (self.__class__.__name__, self.name,
                 self.component_class.name))

    def to_xml(self):
        return self._nineml.to_xml()

    @property
    def used_units(self):
        return self._nineml.used_units

    def write(self, file):  # @ReservedAssignment
        self._nineml.write(file)

    # This has to go last to avoid clobbering the property decorators
    def property(self, name):
        return self._nineml.property(name)


class CellMetaClass(base.CellMetaClass):

    """
    Metaclass for building NineMLCellType subclasses Called by
    nineml_celltype_from_model
    """

    _built_types = {}
    CodeGenerator = CodeGenerator
    BaseCellClass = Cell

    @classmethod
    def load_model(cls, name, install_dir):  # @UnusedVariable @NoSelf
        load_mechanisms(os.path.dirname(install_dir))


# This is adapted from the code for the simulation controller in PyNN for
# use with individual cell objects
class _SimulationController(object):

    def __init__(self):
        self.running = False
        self.registered_cells = []
        self._time = h.Vector()

    @property
    def time(self):
        return pq.Quantity(self._time, 'ms')

    def register_cell(self, cell):
        self.registered_cells.append(weakref.ref(cell))

    def run(self, simulation_time, reset=True, timestep='cvode', rtol=None,
            atol=None):
        """
        Run the simulation for a certain time.
        """
        self._time.record(h._ref_t)
        if timestep == 'cvode':
            self.cvode = h.CVode()
            if rtol is not None:
                self.cvode.rtol = rtol
            if atol is not None:
                self.cvode.atol = atol
        else:
            h.dt = timestep
        if reset or not self.running:
            self.running = True
            self.reset()
        # Convert simulation time to float value in ms
        simulation_time = float(pq.Quantity(simulation_time, 'ms'))
        for _ in numpy.arange(h.dt, simulation_time + h.dt, h.dt):
            h.fadvance()
        self.tstop += simulation_time

    def reset(self):
        h.finitialize(-65.0)
        for cell_ref in reversed(self.registered_cells):
            if cell_ref():
                cell_ref().memb_init()
                cell_ref().reset_recordings()
            else:
                # If the cell has been deleted remove the weak reference to it
                self.registered_cells.remove(cell_ref)
        self.tstop = 0

# Make a singleton instantiation of the simulation controller
simulation_controller = _SimulationController()
del _SimulationController
