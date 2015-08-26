"""
Command that compares a 9ML model with an existing version in NEURON and/or
NEST
"""
import argparse
from os import path
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

    models = [('Izhikevich2003', 'Izhikevich', 'izhikevich'),
              ('AdExpIaF', 'AdExpIF', 'aeif_cond_alpha'),
              ('HodgkinHuxley', 'hh_traub', 'hh_cond_exp_traub'),
              ('LeakyIntegrateAndFire', 'ResetRefrac', 'iaf_psc_alpha')]

    initial_states = {'Izhikevich2003': {'u': -14 * pq.mV / pq.ms,
                                         'v': -65.0 * pq.mV},
                      'AdExpIaF': {'w': 0.0 * pq.nA,
                                   'v': -65 * pq.mV},
                      'HodgkinHuxley': {'v': -65 * pq.mV,
                                        'm': 0, 'h': 1, 'n': 0},
                      'LeakyIntegrateAndFire': {'v': -65 * pq.mV,
                                                'end_refractory': 0.0}}

    neuron_pas = {'Izhikevich2003': None,
                  'AdExpIaF': None,
                  'HodgkinHuxley': None,
                  'LeakyIntegrateAndFire': {'g': 0.00025, 'e': -70}}
    neuron_params = {'Izhikevich2003': None,
                     'AdExpIaF': None,
                     'HodgkinHuxley': None,
                     'LeakyIntegrateAndFire': {
                         'vthresh': -55,
                         'vreset': -70,
                         'trefrac': 2}}

    nest_states = {'Izhikevich2003': {'u': 'U_m', 'v': 'V_m'},
                   'AdExpIaF': {'w': 'w', 'v': 'V_m'},
                   'HodgkinHuxley': {'v': 'V_m', 'm': 'Act_m', 'h': 'Act_h',
                                     'n': 'Inact_n'},
                   'LeakyIntegrateAndFire': {'v': 'V_m',
                                             'end_refractory': None}}
    nest_params = {'Izhikevich2003': {'a': 0.02, 'c': -65.0, 'b': 0.2,
                                      'd': 2.0},
                   'AdExpIaF': {},
                   'HodgkinHuxley': {},
                   'LeakyIntegrateAndFire': {"C_m": 250.0,
                                             "tau_m": 20.0,
                                             "tau_syn_ex": 0.5,
                                             "tau_syn_in": 0.5,
                                             "t_ref": 2.0,
                                             "E_L": 0.0,
                                             "V_reset": 0.0,
                                             "V_m": 0.0,
                                             "V_th": 20.0}}
    paradigms = {'Izhikevich2003': {'duration': 100 * pq.ms,
                                    'stim_amp': 0.02 * pq.nA,
                                    'stim_start': 20 * pq.ms,
                                    'dt': 0.02 * pq.ms},
                 'AdExpIaF': {'duration': 50 * pq.ms,
                              'stim_amp': 1 * pq.nA,
                              'stim_start': 25 * pq.ms,
                              'dt': 0.002 * pq.ms},
                 'HodgkinHuxley': {'duration': 100 * pq.ms,
                                   'stim_amp': 0.5 * pq.nA,
                                   'stim_start': 50 * pq.ms,
                                   'dt': 0.002 * pq.ms},
                 'LeakyIntegrateAndFire': {'duration': 50 * pq.ms,
                                           'stim_amp': 1 * pq.nA,
                                           'stim_start': 25 * pq.ms,
                                           'dt': 0.002 * pq.ms}}

