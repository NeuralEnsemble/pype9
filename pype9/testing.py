"""
Command that compares a 9ML model with an existing version in NEURON and/or
NEST
"""
from __future__ import absolute_import, division
import sys
import os.path
import re
import subprocess as sp
from itertools import combinations
import tempfile
import shutil
import neuron
import pyNN.neuron  # @UnusedImport - imports PyNN mechanisms
import nest
try:
    import pylab as plt
except ImportError:
    plt = None
from pype9.neuron.cells import (
    CellMetaClass as CellMetaClassNEURON,
    simulation_controller as simulatorNEURON)
from pype9.neuron.units import UnitHandler as UnitHandlerNEURON
from pype9.nest.units import UnitHandler as UnitHandlerNEST
from pype9.nest.cells import (
    CellMetaClass as CellMetaClassNEST,
    simulation_controller as simulatorNEST)
from nineml.user import Quantity
import numpy
import quantities as pq
import neo
from pype9.exceptions import Pype9RuntimeError


compare_script_path = os.path.join(os.path.dirname(__file__), '..', 'scripts',
                                   'compare.py')

# This finds the python command path from the location of the os module
# python_cmd_path = os.path.join(os.path.dirname(os.__file__), '..', 'bin',
#                                'python')
# However, this will probably only work on *nix systems so a fall back using
# the sys.executable is used instead in this case (won't work from embedded
# executions
# if not os.path.exists(python_cmd_path):
python_cmd_path = sys.executable


