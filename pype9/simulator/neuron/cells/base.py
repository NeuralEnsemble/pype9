"""

  This package combines the common.ncml with existing pyNN classes

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
# MPI may not be required but NEURON sometimes needs to be initialized after
# MPI so I am doing it here just to be safe (and to save me headaches in the
# future)
try:
    from mpi4py import MPI  # @UnusedImport @IgnorePep8 This is imported before NEURON to avoid a bug in NEURON
except ImportError:
    pass
import os.path
import collections
from itertools import chain
import operator
import quantities as pq
import neo
from .code_gen import CodeGenerator, REGIME_VARNAME
from neuron import h, load_mechanisms
from nineml import units as un
from nineml.abstraction import EventPort
from nineml.exceptions import NineMLNameError
from math import pi
import numpy
from pype9.simulator.base.cells import base
from pype9.simulator.neuron.units import UnitHandler
from pype9.simulator.neuron.simulation import Simulation
from pype9.annotations import (
    PYPE9_NS, BUILD_TRANS, MEMBRANE_CAPACITANCE, EXTERNAL_CURRENTS,
    MEMBRANE_VOLTAGE, MECH_TYPE, ARTIFICIAL_CELL_MECH)
from pype9.exceptions import Pype9RuntimeError
import logging

basic_nineml_translations = {'Voltage': 'v', 'Diameter': 'diam', 'Length': 'L'}

NEURON_NS = 'NEURON'

logger = logging.getLogger("PyPe9")


class Cell(base.Cell):
    """
    Base class for Neuron cell objects.

    Parameters
    ----------
    properties : list(nineml.Property)
        Can accept a single property, which is a dictionary of properties
        or a list of nineml.Property objects
    kwargs : dict(str, nineml.Property)
        A dictionary of properties
    """

    V_INIT_DEFAULT = -65.0

    UnitHandler = UnitHandler
    Simulation = Simulation

    def __init__(self, *properties, **kwprops):
        self._flag_created(False)
        # Construct all the NEURON structures
        self._sec = h.Section()  # @UndefinedVariable
        # Insert dynamics mechanism (the built component class)
        HocClass = getattr(h, self.__class__.name)
        self._hoc = HocClass(0.5, sec=self._sec)
        # A recordable of 'spikes' is needed for PyNN compatibility
        self.recordable = {'spikes': None}
        # Add a recordable entry for each event send ports
        # TODO: These ports aren't able to be recorded from at present because
        #       different event ports are not distinguishable in Neuron (well
        #       not easily anyway). Users should use 'spikes' instead for now
        for port in chain(self.component_class.event_send_ports):
            self.recordable[port.name] = None
        for port in chain(self.component_class.analog_send_ports,
                          self.component_class.state_variables):
            if port.name != self.component_class.annotations.get(
                    (BUILD_TRANS, PYPE9_NS), MEMBRANE_VOLTAGE, default=None):
                self.recordable[port.name] = getattr(
                    self._hoc, '_ref_' + port.name)
        # Get the membrane capacitance property if not an artificial cell
        if self.build_component_class.annotations.get(
                (BUILD_TRANS, PYPE9_NS), MECH_TYPE) == ARTIFICIAL_CELL_MECH:
            self.cm_prop_name = None
        else:
            # In order to scale the distributed current to the same units as
            # point process current, i.e. mA/cm^2 -> nA the surface area needs
            # to be 100um. mA/cm^2 = -3-(-2^2) = 10^1, 100um^2 = 2 + -6^2 =
            # 10^(-10), nA = 10^(-9). 1 - 10 = - 9. (see PyNN Izhikevich neuron
            # implementation)
            self._sec.L = 10.0
            self._sec.diam = 10.0 / pi
            self.cm_prop_name = self.build_component_class.annotations.get(
                (BUILD_TRANS, PYPE9_NS), MEMBRANE_CAPACITANCE)
            cm_prop = None
            try:
                try:
                    cm_prop = properties[0][self.cm_prop_name]
                except IndexError:
                    cm_prop = kwprops[self.cm_prop_name] * un.nF
            except KeyError:
                if self.build_properties is not None:
                    cm_prop = self.build_properties.property(self.cm_prop_name)
            if cm_prop is not None:
                cm = pq.Quantity(UnitHandler.to_pq_quantity(cm_prop), 'nF')
            else:
                cm = 1.0 * pq.nF
            # Set capacitance in mechanism
            setattr(self._hoc, self.cm_prop_name, float(cm))
            # Set capacitance in hoc
            specific_cm = pq.Quantity(cm / self.surface_area, 'uF/cm^2')
            self._sec.cm = float(specific_cm)
            self.recordable[self.component_class.annotations.get(
                (BUILD_TRANS, PYPE9_NS),
                MEMBRANE_VOLTAGE)] = self.source_section(0.5)._ref_v
        # Set up members required for PyNN
        self.spike_times = h.Vector(0)
        self.traces = {}
        self.gsyn_trace = {}
        self.recording_time = 0
        self.rec = h.NetCon(self.source, None, sec=self._sec)
        self._inputs = {}
        self._input_auxs = []
#         self.initial_v = self.V_INIT_DEFAULT
        # Get a mapping of receptor names to NMODL indices for PyNN projection
        # connection
        assert (set(self.build_component_class.event_receive_port_names) ==
                set(self.component_class.event_receive_port_names))
        # Need to use the build_component_class to get the same index as was
        # used to construct the indices
        # FIXME: These indices will need to be saved somewhere in the
        #        annotations of the build class so they can be reloaded
        if self.build_component_class.num_event_receive_ports:
            ports_n_indices = [
                (self.build_component_class.index_of(p), p.name)
                for p in self.build_component_class.event_receive_ports]
            # Get event receive ports sorted by the indices
            sorted_ports = zip(
                *sorted(ports_n_indices, key=operator.itemgetter(0)))[1]
        else:
            sorted_ports = []
        self.type = collections.namedtuple('Type', 'receptor_types')(
            sorted_ports)
        # Call base init (needs to be after 9ML init)
        super(Cell, self).__init__(*properties, **kwprops)
        self._flag_created(True)

    @property
    def name(self):
        return self.prototype.name

    @property
    def source_section(self):
        """
        A property used when treated as a PyNN standard model
        """
        return self._sec

    @property
    def source(self):
        """
        A property used when treated as a PyNN standard model
        """
        return self._hoc

    def __dir__(self):
        return (super(Cell, self).__dir__() +
                list(self.event_receive_port_names))

    def __setattr__(self, varname, val):
        # Capture attributes ending with '_init' (the convention PyNN uses to
        # specify initial conditions of state variables) and save them in
        # initial states
        if varname == '_regime_init':
            object.__setattr__(self, '_initial_regime', val)
        elif (varname.endswith('_init') and
              varname[:-5] in self.component_class.state_variable_names):
            if varname in chain(self.component_class.state_variable_names,
                                self.component_class.parameter_names):
                raise Pype9RuntimeError(
                    "Ambiguous variable '{}' can either be the initial state "
                    "of '{}' or a parameter/state-variable"
                    .format(varname, varname[:-5]))
            if self._initial_states is None:
                object.__setattr__(self, '_initial_states', {})
            self._initial_states[varname[:-5]] = val
        elif varname in ('record_times', 'recording_time'):
            # PyNN needs to be able to set 'record_times' and 'recording_time'
            # to record state variables
            object.__setattr__(self, varname, val)
        else:
            super(Cell, self).__setattr__(varname, val)

    def __getattr__(self, varname):
        if varname in self.event_receive_port_names:
            # Return the hoc object for projection connections
            return self._hoc
        else:
            return super(Cell, self).__getattr__(varname)

    def memb_init(self):
        """
        Wrapper to redirect PyNN initialisation to the 'initialize' method
        """
        self.initialize()

    @property
    def surface_area(self):
        return (self._sec.L * pq.um) * (self._sec.diam * pi * pq.um)

    def _get(self, varname):
        varname = self._escaped_name(varname)
        try:
            return getattr(self._hoc, varname)
        except AttributeError:
            try:
                return getattr(self._sec, varname)
            except AttributeError:
                assert False

    def _set(self, varname, val):
        try:
            setattr(self._hoc, varname, val)
            # If capacitance, also set the section capacitance
            if varname == self.cm_prop_name:
                # This assumes that the value of the capacitance is in nF
                # which it should be from the super setattr method
                self._sec.cm = float(
                    pq.Quantity(val * pq.nF / self.surface_area, 'uF/cm^2'))
        except LookupError:
            varname = self._escaped_name(varname)
            setattr(self._sec, varname, val)

    def _set_regime(self, index):
        setattr(self._hoc, REGIME_VARNAME, index)

    def record(self, port_name):
        self._initialize_local_recording()
        # Get the port or state variable to record
        try:
            port = self.component_class.send_port(port_name)
        except NineMLNameError:
            port = self.component_class.state_variable(port_name)
        # Set up Hoc vector to hold the recording
        self._recordings[port_name] = recording = h.Vector()
        if isinstance(port, EventPort):
            if self.build_component_class.annotations.get(
                    (BUILD_TRANS, PYPE9_NS), MECH_TYPE) == ARTIFICIAL_CELL_MECH:
                self._recorders[port_name] = recorder = h.NetCon(
                    self._hoc, None, sec=self._sec)
            else:
                logger.warning("Assuming '{}' is voltage threshold crossing"
                               .format(port_name))
                self._recorders[port_name] = recorder = h.NetCon(
                    self._sec._ref_v, None, self.get_threshold(), 0.0, 1.0,
                    sec=self._sec)
            recorder.record(recording)
        else:
            escaped_port_name = self._escaped_name(port_name)
            try:
                self._recorders[port_name] = recorder = getattr(
                    self._hoc, '_ref_' + escaped_port_name)
            except AttributeError:
                self._recorders[port_name] = recorder = getattr(
                    self._sec(0.5), '_ref_' + escaped_port_name)
            recording.record(recorder)

    def record_transitions(self):
        self._initialize_local_recording()
        self._recordings['__REGIME__'] = recording = h.Vector()
        recording.record(getattr(self._hoc, '_ref_regime_'))

    def recording(self, port_name):
        """
        Return recorded data as a dictionary containing one numpy array for
        each neuron, ids as keys.
        """
        try:
            port = self.component_class.port(port_name)
        except NineMLNameError:
            port = self.component_class.state_variable(port_name)
        if isinstance(port, EventPort):
            recording = neo.SpikeTrain(
                self._recordings[port_name], t_start=0.0 * pq.ms,
                t_stop=h.t * pq.ms, units='ms')
        else:
            units_str = UnitHandler.dimension_to_unit_str(port.dimension)
            recording = neo.AnalogSignal(
                self._recordings[port_name], sampling_period=h.dt * pq.ms,
                t_start=0.0 * pq.ms, units=units_str, name=port_name)
        return recording

    def transitions(self):
        try:
            recording = numpy.array(self._recordings['__REGIME__'], dtype=int)
        except KeyError:
            raise Pype9RuntimeError(
                "Transitions not recorded, call 'record_transitions' before "
                "simulation")
        cc = self.build_component_class
        index_map = dict((cc.index_of(r), r.name) for r in cc.regimes)
        transition_inds = (
            numpy.nonzero((recording[1:] != recording[:-1]))[0]) + 1
        transitions = [(0 * pq.ms, index_map[recording[0]])]
        transitions.extend(
            (i * h.dt * pq.ms, index_map[recording[i]])
            for i in transition_inds)
        return transitions

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
        super(Cell, self).clear_recorders()
        super(base.Cell, self).__setattr__('_recordings', {})

    def play(self, port_name, signal, properties=[]):
        """
        Injects current into the segment

        `port_name` -- the name of the receive port to play the signal into
        `signal`    -- a neo.AnalogSignal or neo.SpikeTrain to play into the
                       port
        `weight`    -- a tuple of (port_name, value/qty) to set the weight of
                       the event port.
        """
        ext_is = self.build_component_class.annotations.get(
            (BUILD_TRANS, PYPE9_NS), EXTERNAL_CURRENTS).split(',')
        try:
            port = self.component_class.port(port_name)
        except KeyError:
            raise Pype9RuntimeError(
                "Cannot play into unrecognised port '{}'".format(port_name))
        if isinstance(port, EventPort):
            if len(list(self.component_class.event_receive_ports)) > 1:
                raise NotImplementedError(
                    "Multiple event receive ports ('{}') are not currently "
                    "supported".format("', '".join(
                        [p.name
                         for p in self.component_class.event_receive_ports])))
            vstim = h.VecStim()
            vstim_times = h.Vector(pq.Quantity(signal, 'ms'))
            vstim.play(vstim_times)
            vstim_con = h.NetCon(vstim, self._hoc, sec=self._sec)
            self._check_connection_properties(port_name, properties)
            if len(properties) > 1:
                raise NotImplementedError(
                    "Cannot handle more than one connection property per port")
            elif properties:
                vstim_con.weight[0] = self.UnitHandler.scale_value(
                    properties[0].quantity)
            self._inputs['vstim'] = vstim
            self._input_auxs.extend((vstim_times, vstim_con))
        else:
            if port_name not in ext_is:
                raise NotImplementedError(
                    "Can only play into external current ports ('{}'), not "
                    "'{}' port.".format("', '".join(ext_is), port_name))
            iclamp = h.IClamp(0.5, sec=self._sec)
            iclamp.delay = 0.0
            iclamp.dur = 1e12
            iclamp.amp = 0.0
            iclamp_amps = h.Vector(pq.Quantity(signal, 'nA'))
            iclamp_times = h.Vector(pq.Quantity(signal.times, 'ms'))
            iclamp_amps.play(iclamp._ref_amp, iclamp_times)
            self._inputs['iclamp'] = iclamp
            self._input_auxs.extend((iclamp_amps, iclamp_times))

    def voltage_clamp(self, voltages, series_resistance=1e-3):
        """
        Clamps the voltage of a segment

        `voltage` -- a vector containing the voltages to clamp the segment
                     to [neo.AnalogSignal]
        """
        seclamp = h.SEClamp(0.5, sec=self._sec)
        seclamp.rs = series_resistance
        seclamp.dur1 = 1e12
        seclamp_amps = h.Vector(pq.Quantity(voltages, 'mV'))
        seclamp_times = h.Vector(pq.Quantity(voltages.times, 'ms'))
        seclamp_amps.play(seclamp._ref_amp, seclamp_times)
        self._inputs['seclamp'] = seclamp
        self._input_auxs.extend((seclamp_amps, seclamp_times))

    def _escaped_name(self, name):
        if name == self.component_class.annotations.get(
                (BUILD_TRANS, PYPE9_NS), MEMBRANE_VOLTAGE):
            name = self.build_component_class.annotations.get(
                (BUILD_TRANS, PYPE9_NS), MEMBRANE_VOLTAGE)
        return name


class CellMetaClass(base.CellMetaClass):

    """
    Metaclass for building NineMLCellType subclasses Called by
    nineml_celltype_from_model
    """

    _built_types = {}
    CodeGenerator = CodeGenerator
    BaseCellClass = Cell

    @classmethod
    def load_libraries(cls, _, install_dir):
        load_mechanisms(os.path.dirname(install_dir))