#     order = [0, 1, 2, 3, 4]
    order = [2, 2, 3]
    min_delay = 0.04
    max_delay = 10

    def test_cells(
            self, plot=False, build_mode='force',
            tests=('nrn9ML', 'nrnPyNN', 'nest9ML', 'nestPyNN')):
        self.nml_cells = {}
        # for name9, namePynn in zip(self.models9ML, self.modelsPyNN):
        for i in self.order:
            name, nameNEURON, nameNEST = self.models[i]
            paradigm = self.paradigms[name]
            stim_amp = paradigm['stim_amp']
            duration = to_float(paradigm['duration'], 'ms')
            stim_start = to_float(paradigm['stim_start'], 'ms')
            dt = paradigm['dt']
            if 'nrn9ML' in tests or 'nrnPyNN' in tests:
                h.dt = to_float(dt, 'ms')
            if 'nest9ML' in tests or 'nestPyNN' in tests:
                nest.SetKernelStatus({'resolution': to_float(dt, 'ms')})
            injected_signal = neo.AnalogSignal(
                ([0.0] * int(stim_start) + [stim_amp] * int(duration)),
                sampling_period=1 * pq.ms, units='nA')
            if 'nrnPyNN' in tests:
                self._create_NEURON(name, nameNEURON, stim_start, stim_amp,
                                    duration)
            if 'nrn9ML' in tests:
                self._create_9ML(name, 'NEURON', build_mode, injected_signal)
            if 'nestPyNN' in tests:
                self._create_NEST(name, nameNEST, stim_start, stim_amp,
                                  duration, dt)
            if 'nest9ML' in tests:
                self._create_9ML(name, 'NEST', build_mode, injected_signal)
            # -----------------------------------------------------------------
            # Run and plot the simulation
            # -----------------------------------------------------------------
            if 'nrn9ML' in tests or 'nrnPyNN' in tests:
                simulatorNEURON.run(duration)
            if 'nest9ML' in tests or 'nestPyNN' in tests:
                simulatorNEST.run(duration)
            if plot:
                leg = []
                if 'nrnPyNN' in tests:
                    self._plot_NEURON(name)
                    leg.append('PyNN NEURON')
                if 'nrn9ML' in tests:
                    self._plot_9ML(name, 'NEURON')
                    leg.append('9ML NEURON')
                if 'nestPyNN' in tests:
                    self._plot_NEST(name)
                    leg.append('PyNN NEST')
                if 'nest9ML' in tests:
                    self._plot_9ML(name, 'NEST')
                    leg.append('9ML NEST')
                plt.legend(leg)
                plt.show()
            else:
                if 'nrn9ML' in tests or 'nrnPyNN' in tests:
                    self.assertAlmostEqual(self._diff_NEURON(name), 0,
                                           places=3)
                if 'nest9ML' in tests or 'nestPyNN' in tests:
                    self.assertAlmostEqual(self._diff_NEST(name), 0, places=3)
            break

    def _create_9ML(self, name, sim_name, build_mode, injected_signal):
        # -----------------------------------------------------------------
        # Set up 9MLML cell
        # -----------------------------------------------------------------
        if sim_name == 'NEURON':
            CellMetaClass = CellMetaClassNEURON
        elif sim_name == 'NEST':
            CellMetaClass = CellMetaClassNEST
        else:
            assert False
        CellClass = CellMetaClass(
            path.join(xml_dir, name + '.xml'), build_mode=build_mode)
        self.nml_cells[sim_name] = CellClass()
        self.nml_cells[sim_name].play('iExt', injected_signal)
        self.nml_cells[sim_name].record('v')
        self.nml_cells[sim_name].update_state(self.initial_states[name])

    def _create_NEURON(self, name, model_name, stim_start, stim_amp, duration):  # @UnusedVariable @IgnorePep8
        # -----------------------------------------------------------------
        # Set up PyNN section
        # -----------------------------------------------------------------
        self._nrn_pnn = h.Section()
        try:
            self._nrn_pnn_cell = eval(
                'h.{}(0.5, sec=self._nrn_pnn)'.format(model_name))
            self._nrn_pnn.L = 10
            self._nrn_pnn.diam = 10 / pi
            self._nrn_pnn.cm = 1.0
        except TypeError:
            self._nrn_pnn.insert(model_name)
            self._nrn_pnn_cell = self._nrn_pnn(0.5)
            self._nrn_pnn.L = 100
            self._nrn_pnn.diam = 1000 / pi
            self._nrn_pnn.cm = 0.2