class Comparer(object):
    """
    The Comparer class is used to compare the dynamics of a 9ML model simulated
    in either NEURON or NEST with a native model in either of those simulators
    (or both)
    """

    specific_params = ('pas.g', 'cm')

    def __init__(self, nineml_model=None, properties={}, initial_states={},
                 initial_regime=None, state_variable='v', dt=0.01,
                 simulators=[], neuron_ref=None, nest_ref=None,
                 input_signal=None, input_train=None, neuron_translations={},
                 nest_translations={}, neuron_build_args={},
                 nest_build_args={}, min_delay=0.02, max_delay=10.0,
                 extra_mechanisms=[], extra_point_process=None):
        """
        nineml_model   -- 9ML model to compare
        nineml_sims    -- tuple of simulator names to simulate the 9ML model in
        duration       -- simulation duration
        dt             -- simulation time step
        initial_states -- a dictionary of the initial states
        neuron_ref   -- a tuple containing the name of neuron model and a
                          dictionary of parameter and state name mappings
        nest_ref     -- a tuple containing the name of nest model and a
                          dictionary of parameter and state name mappings
        input_signal  -- tuple containing the analog signal (in Neo format)
                          and the port to play it into
        input_train    -- tuple containing the event train (in Neo format)
                          and the port to play it into
        """
        if nineml_model is not None and not simulators:
            raise Pype9RuntimeError(
                "No simulators specified to simulate the 9ML model '{}'."
                "Add either 'neuron', 'nest' or both to the positional "
                "arguments".format(nineml_model.name))
        self.simulate_neuron = ('neuron' in simulators or
                                neuron_ref is not None)
        self.simulate_nest = 'nest' in simulators or nest_ref is not None
        self.dt = self.to_float(dt, 'ms')
        self.state_variable = state_variable
        self.nineml_model = nineml_model
        self.properties = properties
        self.neuron_ref = neuron_ref
        self.nest_ref = nest_ref
        self.simulators = simulators
        self.extra_mechanisms = extra_mechanisms
        self.extra_point_process = extra_point_process
        self.neuron_translations = neuron_translations
        self.nest_translations = nest_translations
        self.initial_states = initial_states
        self.initial_regime = initial_regime
        self.input_signal = input_signal
        self.input_train = input_train
        self.build_args = {'nest': nest_build_args,
                           'neuron': neuron_build_args}
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
        self.max_delay = max_delay

    def simulate(self, duration):
        """
        Run and the simulation
        """
        if self.simulate_neuron:
            simulatorNEURON.reset()
            neuron.h.dt = self.dt
        if self.simulate_nest:
            nest.ResetKernel()
            simulatorNEST.reset()
            nest.SetKernelStatus({'resolution': self.dt})
        for simulator in self.simulators:
            self._create_9ML(self.nineml_model, self.properties, simulator)
        if self.neuron_ref is not None:
            self._create_NEURON(self.neuron_ref)
        if self.nest_ref is not None:
            self._create_NEST(self.nest_ref)
        if self.simulate_neuron:
            simulatorNEURON.run(duration)
        if self.simulate_nest:
            simulatorNEST.reset()
            simulatorNEST.run(duration)
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
            avg_diff = numpy.sum(numpy.abs(signal1 - signal2)) / len(signal1)
            comparisons[tuple(sorted((name1, name2)))] = avg_diff
        return comparisons

    def plot(self):
        legend = []
        for simulator in self.simulators:
            self._plot_9ML(simulator)
            legend.append('{} (9ML-{})'.format(self.nineml_model.name,
                                               simulator.upper()))
        if self.neuron_ref:
            self._plot_NEURON()
            legend.append(self.neuron_ref + ' (NEURON)')
        if self.nest_ref:
            self._plot_NEST()
            legend.append(self.nest_ref + ' (NEST)')
        plt.legend(legend)
        plt.show()

    def _create_9ML(self, model, properties, simulator):
        # -----------------------------------------------------------------
        # Set up 9MLML cell
        # -----------------------------------------------------------------
        if simulator.lower() == 'neuron':
            CellMetaClass = CellMetaClassNEURON
        elif simulator.lower() == 'nest':
            CellMetaClass = CellMetaClassNEST
        else:
            assert False
        self.nml_cells[simulator] = CellMetaClass(
            model, default_properties=properties,
            initial_regime=self.initial_regime,
            **self.build_args[simulator])()
        if self.input_signal is not None:
            self.nml_cells[simulator].play(*self.input_signal)
        if self.input_train is not None:
            self.nml_cells[simulator].play(*self.input_train)
        self.nml_cells[simulator].record(self.state_variable)
        self.nml_cells[simulator].update_state(self.initial_states)

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
        for prop in self.properties:
            name = prop.name
            value = prop.value
            try:
                varname, scale = self.neuron_translations[name]
                value = value * scale
            except (ValueError, KeyError):
                varname = self.neuron_translations.get(name, name)
            if varname in self.specific_params:
                specific_value = UnitHandlerNEURON.to_pq_quantity(
                    Quantity(value, prop.units)) / (100 * (pq.um ** 2))
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
        for name, value in self.initial_states.iteritems():
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
            self._nrn_iclamp = neuron.h.IClamp(0.5, sec=self.nrn_cell_sec)
            self._nrn_iclamp.delay = 0.0
            self._nrn_iclamp.dur = 1e12
            self._nrn_iclamp.amp = 0.0
            self._nrn_iclamp_amps = neuron.h.Vector(pq.Quantity(signal, 'nA'))
            self._nrn_iclamp_times = neuron.h.Vector(pq.Quantity(signal.times,
                                                                 'ms'))
            self._nrn_iclamp_amps.play(self._nrn_iclamp._ref_amp,
                                       self._nrn_iclamp_times)
        if self.input_train is not None:
            _, train = self.input_train
            self._vstim = neuron.h.VecStim()
            self._vstim_times = neuron.h.Vector(pq.Quantity(train, 'ms'))
            self._vstim.play(self._vstim_times)
            target = (self.extra_point_process
                      if self.extra_point_process is not None
                      else self.nrn_cell)
            self._vstim_con = neuron.h.NetCon(
                self._vstim, target, sec=self.nrn_cell_sec)
        # Record Time from NEURON (neuron.h.._ref_t)
        self._nrn_rec = self.NEURONRecorder(self.nrn_cell_sec, self.nrn_cell)
        self._nrn_rec.record(self.neuron_state_variable)

    def _create_NEST(self, nest_name):
        trans_params = {}
        for prop in self.properties:
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
                {'amplitude_values': pq.Quantity(signal, 'pA'),
                 'amplitude_times': (pq.Quantity(signal.times, 'ms') -
                                     self.min_delay * pq.ms),
                 'start': float(pq.Quantity(signal.t_start, 'ms')),
                 'stop': float(pq.Quantity(signal.t_stop, 'ms'))})
            nest.Connect(generator, self.nest_cell,
                         syn_spec={'receptor_type':
                                   (receptor_types[port_name]
                                    if receptor_types else 0),
                                   'delay': self.min_delay})
        if self.input_train is not None:
            port_name, signal = self.input_train
            spike_times = (pq.Quantity(signal, 'ms') - self.min_delay * pq.ms)
            if any(spike_times < 0.0):
                raise Pype9RuntimeError(
                    "Some spike are less than minimum delay and so can't be "
                    "played into cell ({})".format(
                        ', '.join(str(t) for t in
                                  spike_times[spike_times < self.min_delay])))
            generator = nest.Create(
                'spike_generator', 1, {'spike_times': spike_times})
            nest.Connect(generator, self.nest_cell,
                         syn_spec={'receptor_type':
                                   (receptor_types[port_name]
                                    if receptor_types else 0),
                                   'delay': self.min_delay})
        self.nest_multimeter = nest.Create(
            'multimeter', 1, {"interval": self.to_float(self.dt, 'ms')})
        nest.SetStatus(
            self.nest_multimeter,
            {'record_from': [self.nest_state_variable]})
        nest.Connect(self.nest_multimeter, self.nest_cell)
        trans_states = {}
        for name, qty in self.initial_states.iteritems():
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
        plt.plot(pq.Quantity(nest_v.times, 'ms'), pq.Quantity(nest_v, 'mV'))

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
            sampling_period=simulatorNEST.dt * pq.ms, units='mV')  # @UndefinedVariable @IgnorePep8

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


