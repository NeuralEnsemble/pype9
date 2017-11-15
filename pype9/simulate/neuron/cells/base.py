"""

  This package combines the common.ncml with existing pyNN classes

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
from __future__ import division
from builtins import zip
import collections
from itertools import chain
import operator
import numpy
import quantities as pq
import sympy
import neo
from ..code_gen import CodeGenerator
from neuron import h
from nineml import units as un
from nineml.abstraction import EventPort, Dynamics
from nineml.exceptions import NineMLNameError
from nineml.visitors import BaseVisitorWithContext
from math import pi
from pype9.simulate.common.cells import base
from pype9.simulate.neuron.units import UnitHandler
from pype9.simulate.neuron.simulation import Simulation
from pype9.annotations import (
    PYPE9_NS, BUILD_TRANS, MEMBRANE_CAPACITANCE, EXTERNAL_CURRENTS,
    MEMBRANE_VOLTAGE, MECH_TYPE, ARTIFICIAL_CELL_MECH)
from pype9.exceptions import (
    Pype9RuntimeError, Pype9UsageError, Pype9Unsupported9MLException)

basic_nineml_translations = {'Voltage': 'v', 'Diameter': 'diam', 'Length': 'L'}

NEURON_NS = 'NEURON'


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

    DEFAULT_CM = 1.0 * un.nF  # Chosen to match point processes (...I think).

    def __init__(self, *args, **kwargs):
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
            self.cm_param_name = None
        else:
            # In order to scale the distributed current to the same units as
            # point process current, i.e. mA/cm^2 -> nA the surface area needs
            # to be 100um. mA/cm^2 = -3-(-2^2) = 10^1, 100um^2 = 2 + -6^2 =
            # 10^(-10), nA = 10^(-9). 1 - 10 = - 9. (see PyNN Izhikevich neuron
            # implementation)
            self._sec.L = 10.0
            self._sec.diam = 10.0 / pi
            self.cm_param_name = self.build_component_class.annotations.get(
                (BUILD_TRANS, PYPE9_NS), MEMBRANE_CAPACITANCE)
            if self.cm_param_name not in self.component_class.parameter_names:
                # Set capacitance to capacitance of section to default value
                # for input currents
                # Set capacitance in NMODL
                setattr(self._hoc, self.cm_param_name,
                        float(self.DEFAULT_CM.in_units(un.nF)))
                # Set capacitance in HOC section
                specific_cm = self.DEFAULT_CM / self.surface_area
                self._sec.cm = float(specific_cm.in_units(un.uF / un.cm ** 2))
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
            sorted_ports = list(zip(
                *sorted(ports_n_indices, key=operator.itemgetter(0))))[1]
        else:
            sorted_ports = []
        self.type = collections.namedtuple('Type', 'receptor_types')(
            sorted_ports)
        # Call base init (needs to be after 9ML init)
        super(Cell, self).__init__(*args, **kwargs)
        if self.in_array:
            self._initial_states = {}
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
            object.__setattr__(self, '_regime_index', val)
        elif (varname.endswith('_init') and
              varname[:-5] in self.component_class.state_variable_names):
            if varname in chain(self.component_class.state_variable_names,
                                self.component_class.parameter_names):
                raise Pype9RuntimeError(
                    "Ambiguous variable '{}' can either be the initial state "
                    "of '{}' or a parameter/state-variable"
                    .format(varname, varname[:-5]))
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

    def initialize(self):
        if self.in_array:
            for k, v in self._initial_states.items():
                self._set(k, v)
            assert self._regime_index is not None
            self._set_regime()
        else:
            super(Cell, self).initialize()

    @property
    def surface_area(self):
        return (self._sec.L * un.um) * (self._sec.diam * pi * un.um)

    def _get(self, varname):
        varname = self._escaped_name(varname)
        try:
            return getattr(self._hoc, varname)
        except AttributeError:
            try:
                return getattr(self._sec, varname)
            except AttributeError:
                raise Pype9UsageError(
                    "'{}' doesn't have an attribute '{}'"
                    .format(self.name, varname))

    def _set(self, varname, val):
        try:
            setattr(self._hoc, varname, val)
            # If capacitance, also set the section capacitance
            if varname == self.cm_param_name:
                # This assumes that the value of the capacitance is in nF
                # which it should be from the super setattr method
                self._sec.cm = float((
                    val * un.nF / self.surface_area).in_units(un.uF /
                                                              un.cm ** 2))
        except LookupError:
            varname = self._escaped_name(varname)
            try:
                setattr(self._sec, varname, val)
            except AttributeError:
                # Check to see if parameter has been removed in build
                # transform and if not raise the error
                if varname not in self.component_class.parameter_names:
                    raise AttributeError(
                        "Could not set '{}' to hoc object or NEURON section"
                        .format(varname))

    def _set_regime(self):
        setattr(self._hoc, self.code_generator.REGIME_VARNAME, self._regime_index)

    def record(self, port_name, **kwargs):  # @UnusedVariable
        """
        Parameters
        ----------
        port_name : str
            Name of the port to record from
        v_thresh_tol : Quantity (voltage)
            A small voltage added to the threshold for determining emitted
            spikes. Used when there is a voltage reset after the time crossing
            that may cause the threshold to be missed.
        """
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
                    (BUILD_TRANS,
                     PYPE9_NS), MECH_TYPE) == ARTIFICIAL_CELL_MECH:
                self._recorders[port_name] = recorder = h.NetCon(
                    self._hoc, None, sec=self._sec)
            else:
                v_thresh = self.get_v_threshold(self._nineml, port.name)
                self._recorders[port_name] = recorder = h.NetCon(
                    self._sec(0.5)._ref_v, None, v_thresh, 0.0, 0.0,
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

    def record_regime(self):
        self._initialize_local_recording()
        self._recordings[
            self.code_generator.REGIME_VARNAME] = recording = h.Vector()
        recording.record(getattr(self._hoc, '_ref_{}'
                                 .format(self.code_generator.REGIME_VARNAME)))

    def recording(self, port_name, t_start=None):
        """
        Return recorded data as a dictionary containing one numpy array for
        each neuron, ids as keys.
        """
        if self.is_dead():
            t_stop = self._t_stop
        else:
            t_stop = self.Simulation.active().t
        if t_start is None:
            t_start = UnitHandler.to_pq_quantity(self._t_start)
        t_start = pq.Quantity(t_start, 'ms')
        t_stop = self.unit_handler.to_pq_quantity(t_stop)
        try:
            port = self.component_class.port(port_name)
        except NineMLNameError:
            port = self.component_class.state_variable(port_name)
        if isinstance(port, EventPort):
            events = numpy.asarray(self._recordings[port_name])
            recording = neo.SpikeTrain(
                self._trim_spike_train(events, t_start), t_start=t_start,
                t_stop=t_stop, units='ms')
        else:
            units_str = self.unit_handler.dimension_to_unit_str(
                port.dimension, one_as_dimensionless=True)
            interval = h.dt * pq.ms
            signal = numpy.asarray(self._recordings[port_name])
            recording = neo.AnalogSignal(
                self._trim_analog_signal(signal, t_start, interval),
                sampling_period=interval,
                t_start=t_start, units=units_str, name=port_name)
            recording = recording[:-1]  # Drop final timepoint
        return recording

    def _regime_recording(self):
        t_start = self.unit_handler.to_pq_quantity(self._t_start)
        return neo.AnalogSignal(
            self._recordings[self.code_generator.REGIME_VARNAME],
            sampling_period=h.dt * pq.ms,
            t_start=t_start, units='dimensionless',
            name=self.code_generator.REGIME_VARNAME)

    def reset_recordings(self):
        """
        Resets the recordings for the cell and the NEURON simulator (assumes
        that only one cell is instantiated)
        """
        for rec in self._recordings.values():
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

        Parameters
        ----------
        port_name : str
            The name of the receive port to play the signal into
        signal : neo.AnalogSignal (current) | neo.SpikeTrain
            Signal to play into the port
        properties : list(nineml.Property)
            The connection properties of the event port
        """
        ext_is = self.build_component_class.annotations.get(
            (BUILD_TRANS, PYPE9_NS), EXTERNAL_CURRENTS).split(',')
        port = self.component_class.port(port_name)
        if isinstance(port, EventPort):
            if len(list(self.component_class.event_receive_ports)) > 1:
                raise Pype9Unsupported9MLException(
                    "Multiple event receive ports ('{}') are not currently "
                    "supported".format("', '".join(
                        [p.name
                         for p in self.component_class.event_receive_ports])))
            if signal.t_start < 1.0:
                raise Pype9UsageError(
                    "Signal must start at or after 1 ms to handle delay in "
                    "neuron ({})".format(signal.t_start))
            times = numpy.asarray(signal.times.rescale(pq.ms)) - 1.0
            vstim = h.VecStim()
            vstim_times = h.Vector(times)
            vstim.play(vstim_times)
            vstim_con = h.NetCon(vstim, self._hoc, sec=self._sec)
            self._check_connection_properties(port_name, properties)
            if len(properties) > 1:
                raise NotImplementedError(
                    "Cannot handle more than one connection property per port")
            elif properties:
                vstim_con.weight[0] = self.unit_handler.scale_value(
                    properties[0].quantity)
            self._inputs['vstim'] = vstim
            self._input_auxs.extend((vstim_times, vstim_con))
        else:
            if port_name not in ext_is:
                raise Pype9Unsupported9MLException(
                    "Can only play into external current ports ('{}'), not "
                    "'{}' port.".format("', '".join(ext_is), port_name))
            iclamp = h.IClamp(0.5, sec=self._sec)
            iclamp.delay = 0.0
            iclamp.dur = 1e12
            iclamp.amp = 0.0
            iclamp_amps = h.Vector(pq.Quantity(signal, 'nA'))
            iclamp_times = h.Vector(signal.times.rescale(pq.ms))
            iclamp_amps.play(iclamp._ref_amp, iclamp_times)
            self._inputs['iclamp'] = iclamp
            self._input_auxs.extend((iclamp_amps, iclamp_times))

    def connect(self, sender, send_port_name, receive_port_name,
                delay=0.0 * un.ms, properties=None):
        """
        Connects a port of the cell to a matching port on the 'other' cell

        Parameters
        ----------
        sender : pype9.simulator.neuron.cells.Cell
            The sending cell to connect the from
        send_port_name : str
            Name of the port in the sending cell to connect to
        receive_port_name : str
            Name of the receive port in the current cell to connect from
        delay : nineml.Quantity (time)
            The delay of the connection
        properties : list(nineml.Property)
            The connection properties of the event port
        """
        send_port = sender.component_class.send_port(send_port_name)
        receive_port = self.component_class.receive_port(receive_port_name)
        delay = float(delay.in_units(un.ms))
        if properties is None:
            properties = []
        if send_port.communicates != receive_port.communicates:
            raise Pype9UsageError(
                "Cannot connect {} send port, '{}', to {} receive port, '{}'"
                .format(send_port.communicates, send_port_name,
                        receive_port.communicates, receive_port_name))
        if receive_port.communicates == 'event':
            if len(list(self.component_class.event_receive_ports)) > 1:
                raise Pype9Unsupported9MLException(
                    "Multiple event receive ports ('{}') are not currently "
                    "supported".format("', '".join(
                        [p.name
                         for p in self.component_class.event_receive_ports])))
            netcon = h.NetCon(sender._hoc, self._hoc, sec=self._sec)
            if delay:
                netcon.delay = delay
            self._check_connection_properties(receive_port_name, properties)
            if len(properties) > 1:
                raise Pype9Unsupported9MLException(
                    "Cannot handle more than one connection property per port")
            elif properties:
                netcon.weight[0] = self.unit_handler.scale_value(
                    properties[0].quantity)
            self._input_auxs.append(netcon)
        elif receive_port.communicates == 'analog':
            raise Pype9UsageError(
                "Cannot individually 'connect' analog ports. Simulate the "
                "sending cell in a separate simulation then play the analog "
                "signal in the port")
        else:
            raise Pype9UsageError(
                "Unrecognised port communication '{}'".format(
                    receive_port.communicates))

    def voltage_clamp(self, voltages, series_resistance=1e-3):
        """
        Clamps the voltage of a segment

        Parameters
        ----------
        voltage : neo.AnalogSignal (voltage)
            The voltages to clamp the segment to
        series_resistance : float (??)
            The series resistance of the voltage clamp
        """
        seclamp = h.SEClamp(0.5, sec=self._sec)
        seclamp.rs = series_resistance
        seclamp.dur1 = 1e12
        seclamp_amps = h.Vector(pq.Quantity(voltages, 'mV'))
        seclamp_times = h.Vector(voltages.times.rescale(pq.ms))
        seclamp_amps.play(seclamp._ref_amp, seclamp_times)
        self._inputs['seclamp'] = seclamp
        self._input_auxs.extend((seclamp_amps, seclamp_times))

    def _escaped_name(self, name):
        if name == self.component_class.annotations.get(
                (BUILD_TRANS, PYPE9_NS), MEMBRANE_VOLTAGE):
            name = self.build_component_class.annotations.get(
                (BUILD_TRANS, PYPE9_NS), MEMBRANE_VOLTAGE)
        return name

    @classmethod
    def get_v_threshold(self, dynamics_properties, port_name):
        """
        Returns the voltage threshold at which an event is emitted from the
        given event port

        Parameters
        ----------
        component_class : nineml.Dynamics
            The component class of the cell to find the v-threshold for
        port_name : str
            Name of the event send port to threshold
        """
        comp_class = (dynamics_properties.component_class.
                      _dynamics.substitute_aliases())
        transitions = OuputEventTransitionsFinder(
            comp_class, comp_class.event_send_port(port_name)).transitions
        assert transitions
        try:
            triggers = set(t.trigger for t in transitions)
        except AttributeError:
            raise Pype9UsageError(
                "Cannot get threshold for event port '{}' in {} as it is "
                "emitted from at least OnEvent transition ({})".format(
                    port_name, comp_class,
                    ', '.join(str(t) for t in transitions)))
        if len(triggers) > 1:
            raise Pype9UsageError(
                "Cannot get threshold for event port '{}' in {} as it is the "
                "condition from at least OnEvent transition ({})".format(
                    port_name, comp_class, ', '.join(transitions)))
        expr = next(iter(triggers)).rhs
        v = sympy.Symbol(self.component_class.annotations.get(
            (BUILD_TRANS, PYPE9_NS), MEMBRANE_VOLTAGE))
        if v not in expr.free_symbols:
            raise Pype9UsageError(
                "Trigger expression for '{}' port in {} is not an expression "
                "of membrane voltage '{}'".format(port_name, comp_class, v))
        solution = None
        if isinstance(expr, (sympy.StrictGreaterThan,
                             sympy.StrictLessThan)):
            # Get the equation for the transition between true and false
            equality = sympy.Eq(*expr.args)
            solutions = sympy.solvers.solve(equality, v)
            if len(solutions) == 1:
                solution = solutions[0]
        if solution is None:
            raise Pype9UsageError(
                "Cannot solve threshold equation for trigger expression '{}' "
                "for '{}' (to find condition where spikes are emitted from "
                "'{}' event send port) in {} as it is not a simple inequality"
                .format(expr, v, port_name, comp_class))
        values = {}
        for sym in solution.free_symbols:
            sym_str = str(sym)
            try:
                prop = dynamics_properties.property(sym_str)
            except NineMLNameError:
                try:
                    prop = comp_class.constant(sym_str)
                except NineMLNameError:
                    raise Pype9UsageError(
                        "Cannot calculated fixed value for voltage threshold "
                        "as it contains reference to {}".format(
                            comp_class.element(sym_str)))
            values[sym] = self.unit_handler.scale_value(prop.quantity)
        threshold = solution.subs(values)
        return float(threshold)


class CellMetaClass(base.CellMetaClass):

    """
    Metaclass for building NineMLCellType subclasses Called by
    nineml_celltype_from_model
    """

    _built_types = {}  # Stores previously created types for reuse
    CodeGenerator = CodeGenerator
    BaseCellClass = Cell
    Simulation = Simulation


class OuputEventTransitionsFinder(BaseVisitorWithContext):
    """
    Finds the transitions which emit an output event

    Parameters
    ----------
    component_class : Dynamics
        The component class to find the transitions from
    port : EventSendPort
        The event send port over which the events are emitted.
    """

    as_class = Dynamics

    def __init__(self, component_class, port):
        super(OuputEventTransitionsFinder, self).__init__()
        self._port = port
        self._transitions = []
        self.visit(component_class)

    @property
    def transitions(self):
        return self._transitions

    def action_outputevent(self, outputevent, **kwargs):  # @UnusedVariable @IgnorePep8
        if outputevent.port == self._port:
            self._transitions.append(self.context.parent)

    def default_action(self, obj, nineml_cls, **kwargs):
        pass