#         if self.neuron_params[name] is not None:
#             for k, v in self.neuron_params[name].iteritems():
#                 setattr(getattr(self._nrn_pnn(0.5), model_name), k, v)
        if self.neuron_pas[name] is not None:
            self._nrn_pnn.insert('pas')
            self._nrn_pnn(0.5).pas.g = self.neuron_pas[name]['g']
            self._nrn_pnn(0.5).pas.e = self.neuron_pas[name]['e']
        # Specify current injection
        self._nrn_stim = h.IClamp(1.0, sec=self._nrn_pnn)
        self._nrn_stim.delay = stim_start   # ms
        self._nrn_stim.dur = duration   # ms
        self._nrn_stim.amp = to_float(stim_amp, 'nA')   # nA
        # Record Time from NEURON (neuron.h._ref_t)
        self._nrn_rec = NEURONRecorder(self._nrn_pnn, self._nrn_pnn_cell)
        self._nrn_rec.record('v')

    def _create_NEST(self, name, model_name, stim_start, stim_amp, duration,
                     dt):
        # ---------------------------------------------------------------------
        # Set up PyNN section
        # ---------------------------------------------------------------------
        self.nest_cells = nest.Create(model_name, 1, self.nest_params[name])
        self.nest_iclamp = nest.Create(
            'dc_generator', 1,
            {'start': stim_start - self.min_delay,
             'stop': duration,
             'amplitude': to_float(stim_amp, 'pA')})
        nest.Connect(self.nest_iclamp, self.nest_cells,
                     syn_spec={'delay': self.min_delay})
        self.nest_multimeter = nest.Create('multimeter', 1,
                                           {"interval": to_float(dt, 'ms')})
        nest.SetStatus(self.nest_multimeter,
                       {'record_from': [self.nest_states[name]['v']]})
        nest.Connect(self.nest_multimeter, self.nest_cells)
        nest.SetStatus(
            self.nest_cells,
            dict((self.nest_states[name][n], float(v))
                 for n, v in self.initial_states[name].iteritems()
                 if self.nest_states[name][n] is not None))

    def _plot_NEURON(self, name):  # @UnusedVariable
        pnn_t, pnn_v = self._get_NEURON_signal()
        plt.plot(pnn_t[:-1], pnn_v[1:])

    def _plot_NEST(self, name):
        nest_v = self._get_NEST_signal(name)
        plt.plot(pq.Quantity(nest_v.times, 'ms'), pq.Quantity(nest_v, 'mV'))

    def _plot_9ML(self, name, sim_name):  # @UnusedVariable
        nml_v = self.nml_cells[sim_name].recording('v')
        plt.plot(nml_v.times, nml_v)

    def _diff_NEURON(self, name):  # @UnusedVariable
        _, pnn_v = self._get_NEURON_signal()
        nml_v = self.nml_cells['NEURON'].recording('v')
        return float(pq.Quantity((nml_v - pnn_v[1:] * pq.mV).sum(), 'V'))

    def _diff_NEST(self, name):
        nest_v = self._get_NEST_signal(name)
        nml_v = self.nml_cells['NEST'].recording('v')
        return float(pq.Quantity((nml_v - nest_v * pq.mV).sum(), 'V'))

    def _get_NEURON_signal(self):
        return self._nrn_rec.recording('v')  # @UnusedVariable

    def _get_NEST_signal(self, name):
        return neo.AnalogSignal(
            nest.GetStatus(
                self.nest_multimeter, 'events')[0][
                    self.nest_states[name]['v']],
            sampling_period=simulatorNEST.dt * pq.ms, units='mV')  # @UndefinedVariable @IgnorePep8


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
    parser.add_argument('nineml_model', type=str, help="The 9ML model to compare")
    parser.add_argument('temp', type=int, help="dummy")
    parser.add_argument('--nest', type=str,
                        help="The name of the nest model to compare against")
    parser.add_argument('--neuron', type=str,
                        help="The name of the NEURON model to compare against")
    args = parser.parse_args()
    print args.nineml_model + ', ' + str(args.temp)
