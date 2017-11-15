"""
Command that compares a 9ML model with an existing version in NEURON and/or
NEST
"""
from __future__ import absolute_import, division
from __future__ import print_function
from builtins import str
from builtins import object
import os.path
import re
from itertools import combinations
from collections import defaultdict
import neuron
from copy import copy
import pyNN.neuron  # @UnusedImport - imports PyNN mechanisms
import nest
from numpy import exp
try:
    import pylab as plt
except (ImportError, RuntimeError):
    plt = None
from pype9.simulate.neuron import (
    CellMetaClass as NeuronCellMetaClass,
    Simulation as NeuronSimulation)
from pype9.simulate.nest import CodeGenerator as NESTCodeGenerator
from pype9.simulate.neuron.units import UnitHandler as UnitHandlerNEURON
from pype9.simulate.nest.units import UnitHandler as UnitHandlerNEST
from pype9.simulate.nest import (
    CellMetaClass as NESTCellMetaClass,
    Simulation as NESTSimulation)
from nineml.units import Quantity
from nineml import units as un
import numpy
import quantities as pq
import neo
from pype9.exceptions import Pype9RuntimeError
from pype9.utils.logging import logger


class Comparer(object):
    """
    The Comparer class is used to compare the dynamics of a 9ML model simulated
    in either NEURON or NEST with a native model in either of those simulators
    (or both)

    Parameters
    ----------
    nineml_model : nineml.Dynamics | nineml.Network
        9ML model to compare
    simulators : list(str)
        List of simulator names to simulate the 9ML model in
    duration : float
        Simulation duration
    dt : float
        Simulation time step
    initial_states : dict(str, nineml.Quantity)
        A dictionary of the initial states
    neuron_ref : tuple(str, dict(str, nineml.Quantity)
        A tuple containing the name of neuron model and a dictionary of
        parameter and state name mappings
    nest_ref :  tuple(str, dict(str, nineml.Quantity)
        A tuple containing the name of nest model and a dictionary of parameter
        and state name mappings
    input_signal : neo.AnalogSignal
        Tuple containing the analog signal (in Neo format) and the port to play
        it into
    input_train : neo.SpikeTrain
        Tuple containing the event train (in Neo format) and the port to play
        it into
    """

    specific_params = ('pas.g', 'cm')

    def __init__(self, nineml_model=None, properties=None, initial_states=None,
                 initial_regime=None, state_variable='v',
                 dt=0.01, simulators=None, neuron_ref=None, nest_ref=None,
                 input_signal=None, input_train=None, neuron_translations=None,
                 nest_translations=None, neuron_build_args=None,
                 nest_build_args=None, min_delay=0.1, device_delay=0.1,
                 max_delay=10.0, extra_mechanisms=None,
                 extra_point_process=None,
                 auxiliary_states=None):
        if nineml_model is not None and not simulators:
            raise Pype9RuntimeError(
                "No simulators specified to simulate the 9ML model '{}'."
                "Add either 'neuron', 'nest' or both to the positional "
                "arguments".format(nineml_model.name))
        self.simulate_neuron = 'neuron' in simulators
        self.simulate_nest = 'nest' in simulators
        self.dt = self.to_float(dt, 'ms')
        self.state_variable = state_variable
        self.nineml_model = nineml_model
        self.properties = properties if properties is not None else {}
        self.neuron_ref = neuron_ref if self.simulate_neuron else None
        self.nest_ref = nest_ref if self.simulate_nest else None
        self.simulators = simulators if simulators is not None else []
        self.extra_mechanisms = (extra_mechanisms
                                 if extra_mechanisms is not None else [])
        self.extra_point_process = extra_point_process
        self.neuron_translations = (neuron_translations
                                    if neuron_translations is not None else {})
        self.nest_translations = (nest_translations
                                  if nest_translations is not None else {})
        self.initial_states = (initial_states
                               if initial_states is not None else {})
        self.initial_regime = initial_regime
        self.auxiliary_states = (auxiliary_states
                                 if auxiliary_states is not None else [])
        self.input_signal = input_signal
        self.input_train = input_train
        self.build_args = {
            'nest': (nest_build_args
                     if nest_build_args is not None else {}),
            'neuron': (neuron_build_args
                       if neuron_build_args is not None else {})}
        self.nml_cells = {}
        if self.state_variable in self.nest_translations:
            self.nest_state_variable = self.nest_translations[
                self.state_variable][0]
        else:
            self.nest_state_variable = self.state_variable
        if self.state_variable in self.neuron_translations:
            self.neuron_state_variable = self.neuron_translations[
                self.state_variable][0]
        else:
            self.neuron_state_variable = self.state_variable
        self.min_delay = min_delay
        self.device_delay = device_delay
        self.max_delay = max_delay

    def simulate(self, duration, nest_rng_seed=12345, neuron_rng_seed=54321):
        """
        Run and the simulation
        """
        if self.simulate_nest:
            with NESTSimulation(dt=self.dt * un.ms, seed=nest_rng_seed,
                                min_delay=self.min_delay * un.ms,
                                max_delay=self.max_delay * un.ms,
                                device_delay=self.device_delay * un.ms) as sim:
                if 'nest' in self.simulators:
                    self._create_9ML(self.nineml_model, self.properties,
                                     'nest')
                if self.nest_ref is not None:
                    self._create_NEST(self.nest_ref)
                sim.run(duration)
        if self.simulate_neuron:
            with NeuronSimulation(dt=self.dt * un.ms, seed=neuron_rng_seed,
                                  min_delay=self.min_delay * un.ms,
                                  max_delay=self.max_delay * un.ms) as sim:
                if 'neuron' in self.simulators:
                    self._create_9ML(self.nineml_model, self.properties,
                                     'neuron')
                if self.neuron_ref is not None:
                    self._create_NEURON(self.neuron_ref)
                sim.run(duration)
        return self  # return self so it can be chained with subsequent methods

    def compare(self):
        name_n_sigs = [('9ML-' + s,
                        self.nml_cells[s].recording(self.state_variable))
                       for s in self.simulators]
        if self.neuron_ref is not None:
            name_n_sigs.append(('Ref-neuron',
                                pq.Quantity(self._get_NEURON_signal()[1][1:],
                                            'mV')))
        if self.nest_ref is not None:
            name_n_sigs.append(('Ref-nest',
                                pq.Quantity(self._get_NEST_signal(), 'mV')))
        comparisons = {}
        for (name1, signal1), (name2, signal2) in combinations(name_n_sigs, 2):
            if len(signal1):
                logger.debug("Comparing {} with {}".format(name1, name2))
                avg_diff = (numpy.sum(numpy.abs(numpy.ravel(signal1) -
                                                numpy.ravel(signal2))) /
                            len(signal1))
            else:
                avg_diff = 0.0
            comparisons[tuple(sorted((name1, name2)))] = avg_diff
        return comparisons

    def plot(self, to_plot=None):
        legend = []
        for simulator in self.simulators:
            if to_plot is None or simulator in to_plot:
                self._plot_9ML(simulator)
                legend.append('{} (9ML-{})'.format(self.nineml_model.name,
                                                   simulator.upper()))
        if self.neuron_ref and (to_plot is None or self.neuron_ref in to_plot):
            self._plot_NEURON()
            legend.append(self.neuron_ref + ' (NEURON)')
        if self.nest_ref and (to_plot is None or self.nest_ref in to_plot):
            self._plot_NEST()
            legend.append(self.nest_ref + ' (NEST)')
        plt.legend(legend)
        if self.auxiliary_states:
            for state_var in self.auxiliary_states:
                plt.figure()
                aux_legend = []
                for simulator in self.simulators:
                    s = self.nml_cells[simulator].recording(state_var)
                    scaled = UnitHandlerNEURON.scale_value(s)
                    plt.plot(s.times, scaled)
                    aux_legend.append('9ML - {}'.format(simulator))
                plt.title(state_var)
                plt.legend(aux_legend)
        plt.show()

    def _create_9ML(self, model, properties, simulator):
        # -----------------------------------------------------------------
        # Set up 9MLML cell
        # -----------------------------------------------------------------
        if simulator.lower() == 'neuron':
            CellMetaClass = NeuronCellMetaClass
        elif simulator.lower() == 'nest':
            CellMetaClass = NESTCellMetaClass
        else:
            assert False
        Cell = CellMetaClass(model, **self.build_args[simulator])
        self.nml_cells[simulator] = Cell(properties,
                                         regime_=self.initial_regime,
                                         **self.initial_states)
        if self.input_signal is not None:
            self.nml_cells[simulator].play(*self.input_signal)
        if self.input_train is not None:
            self.nml_cells[simulator].play(*self.input_train)
        self.nml_cells[simulator].record(self.state_variable)
        for state_var in self.auxiliary_states:
            self.nml_cells[simulator].record(state_var)
