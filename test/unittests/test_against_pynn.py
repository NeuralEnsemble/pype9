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
from pype9.cells.neuron import (
    CellMetaClass as CellMetaClassNEURON,
    simulation_controller as simulatorNEURON)
from pype9.cells.nest import (
    CellMetaClass as CellMetaClassNEST,
    simulation_controller as simulatorNEST)
import numpy
import quantities as pq
import neo
import os

# from pyNN.neuron.cells import Izhikevich_ as IzhikevichPyNN
# MPI may not be required but NEURON sometimes needs to be initialised after
# MPI so I am doing it here just to be safe (and to save me headaches in the
# future)

from math import pi
import pyNN.neuron  # @UnusedImport loads pyNN mechanisms

stim_amp = 20


class TestAgainstPyNN(TestCase):

    xml_dir = path.join(os.environ['HOME'], 'git', 'nineml_catalog',
                        'pynn_nmodl_import', 'neurons')
    models = [('Izhikevich', 'Izhikevich', 'izhikevich'),
              ('AdExpIaF', 'AdExpIF'),
              ('HHTraub', 'hh_traub'),
              ('IF', 'Reset'),
              ('IFRefrac', 'ResetRefrac')]

    initial_states = {'Izhikevich': {'u': -14 * pq.mV / pq.ms,
                                     'v': -65.0 * pq.mV},
                      'AdExpIaF': {'w': 0.0 * pq.nA,
                                   'v': -65 * pq.mV},
                      'HHTraub': {'m': 0.0, 'h': 0.0, 'n': 0.0},
                      'IF': {},
                      'IFRefrac': {}}

    nest_states = {'Izhikevich': {'u': 'U_m', 'v': 'V_m'},
                   'AdExpIaF': {'w': 0.0 * pq.nA, 'v': -65 * pq.mV},
                   'HHTraub': {'m': 0.0, 'h': 0.0, 'n': 0.0},
                   'IF': {},
                   'IFRefrac': {}}

    nest_params = {'Izhikevich': {'a': 0.02, 'c': -65.0, 'b': 0.2, 'd': 2.0},
                   'AdExpIaF': {},
                   'HHTraub': {},
                   'IF': {},
                   'IFRefrac': {}}

    injected_signal = neo.AnalogSignal(
        [0.0] * 2 + [stim_amp] * 93 + [0.0] * 5, sampling_period=1 * pq.ms,
        units='pA')

    order = [0, 1, 2, 3, 4]
    duration = 10 * pq.ms
    dt = 0.01

    def test_against_pyNN_models(
            self,
            plot=False, tests=('nrn9ML', 'nrnPyNN', 'nest9ML', 'nestPyNN')):
        self.nml_cells = {}
        # for name9, namePynn in zip(self.models9ML, self.modelsPyNN):
        for i in self.order:
            name, nameNEURON, nameNEST = self.models[i]
            if 'nrnPyNN' in tests:
                self._create_NEURON(name, nameNEURON)
            if 'nrn9ML' in tests:
                self._create_9ML(name, 'NEURON')
            if 'nestPyNN' in tests:
                self._create_NEST(name, nameNEST)
            if 'nest9ML' in tests:
                self._create_9ML(name, 'NEST')
            # -----------------------------------------------------------------
            # Run and plot the simulation
            # -----------------------------------------------------------------
            if 'nrn9ML' in tests or 'nrnPyNN' in tests:
                simulatorNEURON.run(10.0)
            if 'nest9ML' in tests or 'nestPyNN' in tests:
                simulatorNEST.run(10.0)
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
                    self.assertAlmostEqual(self._diff_NEURON(), 0, places=3)
                if 'nest9ML' in tests or 'nestPyNN' in tests:
                    self.assertAlmostEqual(self._diff_NEST(), 0, places=3)
            break

    def _create_9ML(self, name, sim_name):
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
            path.join(self.xml_dir, name + '.xml'), build_mode='lazy')
        self.nml_cells[sim_name] = CellClass()
        self.nml_cells[sim_name].play('iExt', self.injected_signal)
        self.nml_cells[sim_name].record('v')
        self.nml_cells[sim_name].update_state(self.initial_states[name])

    def _create_NEURON(self, name, model_name):  # @UnusedVariable
        # -----------------------------------------------------------------
        # Set up PyNN section
        # -----------------------------------------------------------------
        self._nrn_pnn = h.Section()
        self._nrn_pnn.L = 10
        self._nrn_pnn.diam = 10 / pi
        self._nrn_pnn.cm = 1.0
        self._nrn_pnn_cell = eval('h.{}(0.5, '
                                  'sec=self._nrn_pnn)'.format(model_name))
        # Specify current injection
        self._nrn_stim = h.IClamp(1.0, sec=self._nrn_pnn)
        self._nrn_stim.delay = 1   # ms
        self._nrn_stim.dur = 100   # ms
        self._nrn_stim.amp = 0.02   # nA
        # Record Time from NEURON (neuron.h._ref_t)
        self._nrn_rec = NEURONRecorder(self._nrn_pnn, self._nrn_pnn_cell)
        self._nrn_rec.record('v')

    def _create_NEST(self, name, model_name):
        # ---------------------------------------------------------------------
        # Set up PyNN section
        # ---------------------------------------------------------------------
        nest.SetKernelStatus({'resolution': 0.01})
        self.nest_cells = nest.Create(model_name, 1, self.nest_params[name])
        self.nest_iclamp = nest.Create(
            'dc_generator', 1,
            {'start': 2.0, 'stop': 95.0,
             'amplitude': float(pq.Quantity(stim_amp, 'pA'))})
        nest.Connect(self.nest_iclamp, self.nest_cells)
        self.nest_multimeter = nest.Create('multimeter', 1,
                                           {"interval": self.dt})
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
    t = TestAgainstPyNN()
    t.test_against_pyNN_models(
        plot=True,
#         tests=('nrn9ML', 'nrnPyNN'))
        tests=('nest9ML', 'nestPyNN'))
#         tests=('nrn9ML', 'nrnPyNN', 'nest9ML', 'nestPyNN'))
