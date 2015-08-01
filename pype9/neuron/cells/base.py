"""

  This package combines the common.ncml with existing pyNN classes

  Author: Thomas G. Close (tclose@oist.jp)
  Copyright: 2012-2014 Thomas G. Close.
  License: This file is part of the "NineLine" package, which is released under
           the MIT Licence, see LICENSE for details.
"""
from __future__ import absolute_import
from pype9.exceptions import Pype9RuntimeError
# MPI may not be required but NEURON sometimes needs to be initialised after
# MPI so I am doing it here just to be safe (and to save me headaches in the
# future)
try:
    from mpi4py import MPI  # @UnusedImport @IgnorePep8 This is imported before NEURON to avoid a bug in NEURON
except ImportError:
    pass
from neuron import h, load_mechanisms
import quantities as pq
import os.path
from .code_gen import CodeGenerator
from pype9.base.cells.tree import in_units
from pype9.utils import create_unit_conversions, convert_units
from itertools import chain
from pype9.base.cells import base
from pype9.neuron.utils import UnitAssigner
from pype9.utils import convert_to_property, convert_to_quantity
from .controller import simulation_controller
from math import pi
from pype9.annotations import PYPE9_NS, MEMBRANE_CAPACITANCE, EXTERNAL_CURRENTS


basic_nineml_translations = {'Voltage': 'v', 'Diameter': 'diam', 'Length': 'L'}

NEURON_NS = 'NEURON'

import logging

logger = logging.getLogger("PyPe9")


_basic_SI_to_neuron_conversions = (('s', 'ms'),
                                   ('V', 'mV'),
                                   ('A', 'nA'),
                                   ('S', 'uS'),
                                   ('F', 'nF'),
                                   ('m', 'um'),
                                   ('Hz', 'Hz'),
                                   ('Ohm', 'MOhm'),
                                   ('M', 'mM'))

_compound_SI_to_neuron_conversions = (
    ((('A', 1), ('m', -2)),
     (('mA', 1), ('cm', -2))),
    ((('F', 1), ('m', -2)),
     (('uF', 1), ('cm', -2))),
    ((('S', 1), ('m', -2)),
     (('S', 1), ('cm', -2))),
    ((('Ohm', 1), ('m', 1)),
     (('Ohm', 1), ('cm', 1))))


_basic_unit_dict, _compound_unit_dict = create_unit_conversions(
    _basic_SI_to_neuron_conversions, _compound_SI_to_neuron_conversions)


def convert_to_neuron_units(value, unit_str=None):
    return convert_units(
        value, unit_str, _basic_unit_dict, _compound_unit_dict)


