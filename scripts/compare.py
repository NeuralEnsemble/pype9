"""
Command that compares a 9ML model with an existing version in NEURON and/or
NEST
"""
import argparse
import neuron
import nest
from neuron import h
try:
    import pylab as plt
except ImportError:
    plt = None
from pype9.neuron.cells import (
    CellMetaClass as CellMetaClassNEURON,
    simulation_controller as simulatorNEURON)
from pype9.nest.cells import (
    CellMetaClass as CellMetaClassNEST,
    simulation_controller as simulatorNEST)
import numpy
import quantities as pq
import neo


class Comparer(object):

    def compare(self, nineml_model, parameters, state_variable, nineml_sims,
                duration, dt, initial_states, neuron_model=None,
                nest_model=None, analog_signal=None, event_train=None,
                plot=True, min_delay=0.2 * pq.ms, max_delay=10.0 * pq.ms,
                include_passive=False):
        """
        nineml_model   -- 9ML model to compare
        nineml_sims    -- tuple of simulator names to simulate the 9ML model in
        duration       -- simulation duration
        dt             -- simulation time step
        initial_states -- a dictionary of the initial states
        neuron_model   -- a tuple containing the name of neuron model and a
                          dictionary of parameter and state name mappings
        nest_model     -- a tuple containing the name of nest model and a
                          dictionary of parameter and state name mappings
        analog_signal  -- tuple containing the analog signal (in Neo format)
                          and the port to play it into
        event_train    -- tuple containing the event train (in Neo format)
                          and the port to play it into
        """
        simulate_neuron = 'neuron' in nineml_sims or neuron_model is not None
        simulate_nest = 'nest' in nineml_sims or nest_model is not None
        self.dt = self.to_float(dt, 'ms')
        self.min_delay = self.to_float(min_delay, 'ms')
        self.max_delay = self.to_float(max_delay, 'ms')
        if simulate_neuron:
            h.dt = self.dt
        if simulate_nest:
            nest.SetKernelStatus({'resolution': self.dt,
                                  'min_delay': self.min_delay,
                                  'max_delay': self.max_delay})
        for simulator in nineml_sims:
            self._create_9ML(nineml_model, simulator, initial_states,
                             state_variable, analog_signal, event_train)
        if neuron_model is not None:
            neuron_name, translations = neuron_model
            self._create_NEURON(neuron_name, parameters, initial_states,
                                state_variable, analog_signal, event_train,
                                translations, include_passive)
        if nest_model is not None:
            nest_name, translations = nest_model
            self._create_NEST(nest_name, parameters, initial_states,
                              state_variable, analog_signal, event_train,
                              translations)
        # -----------------------------------------------------------------
        # Run and plot the simulation
        # -----------------------------------------------------------------
        if simulate_neuron:
            simulatorNEURON.run(duration)
        if simulate_nest:
            simulatorNEST.run(duration)
        if plot:
            legend = []
            for simulator in nineml_sims:
                self._plot_9ML(simulator)
                legend.append('9ML (' + simulator + ')')
            if neuron_model:
                self._plot_NEURON()
                legend.append(neuron_model[0] + ' (NEURON)')
            if nest_model:
                self._plot_NEST()
                legend.append(nest_model[0] + ' (NEST)')
            plt.legend(legend)
            plt.show()

    def _create_9ML(self, model, simulator, initial_states, state_variable,
                    analog_signal, event_train):
        # -----------------------------------------------------------------
        # Set up 9MLML cell
        # -----------------------------------------------------------------
        if simulator == 'NEURON':
            CellMetaClass = CellMetaClassNEURON
        elif simulator == 'NEST':
            CellMetaClass = CellMetaClassNEST
        else:
            assert False
        self.nml_cells[simulator] = CellMetaClass(model, build_mode='force')()
        if analog_signal is not None:
            self.nml_cells[simulator].play(*analog_signal)
        if event_train is not None:
            self.nml_cells[simulator].play(*event_train)
        self.nml_cells[simulator].record(state_variable)
        self.nml_cells[simulator].update_state(initial_states)

    def _create_NEURON(self, neuron_name, parameters, initial_states,
                       state_variable, analog_signal, event_train,
                       translations, include_passive=False):
        # -----------------------------------------------------------------
        # Set up NEURON section
        # -----------------------------------------------------------------
        self._nrn_pnn = h.Section()
        try:
            self._nrn_pnn_cell = eval(
                'h.{}(0.5, sec=self._nrn_pnn)'.format(neuron_name))
            self._nrn_pnn.L = 10
            self._nrn_pnn.diam = 10 / numpy.pi
            self._nrn_pnn.cm = 1.0
        except TypeError:
            self._nrn_pnn.insert(neuron_name)
            self._nrn_pnn_cell = self._nrn_pnn(0.5)
            self._nrn_pnn.L = 100
            self._nrn_pnn.diam = 1000 / numpy.pi
            self._nrn_pnn.cm = 0.2
        if include_passive:
            self._nrn_pnn.insert('pas')
        for name, value in parameters.iteritems():
            try:
                varname, scale = translations[name]
                value = value * scale
            except (ValueError, KeyError):
                varname = translations.get(name, name)
                value = value
            if varname == 'pas.g':
                self._nrn_pnn(0.5).pas.g = value
            elif varname == 'pas.e':
                self._nrn_pnn(0.5).pas.e = value
            elif varname == 'cm':
                self._nrn_pnn.cm = value
            else:
                setattr(self._nrn_pnn_cell, name, value)
        for name, value in initial_states.iteritems():
            try:
                varname, scale = translations[name]
                value = value * scale
            except (ValueError, KeyError):
                varname = translations.get(name, name)
                value = value
            setattr(self._nrn_pnn_cell, name, value)
        # Specify current injection
        if analog_signal is not None:
            _, signal = analog_signal
            self._nrn_iclamp = h.IClamp(0.5, sec=self._nrn_pnn)
            self._nrn_iclamp.delay = 0.0
            self._nrn_iclamp.dur = 1e12
            self._nrn_iclamp.amp = 0.0
            self._nrn_iclamp_amps = h.Vector(pq.Quantity(signal, 'nA'))
            self._nrn_iclamp_times = h.Vector(pq.Quantity(signal.times, 'ms'))
            self._nrn_iclamp_amps.play(self._nrn_iclamp._ref_amp,
                                       self._nrn_iclamp_times)
        if event_train is not None:
            self._vstim = h.VecStim()
            self._vstim_times = h.Vector(pq.Quantity(signal, 'ms'))
            self._vstim.play(self._vstim_times)
            self._vstim_con = h.NetCon(self._vstim, self._hoc, sec=self._sec)
        # Record Time from NEURON (neuron.h._ref_t)
        self._nrn_rec = self.NEURONRecorder(self._nrn_pnn, self._nrn_pnn_cell)
        translations.get(state_variable, state_variable)
        self._nrn_rec.record()

    def _create_NEST(self, nest_name, parameters, initial_states,
                     state_variable, analog_signal, event_train, translations):
        trans_params = {}
        for name, value in parameters.iteritems():
            try:
                varname, scale = translations[name]
                value = value * scale
            except ValueError:
                varname = translations[name]
                value = value
            trans_params[varname] = value
        self.nest_cells = nest.Create(nest_name, 1, trans_params)
        if analog_signal is not None:
            nest.Create(
                'step_current_generator', 1,
                {'amplitude_values': pq.Quantity(analog_signal, 'pA'),
                 'amplitude_times': (pq.Quantity(analog_signal.times, 'ms') -
                                     self.min_delay * pq.ms),
                 'start': float(pq.Quantity(analog_signal.t_start, 'ms')),
                 'stop': float(pq.Quantity(analog_signal.t_stop, 'ms'))})
            nest.Connect(self.nest_iclamp, self.nest_cells,
                         syn_spec={'delay': self.min_delay})
        self.nest_multimeter = nest.Create(
            'multimeter', 1, {"interval": self.to_float(self.dt, 'ms')})
        nest.SetStatus(
            self.nest_multimeter,
            {'record_from': translations.get(state_variable, state_variable)})
        nest.Connect(self.nest_multimeter, self.nest_cells)
        trans_states = {}
        for name, value in initial_states.iteritems():
            try:
                varname, scale = translations[name]
                value = value * scale
            except ValueError:
                varname = translations[name]
                value = value
            trans_states[varname] = value
        nest.SetStatus(self.nest_cells, trans_states)

    def _plot_NEURON(self):  # @UnusedVariable
        pnn_t, pnn_v = self._get_NEURON_signal()
        plt.plot(pnn_t[:-1], pnn_v[1:])

    def _plot_NEST(self):
        nest_v = self._get_NEST_signal()
        plt.plot(pq.Quantity(nest_v.times, 'ms'), pq.Quantity(nest_v, 'mV'))

    def _plot_9ML(self, sim_name):  # @UnusedVariable
        nml_v = self.nml_cells[sim_name].recording('v')
        plt.plot(nml_v.times, nml_v)

    def _diff_NEURON(self):  # @UnusedVariable
        _, pnn_v = self._get_NEURON_signal()
        nml_v = self.nml_cells['NEURON'].recording('v')
        return float(pq.Quantity((nml_v - pnn_v[1:] * pq.mV).sum(), 'V'))

    def _diff_NEST(self):
        nest_v = self._get_NEST_signal()
        nml_v = self.nml_cells['NEST'].recording('v')
        return float(pq.Quantity((nml_v - nest_v * pq.mV).sum(), 'V'))

    def _get_NEURON_signal(self):
        return self._nrn_rec.recording('v')  # @UnusedVariable

    def _get_NEST_signal(self, translations):
        return neo.AnalogSignal(
            nest.GetStatus(
                self.nest_multimeter, 'events')[0][translations['v']],
            sampling_period=simulatorNEST.dt * pq.ms, units='mV')  # @UndefinedVariable @IgnorePep8

    @classmethod
    def to_float(cls, qty, units):
        return float(pq.Quantity(qty, units))

    class NEURONRecorder(object):

        def __init__(self, sec, mech):
            self.sec = sec
            self.mech = mech
            self.rec_t = h.Vector()
            self.rec_t.record(neuron.h._ref_t)
            self.recs = {}

        def record(self, varname):
            rec = h.Vector()
            self.recs[varname] = rec
            if varname == 'v':
                rec.record(self.sec(0.5)._ref_v)
            elif varname == 'Cm':
                rec.record(self.sec(0.5)._ref_cm)
            else:
                rec.record(getattr(self.mech, '_ref_' + varname))

        def recording(self, varname):
            return numpy.array(self.rec_t), numpy.array(self.recs[varname])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('nineml_model', type=str,
                        help="The 9ML model to compare")
    parser.add_argument('temp', type=int, help="dummy")
    parser.add_argument('--nest', type=str,
                        help="The name of the nest model to compare against")
    parser.add_argument('--neuron', type=str,
                        help="The name of the NEURON model to compare against")
    args = parser.parse_args()
    print args.nineml_model + ', ' + str(args.temp)