#         self.nml_cells[simulator].set_state(self.initial_states,
#                                             regime=self.initial_regime)

    def _create_NEURON(self, neuron_name):
        # -----------------------------------------------------------------
        # Set up NEURON section
        # -----------------------------------------------------------------
        self.nrn_cell_sec = neuron.h.Section()
        try:
            self.nrn_cell = eval(
                'neuron.h.{}(0.5, sec=self.nrn_cell_sec)'.format(neuron_name))
        except TypeError:
            self.nrn_cell_sec.insert(neuron_name)
            self.nrn_cell = getattr(self.nrn_cell_sec(0.5), neuron_name)
        self.nrn_cell_sec.L = 10
        self.nrn_cell_sec.diam = 10 / numpy.pi
        self.nrn_cell_sec.cm = 1.0
        for mech_name in self.extra_mechanisms:
            self.nrn_cell_sec.insert(mech_name)
        if self.extra_point_process is not None:
            MechClass = getattr(neuron.h, self.extra_point_process)
            self.extra_point_process = MechClass(self.nrn_cell_sec(0.5))
        for prop in self.properties.properties:
            name = prop.name
            value = prop.value
            try:
                varname, scale = self.neuron_translations[name]
                value = value * scale
            except (ValueError, KeyError):
                varname = self.neuron_translations.get(name, name)
            if varname in self.specific_params:
                specific_value = (Quantity(value, prop.units) /
                                  (100 * un.um ** 2))
                value = UnitHandlerNEURON.scale_value(specific_value)
            else:
                value = UnitHandlerNEURON.scale_value(
                    Quantity(value, prop.units))
            if varname is not None:
                if '.' in varname:
                    mech_name, vname = varname.split('.')
                    try:
                        setattr(getattr(self.nrn_cell_sec(0.5), mech_name),
                                vname, value)
                    except AttributeError:
                        setattr(self.extra_point_process, vname, value)
                elif varname == 'cm':
                    self.nrn_cell_sec.cm = value
                else:
                    try:
                        setattr(self.nrn_cell, varname, value)
                    except AttributeError:
                        setattr(self.nrn_cell_sec, varname, value)
        for name, value in self.initial_states.items():
            try:
                varname, scale = self.neuron_translations[name]
                value = value * scale
            except (ValueError, KeyError):
                varname = self.neuron_translations.get(name, name)
            value = UnitHandlerNEURON.scale_value(
                UnitHandlerNEURON.from_pq_quantity(value))
            if varname is not None:
                if '.' in varname:
                    try:
                        setattr(getattr(self.nrn_cell_sec(0.5), mech_name),
                                vname, value)
                    except AttributeError:
                        setattr(self.point_process, vname, value)
                else:
                    try:
                        setattr(self.nrn_cell, varname, value)
                    except (AttributeError, LookupError):
                        setattr(self.nrn_cell_sec, varname, value)
        # Specify current injection
        if self.input_signal is not None:
            _, signal = self.input_signal
            times = numpy.asarray(signal.times.rescale(pq.ms))
            self._nrn_iclamp = neuron.h.IClamp(0.5, sec=self.nrn_cell_sec)
            self._nrn_iclamp.delay = 0.0
            self._nrn_iclamp.dur = 1e12
            self._nrn_iclamp.amp = 0.0
            self._nrn_iclamp_amps = neuron.h.Vector(signal.rescale(pq.nA))
            self._nrn_iclamp_times = neuron.h.Vector(times)
            self._nrn_iclamp_amps.play(self._nrn_iclamp._ref_amp,
                                       self._nrn_iclamp_times)
        if self.input_train is not None:
            port_name, train, connection_properties = self.input_train
            try:
                _, scale = self.neuron_translations[port_name]
            except KeyError:
                scale = 1.0
            # FIXME: Should scale units
            weight = connection_properties[0].value * scale
            self._vstim = neuron.h.VecStim()
            times = numpy.asarray(train.rescale(pq.ms)) - 1.0
            self._vstim_times = neuron.h.Vector(times)
            self._vstim.play(self._vstim_times)
            target = (self.extra_point_process
                      if self.extra_point_process is not None
                      else self.nrn_cell)
            self._vstim_con = neuron.h.NetCon(
                self._vstim, target, sec=self.nrn_cell_sec)
            self._vstim_con.weight[0] = weight
        # Record Time from NEURON (neuron.h.._ref_t)
        self._nrn_rec = self.NEURONRecorder(self.nrn_cell_sec, self.nrn_cell)
        self._nrn_rec.record(self.neuron_state_variable)

    def _create_NEST(self, nest_name):
        trans_params = {}
        for prop in self.properties.properties:
            name = prop.name
            value = prop.value
            try:
                varname, scale = self.nest_translations[name]
                value = value * scale
            except (ValueError, KeyError):
                varname = self.nest_translations.get(name, name)
            value = UnitHandlerNEST.scale_value(Quantity(value, prop.units))
            if varname is not None:
                trans_params[varname] = value
        self.nest_cell = nest.Create(nest_name, 1, trans_params)
        try:
            receptor_types = nest.GetDefaults(nest_name)['receptor_types']
        except KeyError:
            receptor_types = None
        if self.input_signal is not None:
            port_name, signal = self.input_signal
            generator = nest.Create(
                'step_current_generator', 1,
                {'amplitude_values': numpy.ravel(pq.Quantity(signal, 'pA')),
                 'amplitude_times': numpy.ravel(numpy.asarray(
                     signal.times.rescale(pq.ms))) - self.device_delay,
                 'start': float(signal.t_start.rescale(pq.ms)),
                 'stop': float(signal.t_stop.rescale(pq.ms))})
            nest.Connect(generator, self.nest_cell,
                         syn_spec={'receptor_type':
                                   (receptor_types[port_name]
                                    if receptor_types else 0),
                                   'delay': self.device_delay})
        if self.input_train is not None:
            port_name, signal, connection_properties = self.input_train
            try:
                _, scale = self.nest_translations[port_name]
            except KeyError:
                scale = 1.0
            # FIXME: Should scale units
            weight = connection_properties[0].value * scale
            spike_times = (numpy.asarray(signal.rescale(pq.ms)) -
                           self.device_delay)
            if any(spike_times < 0.0):
                raise Pype9RuntimeError(
                    "Some spike are less than minimum delay and so can't be "
                    "played into cell ({})".format(
                        ', '.join(
                            str(t) for t in
                            spike_times[spike_times < self.device_delay])))
            generator = nest.Create(
                'spike_generator', 1, {'spike_times': spike_times})
            nest.Connect(generator, self.nest_cell,
                         syn_spec={'receptor_type':
                                   (receptor_types[port_name]
                                    if receptor_types else 0),
                                   'delay': self.device_delay,
                                   'weight': float(weight)})
        self.nest_multimeter = nest.Create(
            'multimeter', 1, {"interval": self.to_float(self.dt, 'ms')})
        nest.SetStatus(
            self.nest_multimeter,
            {'record_from': [self.nest_state_variable]})
        nest.Connect(self.nest_multimeter, self.nest_cell,
                     syn_spec={'delay': self.device_delay})
        trans_states = {}
        for name, qty in self.initial_states.items():
            try:
                varname, scale = self.nest_translations[name]
                qty = qty * scale
            except (ValueError, KeyError):
                varname = self.nest_translations.get(name, name)
            value = UnitHandlerNEST.scale_value(qty)
            if varname is not None:
                trans_states[varname] = value
        nest.SetStatus(self.nest_cell, trans_states)

    def _plot_NEURON(self):  # @UnusedVariable
        pnn_t, pnn_v = self._get_NEURON_signal()
        plt.plot(pnn_t[:-1], pnn_v[1:])

    def _plot_NEST(self):
        nest_v = self._get_NEST_signal()
        plt.plot(nest_v.times.rescale(pq.ms), nest_v.rescale(pq.mV))

    def _plot_9ML(self, sim_name):  # @UnusedVariable
        nml_v = self.nml_cells[sim_name].recording(self.state_variable)
        plt.plot(nml_v.times, nml_v)

    def _diff_NEURON(self):  # @UnusedVariable
        _, pnn_v = self._get_NEURON_signal()
        nml_v = self.nml_cells['NEURON'].recording('v')
        return float(pq.Quantity((nml_v - pnn_v[1:] * pq.mV).sum(), 'V'))

    def _diff_NEST(self):
        nest_v = self._get_NEST_signal()
        nml_v = self.nml_cells['NEST'].recording(self.nest_state_variable)
        return float(pq.Quantity((nml_v - nest_v * pq.mV).sum(), 'V'))

    def _get_NEURON_signal(self):
        return self._nrn_rec.recording(self.neuron_state_variable)

    def _get_NEST_signal(self):
        return neo.AnalogSignal(
            nest.GetStatus(
                self.nest_multimeter, 'events')[0][self.nest_state_variable],
            sampling_period=self.dt * pq.ms, units='mV')  # @UndefinedVariable @IgnorePep8

    @classmethod
    def to_float(cls, qty, units):
        return float(pq.Quantity(qty, units))

    class NEURONRecorder(object):

        def __init__(self, sec, mech):
            self.sec = sec
            self.mech = mech
            self.rec_t = neuron.h.Vector()
            self.rec_t.record(neuron.h._ref_t)
            self.recs = {}

        def record(self, varname):
            rec = neuron.h.Vector()
            self.recs[varname] = rec
            if varname == 'v':
                rec.record(self.sec(0.5)._ref_v)
            else:
                rec.record(getattr(self.mech, '_ref_' + varname))

        def recording(self, varname):
            return numpy.array(self.rec_t), numpy.array(self.recs[varname])