def input_step(port_name, amplitude, start_time, duration, dt):
    num_preceding = int(numpy.floor(start_time / dt))
    num_remaining = int(numpy.ceil((duration - start_time) / dt))
    signal = neo.AnalogSignal(
        numpy.concatenate((numpy.zeros(num_preceding),
                           numpy.ones(num_remaining) * amplitude)),
        sampling_period=dt * pq.ms, units='nA', time_units='ms')
    return (port_name, signal)


def input_freq(port_name, freq, duration):
    isi = 1 / float(pq.Quantity(freq, 'kHz'))
    train = neo.SpikeTrain(
        numpy.arange(isi, duration, isi),
        units='ms', t_stop=duration * pq.ms)
    return (port_name, train)


def compare_in_subprocess(
    state_variable, dt, duration, properties={}, initial_states={},
    nineml_model=None, simulators=[], neuron_ref=None, nest_ref=None,
    input_signal=None, input_train=None, neuron_translations={},
    nest_translations={}, neuron_build_args={}, nest_build_args={},
        min_delay=0.02, max_delay=10.0):
    """
    This function can be used to perform the comparison within a subprocess
    so as to quarantine the simulations from subsequent simulations. Can be
    used if NEURON is failing to exit cleanly
    """
    temp_dir = tempfile.mkdtemp()
    args = [python_cmd_path, compare_script_path]
    if nineml_model is not None:
        nineml_path = os.path.join(temp_dir, nineml_model.name + '.xml')
        nineml_model.write(nineml_path)
        # Add path to 9ML file and the required simulators to the argument
        # list
        args.append(nineml_path)
        args.extend(simulators)
        # Pregenerate the code before entering the subprocess to make
        # debugging easier
        if 'neuron' in simulators:
            CellMetaClassNEURON(nineml_path, **neuron_build_args)
            args.extend(('--build_arg', 'neuron', 'build_mode', 'require'))
        if 'nest' in simulators:
            CellMetaClassNEST(nineml_path, **nest_build_args)
            args.extend(('--build_arg', 'nest', 'build_mode', 'require'))
    args.extend(('--state_variable', state_variable))
    args.extend(('--dt', str(dt)))
    if neuron_ref is not None:
        args.extend(('--neuron_ref', neuron_ref))
    if nest_ref is not None:
        args.extend(('--nest_ref', nest_ref))
    for n, v in properties.iteritems():
        args.extend(('-p', n, str(v)))
    for n, v in initial_states.iteritems():
        args.extend(('-i', n, str(v)))
    if input_signal is not None:
        input_signal_path = os.path.join(temp_dir, 'input_signal.neo.pkl')
        neo.PickleIO(input_signal_path).write(input_signal[1])
        args.extend(('--input_signal', input_signal[0], input_signal_path))
    if input_train is not None:
        input_train_path = os.path.join(temp_dir, 'input_train.neo.pkl')
        neo.PickleIO(input_train_path).write(input_train[1])
        args.extend(('--input_train', input_train[0], input_train_path))
    for o, (n, v) in neuron_translations.iteritems():
        if n is None:
            n = '__none__'
        args.extend(('-u', o, n, str(v)))
    for o, (n, v) in nest_translations.iteritems():
        if n is None:
            n = '__none__'
        args.extend(('-s', o, n, str(v)))
    for k, v in neuron_build_args.iteritems():
        args.extend(('-b', 'neuron', k, v))
    for k, v in nest_build_args.iteritems():
        args.extend(('-b', 'nest', k, v))
    args.extend(('--duration', str(duration)))
    args.extend(('--min_delay', str(min_delay)))
    args.extend(('--max_delay', str(max_delay)))
    try:
        pipe = sp.Popen(args, stdout=sp.PIPE, stderr=sp.PIPE)
        stdout, stderr = pipe.communicate()
    except sp.CalledProcessError as e:
        raise Pype9RuntimeError("Error in comparison: {}\n{}\n{}"
                                .format(e, stdout, stderr))
    if _error_re.search(stderr):
        raise Pype9RuntimeError(
            "Error in comparison subprocess: \n\n{}\n{}"
            .format(stdout, stderr))
    shutil.rmtree(temp_dir)
    print stderr
    comparisons = dict(((n1, n2), pq.Quantity(float(v), u))
                       for n1, n2, v, u in _compare_re.findall(stdout))
    return comparisons

_compare_re = re.compile(r"Average error between ([\w\-]+) and ([\w\-]+): "
                         r"([0-9\.\-e]+) (\w+)")
_error_re = re.compile(r"(\w+)Error:")
