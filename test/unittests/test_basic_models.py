if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport
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
from pype9.nest.units import UnitHandler
import numpy
import quantities as pq
import neo
import os

UnitHandler.clear_cache()

# from pyNN.neuron.cells import Izhikevich_ as IzhikevichPyNN
# MPI may not be required but NEURON sometimes needs to be initialised after
# MPI so I am doing it here just to be safe (and to save me headaches in the
# future)

from math import pi
import pyNN.neuron  # @UnusedImport loads pyNN mechanisms


def to_float(qty, units):
    return float(pq.Quantity(qty, units))


xml_dir = path.join(os.environ['HOME'], 'git', 'nineml_catalog', 'neurons')


tauSyn = 0.5
CMem = 250.0
tauMem = 20.0
theta = 20.0


class TestBasicNeuronModels(TestCase):

    models = [('Izhikevich2003', 'Izhikevich', 'izhikevich'),
              ('AdExpIaF', 'AdExpIF', 'aeif_cond_alpha'),
              ('HodgkinHuxley', 'hh_traub', 'hh_cond_exp_traub'),
              ('IaF', 'ResetRefrac', 'iaf_psc_alpha')]

    initial_states = {'Izhikevich2003': {'u': -14 * pq.mV / pq.ms,
                                         'v': -65.0 * pq.mV},
                      'AdExpIaF': {'w': 0.0 * pq.nA,
                                   'v': -65 * pq.mV},
                      'HodgkinHuxley': {'v': -65 * pq.mV,
                                        'm': 0, 'h': 1, 'n': 0},
                      'IaF': {'v': -65 * pq.mV}}

    nest_states = {'Izhikevich2003': {'u': 'U_m', 'v': 'V_m'},
                   'AdExpIaF': {'w': 'w', 'v': 'V_m'},
                   'HodgkinHuxley': {'v': 'V_m', 'm': 'Act_m', 'h': 'Act_h',
                                     'n': 'Inact_n'},
                   'IaF': {'v': 'V_m'}}
    nest_params = {'Izhikevich2003': {'a': 0.02, 'c': -65.0, 'b': 0.2,
                                      'd': 2.0},
                   'AdExpIaF': {},
                   'HodgkinHuxley': {},
                   'IaF': {}}
#                    'IaF': {"C_m": CMem,
#                            "tau_m": tauMem,
#                            "tau_syn_ex": tauSyn,
#                            "tau_syn_in": tauSyn,
#                            "t_ref": 2.0,
#                            "E_L": 0.0,
#                            "V_reset": 0.0,
#                            "V_m": 0.0,
#                            "V_th": theta}}
    paradigms = {'Izhikevich2003': {'duration': 100 * pq.ms,
                                    'stim_amp': 0.02 * pq.nA,
                                    'stim_start': 20 * pq.ms,
                                    'dt': 0.02 * pq.ms},
                 'HodgkinHuxley': {'duration': 100 * pq.ms,
                                   'stim_amp': 0.5 * pq.nA,
                                   'stim_start': 50 * pq.ms,
                                   'dt': 0.002 * pq.ms},
                 'IaF': {'duration': 0.1 * pq.ms,
                                   'stim_amp': 0.5 * pq.nA,
                                   'stim_start': 50 * pq.ms,
                                   'dt': 0.002 * pq.ms}}

#     order = [0, 1, 2, 3, 4]
    order = [3, 2, 3, 4]
    min_delay = 0.04
    max_delay = 10

    def test_basic_models(
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
                 for n, v in self.initial_states[name].iteritems()))

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
    t = TestBasicNeuronModels()
    t.test_basic_models(
        plot=True, build_mode='force',
# #         tests=('nrn9ML', 'nrnPyNN'))
#         tests=('nest9ML', 'nestPyNN'))
#         tests=('nestPyNN',))
        tests=('nrn9ML', 'nrnPyNN', 'nest9ML', 'nestPyNN'))