def input_step(port_name, amplitude, start_time, duration, dt, delay):
    start_time = pq.Quantity(start_time, 'ms')
    duration = pq.Quantity(duration, 'ms')
    dt = pq.Quantity(dt, 'ms')
    delay = pq.Quantity(delay, 'ms')
    start_minus_delay = start_time - delay
    num_preceding = int(numpy.floor(start_minus_delay / dt))
    num_remaining = int(numpy.ceil((duration - start_minus_delay) / dt))
    amplitude = float(pq.Quantity(amplitude, 'nA'))
    signal = neo.AnalogSignal(
        numpy.concatenate((numpy.zeros(num_preceding),
                           numpy.ones(num_remaining) * float(amplitude))),
        sampling_period=dt, units='nA', time_units='ms',
        t_start=delay)
    return (port_name, signal)


def input_freq(port_name, freq, duration, weight, offset=None):
    freq = pq.Quantity(freq, 'kHz')
    duration = pq.Quantity(duration, 'ms')
    isi = 1 / freq
    if offset is None:
        offset = isi
    else:
        offset = pq.Quantity(offset, 'ms')
    train = neo.SpikeTrain(
        numpy.arange(offset, duration, isi),
        units='ms', t_stop=duration,
        t_start=offset)
    return (port_name, train, weight)


