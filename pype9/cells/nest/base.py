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
import nest
from pype9.cells.code_gen.nest import CodeGenerator
from .simulation_controller import simulation_controller
import pype9.cells.base


basic_nineml_translations = {
    'Voltage': 'V_m', 'Diameter': 'diam', 'Length': 'L'}


class Cell(pype9.cells.base.Cell):

    _controller = simulation_controller

    def __init__(self):
        self._cell = nest.Create(self.__class__.name)

    def record(self, variable):
        key = (variable, None, None)
        self._initialise_local_recording()
        if variable == 'spikes':
            raise NotImplementedError
        elif variable == 'v':
            self._recordings[key] = recorder = nest.Create('voltmeter')
            nest.Connect(recorder, self._cell)
        else:
            raise NotImplementedError(
                "Haven't implemented non-membrane voltage recording for NEST "
                "yet.")

    def inject_current(self, current):
        """
        Injects current into the segment

        `current` -- a vector containing the current [neo.AnalogSignal]
        """
        self._iclamp = nest.Create('step_current_generator')
        nest.Connect(self.iclamp, self._cell)
        nest.SetStatus(self._iclamp, {'amplitude_values': current,
                                      'amplitude_times': current.times,
                                      'start': current.time_start,
                                      'stop': current.tim_stop})

    def voltage_clamp(self, voltages, series_resistance=1e-3):
        raise NotImplementedError("voltage clamps are not supported for "
                                  "Pype9->NEST at this stage.")


class CellMetaClass(pype9.cells.base.CellMetaClass):

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
