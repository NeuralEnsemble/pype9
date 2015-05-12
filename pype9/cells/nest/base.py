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
from pype9.cells.code_gen.nest import CodeGenerator
from .simulation_controller import simulation_controller
from pype9.cells import base
from pype9.annotations import PYPE9_NS, MEMBRANE_VOLTAGE


basic_nineml_translations = {
    'Voltage': 'V_m', 'Diameter': 'diam', 'Length': 'L'}


class Cell(base.Cell):

    _controller = simulation_controller

    def __init__(self, *properties, **kwprops):
        super(Cell, self).__setattr__('_initialized', False)
        self._cell = nest.Create(self.__class__.name)
        super(Cell, self).__init__(*properties, **kwprops)
        self._initialized = True

    def __getattr__(self, varname):
        if self._initialized and varname in self._nineml.property_names:
            return nest.GetStatus(self._cell, keys=varname)[0]
        else:
            raise AttributeError("'{}' cell class does not have parameter '{}'"
                                 .format(self.componentclass.name, varname))

    def __setattr__(self, varname, value):
        if (self._initialized and
            varname in chain(
                self._nineml.property_names,
                self._nineml.component_class.state_variable_names)):
            nest.SetStatus(self._cell, varname, value)
        else:
            super(Cell, self).__setattr__(varname, value)

    def set(self, prop):
        super(Cell, self).set(prop)
        # FIXME: need to convert to NEST units!!!!!!!!!!!
        nest.SetStatus(self._cell, prop.name, prop.value)

    def record(self, variable):
        self._initialise_local_recording()
        if variable == self.componentclass.annotations[
                PYPE9_NS][MEMBRANE_VOLTAGE]:
            variable = self.build_componentclass.annotations[
                PYPE9_NS][MEMBRANE_VOLTAGE]
        self._recorders[variable] = recorder = nest.Create('multimeter')
        nest.SetStatus(recorder, {'record_from': [variable]})
        nest.Connect(recorder, self._cell)

    def recording(self, variable):
        """
        Return recorded data as a dictionary containing one numpy array for
        each neuron, ids as keys.
        """
        if variable == self.componentclass.annotations[
                PYPE9_NS][MEMBRANE_VOLTAGE]:
            variable = self.build_componentclass.annotations[
                PYPE9_NS][MEMBRANE_VOLTAGE]
        events = nest.GetStatus(self._recorders[variable], 'events')[0]
#         ids = events['senders']
        data = neo.AnalogSignal(
            events[variable],
            sampling_period=self._controller.dt * pq.ms,
            t_start=0.0 * pq.ms, units='mV',  # FIXME: This should be read from prop. @IgnorePep8
            name=variable)
        return data

    def inject_current(self, current):
        """
        Injects current into the segment

        `current` -- a vector containing the current [neo.AnalogSignal]
        """
        self._iclamp = nest.Create('step_current_generator')
        nest.Connect(self._iclamp, self._cell)
        nest.SetStatus(self._iclamp, {'amplitude_values': current,
                                      'amplitude_times': current.times,
                                      'start': current.t_start,
                                      'stop': current.t_stop})

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
        nest.sli_run('({}) addpath'
                     .format(os.path.join(install_dir, 'share', 'nest')))
        # Install nest module
        nest.Install(name + 'Module')