class ReferenceBrunel2000(object):
    """
    The model in this file has been adapted from the brunel-alpha-nest.py
    model that is part of NEST.

    Copyright (C) 2004 The NEST Initiative

    NEST is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 2 of the License, or
    (at your option) any later version.

    NEST is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with NEST.  If not, see <http://www.gnu.org/licenses/>.
    This version uses NEST's Connect functions.
    """

    min_delay = 0.1 * un.ms
    max_delay = 10.0 * un.ms
    delay = 1.5 * un.ms

    # Parameters used to construct the reference network

    # Initialize the parameters of the integrate and fire neuron
    theta = 20.0 * un.mV
    J = 0.1  # postsynaptic amplitude in mV
    tauSyn = 0.1 * un.ms
    tauMem = 20.0 * un.ms
    tau_refrac = 2.0 * un.ms
    v_reset = 10.0 * un.mV
    # v_reset = 0.0
    R = 1.5 * un.Mohm

    CMem = tauMem / R
#     CMem = 250.0

    epsilon = 0.1  # connection probability

    parameter_sets = {
        "SR": {"g": 3.0, "eta": 2.0 * un.unitless / un.mV},
        "AI": {"g": 5.0, "eta": 2.0 * un.unitless / un.mV},
        "SIfast": {"g": 6.0, "eta": 4.0 * un.unitless / un.mV},
        "SIslow": {"g": 4.5, "eta": 0.9 * un.unitless / un.mV}}

    def __init__(self, case, order, external_input=None, connections=None,
                 init_v=None, delay=1.5 * un.ms, override_input=None):
        self._recorders = None

        (NE, NI, CE, CI, neuron_params,
         J_ex, J_in, p_rate) = self.parameters(case, order)

        if override_input is not None:
            print("changing poisson rate from {} to {}".format(p_rate,
                                                               override_input))
            p_rate = override_input

        nest.SetDefaults("iaf_psc_alpha", neuron_params)
        nodes_exc = nest.Create("iaf_psc_alpha", NE)
        nodes_inh = nest.Create("iaf_psc_alpha", NI)

        if init_v is not None:
            nest.SetStatus(nodes_exc, 'V_m', init_v['Exc'])
            nest.SetStatus(nodes_inh, 'V_m', init_v['Inh'])
        else:
            nest.SetStatus(nodes_exc + nodes_inh, 'V_m',
                           list(numpy.random.rand(NE + NI) * 20.0))

        if external_input is not None:
            nodes_ext = nest.Create(
                "spike_generator", NE + NI,
                params=[{'spike_times': r} for r in external_input])
        else:
            nest.SetDefaults("poisson_generator",
                             {"rate": float(Quantity(p_rate, un.Hz))})
            noise = nest.Create("poisson_generator")
            nodes_ext = nest.Create('parrot_neuron', NE + NI)
            nest.Connect(noise, nodes_ext)

        self._pops = {'Exc': nodes_exc, 'Inh': nodes_inh, 'Ext': nodes_ext}

        # Set up connections

        nest.CopyModel(
            "static_synapse", "excitatory", {
                "weight": float(Quantity(J_ex, un.nS)),
                "delay": float(Quantity(delay, un.ms))})
        nest.CopyModel(
            "static_synapse", "inhibitory", {
                "weight": float(Quantity(J_in, un.nS)),
                "delay": float(Quantity(delay, un.ms))})

        nest.Connect(nodes_ext, nodes_exc + nodes_inh, 'one_to_one',
                     "excitatory")

        if connections is not None:
            for (p1_name, p2_name), conns in connections.items():
                if p1_name == 'Exc':
                    p1 = nodes_exc
                    syn = 'excitatory'
                else:
                    p1 = nodes_inh
                    syn = 'inhibitory'
                p2 = nodes_exc if p2_name == 'Exc' else nodes_inh
                conns = copy(conns)
                conns[:, 0] += p1[0]
                conns[:, 1] += p2[0]
                for i in numpy.unique(conns[:, 1]):
                    nest.Connect(list(conns[(conns[:, 1] == i), 0]), [i],
                                 'all_to_all', syn)
        else:
            # We now iterate over all neuron IDs, and connect the neuron to the
            # sources from our array. The first loop connects the excitatory
            # neurons and the second loop the inhibitory neurons.
            conn_params_ex = {'rule': 'fixed_indegree', 'indegree': CE}
            nest.Connect(
                nodes_exc,
                nodes_exc +
                nodes_inh,
                conn_params_ex,
                "excitatory")

            conn_params_in = {'rule': 'fixed_indegree', 'indegree': CI}
            nest.Connect(
                nodes_inh,
                nodes_exc +
                nodes_inh,
                conn_params_in,
                "inhibitory")

    def __getitem__(self, pop_name):
        return self._pops[pop_name]

    @property
    def projections(self):
        combined = (self['Exc'] + self['Inh'])
        projs = {}
        projs['External'] = nest.GetConnections(self['Ext'], combined,
                                                'excitatory')
        projs['Excitation'] = nest.GetConnections(self['Exc'], combined,
                                                  'excitatory')
        projs['Inhibition'] = nest.GetConnections(self['Inh'], combined,
                                                  'inhibitory')
        return projs

    @classmethod
    def compute_normalised_psr(cls, tauMem, R, tauSyn):
        """Compute the maximum of postsynaptic potential
           for a synaptic input current of unit amplitude
           (1 pA)"""

        a = float(tauMem / tauSyn)
        b = (1.0 / tauSyn - 1.0 / tauMem)

        # time of maximum
        t_max = 1.0 / b * \
            (-nest.sli_func('LambertWm1', -exp(-1.0 / a) / a) - 1.0 / a)

        # maximum of PSP for current of unit amplitude
        return exp(1) / (tauSyn * tauMem * b / R) * (
            (exp(-float(t_max / tauMem)) - exp(-float(t_max / tauSyn))) /
            b - t_max * exp(-float(t_max / tauSyn)))

    @classmethod
    def parameters(cls, case, order):
        # Parameters for asynchronous irregular firing
        g = cls.parameter_sets[case]["g"]
        eta = cls.parameter_sets[case]["eta"]

        NE = 4 * order
        NI = 1 * order

        CE = int(cls.epsilon * NE)  # number of excitatory synapses per neuron
        CI = int(cls.epsilon * NI)  # number of inhibitory synapses per neuron
        if not CE:
            CE = 1
        if not CI:
            CI = 1

        # normalize synaptic current so that amplitude of a PSP is J
        J_unit = cls.compute_normalised_psr(cls.tauMem, cls.R, cls.tauSyn)  # / 1000.0 @IgnorePep8
        J_ex = cls.J / J_unit
        J_in = -g * J_ex

        # threshold rate, equivalent rate of events needed to
        # have mean input current equal to threshold
        nu_th = cls.theta / (J_ex * CE * cls.R * cls.tauSyn)  # threshold rate
        nu_ex = eta * nu_th
        p_rate = nu_ex * CE

        neuron_params = {"C_m": float(Quantity(cls.CMem, un.pF)),
                         "tau_m": float(Quantity(cls.tauMem, un.ms)),
                         "tau_syn_ex": float(Quantity(cls.tauSyn, un.ms)),
                         "tau_syn_in": float(Quantity(cls.tauSyn, un.ms)),
                         "t_ref": float(Quantity(cls.tau_refrac, un.ms)),
                         "E_L": 0.0,
                         "V_reset": float(Quantity(cls.v_reset, un.mV)),
                         "V_m": 0.0,
                         "V_th": float(Quantity(cls.theta, un.mV))}

        return NE, NI, CE, CI, neuron_params, J_ex, J_in, p_rate

    def record(self, num_record=50, num_record_v=2, timestep=0.1,
               to_plot=('Exc', 'Inh')):
        self._recorders = defaultdict(dict)
        for pop_name in to_plot:
            pop = numpy.asarray(self._pops[pop_name], dtype=int)
            spikes = self._recorders[pop_name]['spikes'] = nest.Create(
                "spike_detector")
            nest.SetStatus(spikes, [{"label": "brunel-py-" + pop_name,
                                     "withtime": True, "withgid": True}])
            nest.Connect(list(pop[:num_record]), spikes, syn_spec="excitatory")
            if num_record_v and pop_name != 'Ext':
                # Set up voltage traces recorders for reference network
                multi = self._recorders[pop_name]['V_m'] = nest.Create(
                    'multimeter', params={'record_from': ['V_m'],
                                          'interval': timestep})
                nest.Connect(multi, list(pop[:num_record_v]))

    @property
    def recorders(self):
        return self._recorders

