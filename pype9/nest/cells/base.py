"""

  This package combines the common.ncml with existing pyNN classes

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
import sys
import os.path
from itertools import chain
import neo
import nest
import quantities as pq
import nineml
from .code_gen import CodeGenerator
from .controller import simulation_controller
from pype9.common.cells import base
from pype9.annotations import PYPE9_NS, MEMBRANE_VOLTAGE


basic_nineml_translations = {
    'Voltage': 'V_m', 'Diameter': 'diam', 'Length': 'L'}


class Cell(base.Cell):

    _controller = simulation_controller

    def __init__(self, *properties, **kwprops):
        super(Cell, self).__setattr__('_created', False)
        self._cell = nest.Create(self.__class__.name)
        super(Cell, self).__init__(*properties, **kwprops)
        self._receive_ports = nest.GetDefaults(
            self.__class__.name)['receptor_types']
        self._created = True

    def __getattr__(self, varname):
        if (self._created and varname in chain(
                self.property_names, self.state_variable_names)):
            return nest.GetStatus(self._cell, keys=varname)[0]
        else:
            raise AttributeError("'{}' cell class does not have parameter '{}'"
                                 .format(self.componentclass.name, varname))

    def __setattr__(self, varname, value):
        if (self._created and varname in chain(
                self.property_names, self.state_variable_names)):
            nest.SetStatus(self._cell, varname, value)
        else:
            super(Cell, self).__setattr__(varname, value)

    def set(self, prop):
        super(Cell, self).set(prop)
        # FIXME: need to convert to NEST units!!!!!!!!!!!
        nest.SetStatus(self._cell, prop.name, prop.value)

    def record(self, variable, interval=None):
        # TODO: Need to translate variable to port
        if interval is None:
            interval = simulation_controller.dt
        self._initialise_local_recording()
        if variable == self.componentclass.annotations[
                PYPE9_NS][MEMBRANE_VOLTAGE]:
            variable = self.build_componentclass.annotations[
                PYPE9_NS][MEMBRANE_VOLTAGE]
        self._recorders[variable] = recorder = nest.Create(
            'multimeter', 1, {"interval": interval})
        nest.SetStatus(recorder, {'record_from': [variable]})
        nest.Connect(recorder, self._cell)

    def recording(self, port_name):
        """
        Return recorded data as a dictionary containing one numpy array for
        each neuron, ids as keys.
        """
        if port_name == self.componentclass.annotations[
                PYPE9_NS][MEMBRANE_VOLTAGE]:
            port_name = self.build_componentclass.annotations[
                PYPE9_NS][MEMBRANE_VOLTAGE]
        events, interval = nest.GetStatus(self._recorders[port_name],
                                          ('events', 'interval'))[0]
        data = neo.AnalogSignal(
            events[port_name],
            sampling_period=interval * pq.ms,
            t_start=0.0 * pq.ms, units='mV',  # FIXME: This should be read from prop. @IgnorePep8
            name=port_name)
        return data

    def play(self, port_name, signal):
        """
        Injects current into the segment

        `current` -- a vector containing the current [neo.AnalogSignal]
        """
        if isinstance(self._nineml.component_class.receive_port(port_name),
                      nineml.abstraction.EventPort):
            raise NotImplementedError
        else:
            self.signals[port_name] = nest.Create(
                'step_current_generator', 1,
                {'amplitude_values': pq.Quantity(signal, 'pA'),
                 'amplitude_times': pq.Quantity(signal.times, 'ms'),
                 'start': float(pq.Quantity(signal.t_start, 'ms')),
                 'stop': float(pq.Quantity(signal.t_stop, 'ms'))})
            nest.Connect(self.signals[port_name], self._cell,
                         syn_spec={"receptor_type":
                                   self._receive_ports[port_name]})

    @property
    def signals(self):
        try:
            return self._signals
        except AttributeError:
            super(Cell, self).__setattr__('_signals', {})
            return self._signals

    def voltage_clamp(self, voltages, series_resistance=1e-3):
        raise NotImplementedError("voltage clamps are not supported for "
                                  "Pype9->NEST at this stage.")


class CellMetaClass(base.CellMetaClass):

    _built_types = {}
    CodeGenerator = CodeGenerator
    BaseCellClass = Cell

    @classmethod
    def load_libraries(cls, name, install_dir):
        lib_dir = os.path.join(install_dir, 'lib', 'nest')
        if (sys.platform.startswith('linux') or
            sys.platform in ['os2', 'os2emx', 'cygwin', 'atheos',
                             'ricos']):
            lib_path_key = 'LD_LIBRARY_PATH'
        elif sys.platform == 'darwin':
            lib_path_key = 'DYLD_LIBRARY_PATH'
        elif sys.platform == 'win32':
            lib_path_key = 'PATH'
        if lib_path_key in os.environ:
            os.environ[lib_path_key] += os.pathsep + lib_dir
        else:
            os.environ[lib_path_key] = lib_dir
        # Add module install directory to NEST path
        nest.sli_run(
            '({}) addpath'.format(os.path.join(install_dir, 'share', 'nest',
                                               'sli')))
        # Install nest module
        nest.Install(name + 'Module')