class Cell(base.Cell):

    V_INIT_DEFAULT = -65.0

    _controller = simulation_controller

    def __init__(self, *properties, **kwprops):
        """
        `propertes/kwprops` --  Can accept a single parameter, which is a
                                dictionary of parameters or kwarg parameters,
                                or a list of nineml.Property objects
        """
        super(Cell, self).__setattr__('_created', False)
        # Construct all the NEURON structures
        self._sec = h.Section()  # @UndefinedVariable
        # Insert dynamics mechanism (the built component class)
        HocClass = getattr(h, self.__class__.name)
        self._hoc = HocClass(0.5, sec=self._sec)
        # In order to scale the distributed current to the same units as point
        # process current, i.e. mA/cm^2 -> nA the surface area needs to be
        # 100um. mA/cm^2 = -3-(-2^2) = 10^1, 100um^2 = 2 + -6^2 = 10^(-10), nA
        # = 10^(-9). 1 - 10 = - 9. (see PyNN Izhikevich neuron implementation)
        self._sec.L = 10.0
        self._sec.diam = 10.0 / pi
        # Get the membrane capacitance property
        self._cm_prop = self.build_prototype.property(
            self.build_componentclass.annotations[
                PYPE9_NS][MEMBRANE_CAPACITANCE])
        cm = pq.Quantity(convert_to_quantity(self._cm_prop), 'nF')
        # Set capacitance in mechanism
        setattr(self._hoc, self._cm_prop.name, float(cm))
        # Set capacitance in hoc
        specific_cm = pq.Quantity(cm / self.surface_area, 'uF/cm^2')
        self._sec.cm = float(specific_cm)
        # Set up members required for PyNN
        self.recordable = {'spikes': None, 'v': self.source}
        self.spike_times = h.Vector(0)
        self.traces = {}
        self.gsyn_trace = {}
        self.recording_time = 0
        self.rec = h.NetCon(self.source, None, sec=self._sec)
        self.initial_v = self.V_INIT_DEFAULT
        # Call base init (needs to be after 9ML init)
        super(Cell, self).__init__(*properties, **kwprops)
        # Enable the override of setattr so that only properties of the 9ML
        # component can be set.
        self._created = True

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

    @property
    def surface_area(self):
        return (self._sec.L * pq.um) * (self._sec.diam * pi * pq.um)

    def get_threshold(self):
        return in_units(self._model.spike_threshold, 'mV')

    def __getattr__(self, varname):
        """
        To support the access to components on particular segments in PyNN the
        segment name can be prepended enclosed in curly brackets (i.e. '{}').

        @param var [str]: var of the attribute, with optional segment segment
                          name enclosed with {} and prepended
        """
        if self._created:
            if varname in self.componentclass.parameter_names:
                val = convert_to_quantity(self._nineml.property(varname))
                # FIXME: Need to assert the same as hoc value
            elif varname in self.componentclass.state_variable_names:
                try:
                    val = getattr(self._hoc, varname)
                except AttributeError:
                    try:
                        val = getattr(self._sec, varname)
                    except AttributeError:
                        assert False
            else:
                raise AttributeError("{} does not have attribute '{}'"
                                     .format(self.name, varname))
            return val

    def __setattr__(self, varname, val):
        """
        Any '.'s in the attribute var are treated as delimeters of a nested
        varspace lookup. This is done to allow pyNN's population.tset method to
        set attributes of cell components.

        @param var [str]: var of the attribute or '.' delimeted string of
                          segment, component and attribute vars
        @param val [*]: val of the attribute
        """
        if self._created:
            # Try to set as property
            if varname in self.componentclass.parameter_names:
                self._nineml.set(convert_to_property(varname, val))
            elif varname not in self.componentclass.state_variable_names:
                raise Pype9RuntimeError(
                    "'{}' is not a parameter or state variable of the '{}'"
                    " component class ('{}')"
                    .format(varname, self.componentclass.name,
                            "', '".join(chain(
                                self.componentclass.parameter_names,
                                self.componentclass.state_variable_names))))
            val = UnitAssigner.scale_quantity(self, val)
            try:
                setattr(self._hoc, varname, val)
            except LookupError:
                setattr(self._sec, varname, val)
        else:
            super(Cell, self).__setattr__(varname, val)

    def set(self, prop):
        super(Cell, self).set(prop)
        # FIXME: need to convert to NEURON units!!!!!!!!!!!
        setattr(self._hoc, prop.name, prop.value)
        # Set membrane capacitance in hoc if required
        if prop.name == self._cm_prop.name:
            cm = convert_to_quantity(prop)
            self._sec.cm = float(pq.Quantity(cm / self.surface_area,
                                             'uF/cm^2'))

    def record(self, variable):
        key = (variable, None, None)
        self._initialise_local_recording()
        if variable == 'spikes':
            self._recorders[key] = recorder = h.NetCon(
                self._sec._ref_v, None, self.get_threshold(),
                0.0, 1.0, sec=self._sec)
        elif variable == 'v':
            recorder = getattr(self._sec(0.5), '_ref_' + variable)
        else:
            recorder = getattr(self._hoc, '_ref_' + variable)
        self._recordings[key] = recording = h.Vector()
        recording.record(recorder)

    def play(self, port_name, signal):
        """
        Injects current into the segment

        `current` -- a vector containing the current [neo.AnalogSignal]
        """
        ext_is = self.build_componentclass.annotations[
            PYPE9_NS][EXTERNAL_CURRENTS]
        try:
            self.componentclass.port(port_name)
        except KeyError:
            raise Pype9RuntimeError(
                "Cannot play into unrecognised port '{}'".format(port_name))
        if port_name not in (p.name for p in ext_is):
            raise NotImplementedError(
                "Can only play into external current ports ('{}'), not '{}' "
                "port.".format("', '".join(p.name for p in ext_is), port_name))
        super(Cell, self).__setattr__('iclamp', h.IClamp(0.5, sec=self._sec))
        self.iclamp.delay = 0.0
        self.iclamp.dur = 1e12
        self.iclamp.amp = 0.0
        super(Cell, self).__setattr__(
            'iclamp_amps', h.Vector(pq.Quantity(signal, 'nA')))
        super(Cell, self).__setattr__(
            'iclamp_times', h.Vector(pq.Quantity(signal.times, 'ms')))
        self.iclamp_amps.play(self.iclamp._ref_amp, self.iclamp_times)

    def voltage_clamp(self, voltages, series_resistance=1e-3):
        """
        Clamps the voltage of a segment

        `voltage` -- a vector containing the voltages to clamp the segment
                     to [neo.AnalogSignal]
        """
        super(Cell, self).__setattr__('seclamp', h.SEClamp(0.5, sec=self._sec))
        self.seclamp.rs = series_resistance
        self.seclamp.dur1 = 1e12
        super(Cell, self).__setattr__(
            'seclamp_amps', h.Vector(pq.Quantity(voltages, 'mV')))
        super(Cell, self).__setattr__(
            'seclamp_times', h.Vector(pq.Quantity(voltages.times, 'ms')))
        self.seclamp_amps.play(self.seclamp._ref_amp, self.seclamp_times)


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