_compare_re = re.compile(r"Average error between ([\w\-]+) and ([\w\-]+): "
                         r"([0-9\.\-e]+) (\w+)")
_error_re = re.compile(r"(\w+)Error:")


test_cache = os.path.join(NESTCodeGenerator().base_dir, '..', 'unittest-cache')


class DummyTestCase(object):

    def __init__(self):
        self.setUp()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def __del__(self):
        self.tearDown()

    def assertEqual(self, first, second, msg=None):
        if first != second:
            if msg is None:
                msg = '{} and {} are not equal'.format(repr(first),
                                                       repr(second))
            print(msg)

    def assertAlmostEqual(self, first, second, places=None, msg=None):
        if places is None:
            places = 7
        if abs(first - second) > 10 ** -places:
            if msg is None:
                msg = '{} and {} are not equal'.format(repr(first),
                                                       repr(second))
            print(msg)

    def assertLess(self, first, second, msg=None):
        if first >= second:
            if msg is None:
                msg = '{} is not less than {}'.format(repr(first),
                                                      repr(second))
            print(msg)

    def assertLessEqual(self, first, second, msg=None):
        if first > second:
            if msg is None:
                msg = '{} is not less than or equal to {}'.format(
                    repr(first), repr(second))
            print(msg)

    def assertNotEqual(self, first, second, msg=None):
        if first == second:
            if msg is None:
                msg = '{} is equal to {}'.format(
                    repr(first), repr(second))
            print(msg)

    def assertTrue(self, statement, msg=None):
        if not statement:
            if msg is None:
                msg = '{} is not true'.format(repr(statement))
            print(msg)

    def assertNotTrue(self, statement, msg=None):
        if statement:
            if msg is None:
                msg = '{} is true'.format(repr(statement))
            print(msg)
