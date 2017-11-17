"""

  This package combines the common.ncml with existing pyNN classes

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
import numpy
import neo
import nest
import quantities as pq
from nineml.exceptions import NineMLNameError
from nineml import units as un
from ..code_gen import CodeGenerator
from pype9.simulate.nest.simulation import Simulation
from pype9.simulate.common.cells import base
from pype9.annotations import PYPE9_NS, MEMBRANE_VOLTAGE, BUILD_TRANS
from pype9.exceptions import (
    Pype9UsageError, Pype9Unsupported9MLException)
from pype9.utils.logging import logger

basic_nineml_translations = {
    'Voltage': 'V_m', 'Diameter': 'diam', 'Length': 'L'}


class Cell(base.Cell):

    def __init__(self, *properties, **kwprops):
        self._flag_created(False)
        self._cell = nest.Create(self.__class__.name)
        super(Cell, self).__init__(*properties, **kwprops)
        self._receive_ports = nest.GetDefaults(
            self.__class__.name)['receptor_types']
        self._inputs = {}
        self._flag_created(True)

    def _get(self, varname):
        return nest.GetStatus(self._cell, keys=varname)[0]

    def _set(self, varname, value):
        nest.SetStatus(self._cell, varname, value)

    def _set_regime(self):
        nest.SetStatus(self._cell, self.code_generator.REGIME_VARNAME,
                       self._regime_index)

    def record(self, port_name, interval=None, **kwargs):  # @UnusedVariable @IgnorePep8
        # Create dictionaries for storing local recordings. These are not
        # created initially to save memory if recordings are not required or
        # handled externally
        self._initialize_local_recording()
        try:
            port = self.component_class.send_port(port_name)
        except NineMLNameError:
            try:
                # For convenient access to state variables
                port = self.component_class.state_variable(port_name)
            except NameError:
                raise NineMLNameError(
                    "No matching state variable or event send port matching "
                    "port name '{}' in component class '{}'".format(
                        port_name, self.component_class.name))
        if port.nineml_type in ('EventSendPort', 'EventSendPortExposure'):
            # FIXME: This assumes that all event send port are spikes, which
            #        I think is currently a limitation of NEST
            self._recorders[port_name] = recorder = nest.Create(
                "spike_detector", params={"precise_times": True})
            nest.Connect(self._cell, recorder)
        else:
            if interval is None:
                interval = Simulation.active().dt
            interval = float(interval.in_units(un.ms))
            variable_name = self.build_name(port_name)
            self._recorders[port_name] = recorder = nest.Create(
                'multimeter', 1, {"interval": interval})
            nest.SetStatus(recorder, {'record_from': [variable_name]})
            nest.Connect(
                recorder, self._cell,
                syn_spec={'delay': self.device_delay_ms})

    def record_regime(self, interval=None):
        self._initialize_local_recording()
        if interval is None:
            interval = Simulation.active().dt
        interval = float(interval.in_units(un.ms))
        self._recorders[
            self.code_generator.REGIME_VARNAME] = recorder = nest.Create(
            'multimeter', 1, {"interval": interval})
        nest.SetStatus(recorder,
                       {'record_from': [self.code_generator.REGIME_VARNAME]})
        nest.Connect(
            recorder, self._cell,
            syn_spec={'delay': self.device_delay_ms})

    def recording(self, port_name, t_start=None):
        """
        Return recorded data as a dictionary containing one numpy array for
        each neuron, ids as keys.
        """
        # NB: Port could also be a state variable
        try:
            port = self.component_class.send_port(port_name)
        except NineMLNameError:
            # For convenient access to state variables
            port = self.component_class.state_variable(port_name)
        if self.is_dead():
            t_stop = self._t_stop
        else:
            t_stop = self.Simulation.active().t
        if t_start is None:
            t_start = self.unit_handler.to_pq_quantity(self._t_start)
        t_start = pq.Quantity(t_start, 'ms')
        t_stop = self.unit_handler.to_pq_quantity(t_stop)
        if port.nineml_type in ('EventSendPort', 'EventSendPortExposure'):
            spikes = nest.GetStatus(
                self._recorders[port_name], 'events')[0]['times']
            data = neo.SpikeTrain(
                self._trim_spike_train(spikes * pq.ms, t_start),
                t_start=t_start, t_stop=t_stop, name=port_name)
        else:
            port_name = self.build_name(port_name)
            events, interval = nest.GetStatus(self._recorders[port_name],
                                              ('events', 'interval'))[0]
            try:
                port = self._nineml.component_class.port(port_name)
            except NineMLNameError:
                port = self._nineml.component_class.state_variable(port_name)
            unit_str = self.unit_handler.dimension_to_unit_str(
                port.dimension, one_as_dimensionless=True)
            variable_name = self.build_name(port_name)
            signal = self._trim_analog_signal(events[variable_name],
                                              t_start, interval * pq.ms)
            data = neo.AnalogSignal(
                signal, sampling_period=interval * pq.ms,
                t_start=t_start, units=unit_str, name=port_name)
        return data

    def _regime_recording(self):
        events, interval = nest.GetStatus(
            self._recorders[self.code_generator.REGIME_VARNAME],
            ('events', 'interval'))[0]
        return neo.AnalogSignal(
            events[self.code_generator.REGIME_VARNAME],
            sampling_period=interval * pq.ms, units='dimensionless',
            t_start=self.unit_handler.to_pq_quantity(self._t_start),
            name=self.code_generator.REGIME_VARNAME)

    def build_name(self, varname):
        # Get mapped port name if port corresponds to membrane voltage
        if varname == self.component_class.annotations.get(
                (BUILD_TRANS, PYPE9_NS), MEMBRANE_VOLTAGE, default=None):
            varname = self.build_component_class.annotations.get(
                (BUILD_TRANS, PYPE9_NS), MEMBRANE_VOLTAGE)
        return varname

    def reset_recordings(self):
        logger.warning("Haven't worked out how to implement reset recordings "
                       "for NEST yet")

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
        port = self.component_class.receive_port(port_name)
        if port.nineml_type in ('EventReceivePort',
                                'EventReceivePortExposure'):
            # Shift the signal times to account for the minimum delay and
            # match the NEURON implementation
            spike_times = (numpy.asarray(signal.rescale(pq.ms)) -
                           self.device_delay_ms)
            if any(spike_times <= 0.0):
                raise Pype9UsageError(
                    "Some spike times are less than device delay and so "
                    "can't be played into cell ({})".format(', '.join(
                        spike_times <
                        self.device_delay_ms)))
            self._inputs[port_name] = nest.Create(
                'spike_generator', 1, {'spike_times': list(spike_times)})
            syn_spec = {'receptor_type': self._receive_ports[port_name],
                        'delay': self.device_delay_ms}
            self._check_connection_properties(port_name, properties)
            if len(properties) > 1:
                raise NotImplementedError(
                    "Cannot handle more than one connection property per port")
            elif properties:
                syn_spec['weight'] = self.unit_handler.scale_value(
                    properties[0].quantity)
            nest.Connect(self._inputs[port_name], self._cell,
                         syn_spec=syn_spec)
        elif port.nineml_type in ('AnalogReceivePort', 'AnalogReducePort',
                                  'AnalogReceivePortExposure',
                                  'AnalogReducePortExposure'):
            # Signals are played into NEST cells include a delay (set to be the
            # minimum), which is is subtracted from the start of the signal so
            # that the effect of the signal aligns with other simulators
            t_start = (float(signal.t_start.rescale(pq.ms)) -
                       self.device_delay_ms)
            if t_start <= 0.0:
                raise Pype9UsageError(
                    "Start time of signal played into port '{}' ({}) must "
                    "be greater than device delay ({})".format(
                        port_name, signal.t_start, self.device_delay))
            step_current_params = {
                 'amplitude_values': list(
                    numpy.ravel(pq.Quantity(signal, 'pA'))),
                 'amplitude_times': list(numpy.ravel(numpy.asarray(
                     signal.times.rescale(pq.ms))) - self.device_delay_ms),
                 'start': t_start,
                 'stop': float(signal.t_stop.rescale(pq.ms))}
            self._inputs[port_name] = nest.Create(
                'step_current_generator', 1, step_current_params)
            nest.Connect(self._inputs[port_name], self._cell, syn_spec={
                "receptor_type": self._receive_ports[port_name],
                'delay': self.device_delay_ms})
        else:
            raise Pype9UsageError(
                "Unrecognised port type '{}' to play signal into".format(port))

    def connect(self, sender, send_port_name, receive_port_name, delay=None,
                properties=None):
        """
        Connects a port of the cell to a matching port on the 'other' cell

        Parameters
        ----------
        sender : pype9.simulator.nest.cells.Cell
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
        if delay is None:
            delay = self.device_delay
        if properties is None:
            properties = []
        delay = float(delay.in_units(un.ms))
        send_port = sender.component_class.send_port(send_port_name)
        receive_port = self.component_class.receive_port(receive_port_name)
        if send_port.communicates != receive_port.communicates:
            raise Pype9UsageError(
                "Cannot connect {} send port, '{}', to {} receive port, '{}'"
                .format(send_port.communicates, send_port_name,
                        receive_port.communicates, receive_port_name))
        if receive_port.communicates == 'event':
            if self.component_class.num_event_send_ports > 1:
                raise Pype9Unsupported9MLException(
                    "Cannot currently differentiate between multiple event "
                    "send ports in NEST implementation ('{}')".format(
                        "', '".join(
                            self.component_class.event_send_port_names)))
            syn_spec = {'receptor_type':
                        self._receive_ports[receive_port_name],
                        'delay': delay}
            if len(properties) > 1:
                raise Pype9Unsupported9MLException(
                    "Cannot handle more than one connection property per port")
            elif properties:
                self._check_connection_properties(receive_port_name,
                                                  properties)
                syn_spec['weight'] = self.unit_handler.scale_value(
                    properties[0].quantity)
            nest.Connect(sender._cell, self._cell, syn_spec=syn_spec)
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
        raise NotImplementedError("voltage clamps are not supported for "
                                  "Pype9->NEST at this stage.")

    @property
    def device_delay(self):
        return Simulation.active().device_delay

    @property
    def device_delay_ms(self):
        return Simulation.active().device_delay_ms


class CellMetaClass(base.CellMetaClass):

    _built_types = {}  # Stores previously created types for reuse
    CodeGenerator = CodeGenerator
    BaseCellClass = Cell
    Simulation = Simulation
