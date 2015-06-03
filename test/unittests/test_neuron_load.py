if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport
# from pype9.cells.neuron import CellMetaClass
from os import path
from utils import test_data_dir
import neuron
from neuron import h
import pylab as plt
from pype9.cells.neuron import (
    CellMetaClass, simulation_controller as simulator)
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


class TestNeuronLoad(TestCase):

    izhikevich_file = path.join(test_data_dir, 'xml', 'Izhikevich2003.xml')
    izhikevich_name = 'Izhikevich9ML'
    models9ML = ['AdExpIF', 'HHTraub', 'IF', 'IFRefrac', 'Izhikevich']
    modelsPyNN = ['AdExpIF', 'hh_traub', 'Reset', 'ResetRefrac', 'Izhikevich']
    pyNN_import_dir = path.join(os.environ['HOME'], 'git', 'nineml_catalog',
                                'pynn_nmodl_import', 'neurons')

    initial_states = {'Izhikevich': {'u': -14 * pq.mV / pq.ms,
                                     'v': -65.0 * pq.mV},
                      'AdExpIaF': {'w': 0.0 * pq.nA,
                                   'v': -65 * pq.mV}}

    def test_neuron_load(self):
        # for name9, namePynn in zip(self.models9ML, self.modelsPyNN):
        for name9, namePynn in (
#                                 ('Izhikevich', 'Izhikevich'),
                                ('AdExpIaF', 'AdExpIF'),
                                ):
            # -----------------------------------------------------------------
            # Set up PyNN section
            # -----------------------------------------------------------------
            pnn = h.Section()
            pnn.L = 10
            pnn.diam = 10 / pi
            pnn.cm = 1.0
            pnn_cell = eval('h.{}(0.5, sec=pnn)'.format(namePynn))
            # Specify current injection
            stim = h.IClamp(1.0, sec=pnn)
            stim.delay = 1   # ms
            stim.dur = 100   # ms
            stim.amp = 0.02   # nA
            # Record Time from NEURON (neuron.h._ref_t)
            rec = Recorder(pnn, pnn_cell)
            rec.record('v')
            # -----------------------------------------------------------------
            # Set up 9ML cell
            # -----------------------------------------------------------------
            CellClass = CellMetaClass(
                path.join(self.pyNN_import_dir, name9 + '.xml'),
                name=name9 + 'Properties', build_mode='force')
            cell9 = CellClass()
            cell9.play('iExt', neo.AnalogSignal(
                [0.0] + [stim.amp] * 9, units='nA', sampling_period=1 * pq.ms))
            cell9.record('v')
            cell9.update_state(self.initial_states[name9])

            # Hacks to fix
            cell9._sec.cm = 1.0
#             pnn.L = 100
#             pnn.diam = 100 / pi
#             cell9._sec.L = 100
#             cell9._sec.diam = 100 / pi
            # -----------------------------------------------------------------
            # Run and plot the simulation
            # -----------------------------------------------------------------
            simulator.run(10.0, reset=False)  # @UndefinedVariable
            nml_v = cell9.recording('v')
            pnn_t, pnn_v = rec.recording('v')  # @UnusedVariable
            plt.plot(pnn_t[:-1], pnn_v[1:])
            plt.plot(nml_v.times, nml_v)
            plt.legend(('PyNN v', '9ML v'))
            plt.show()
            self.assertAlmostEqual(float((nml_v - pnn_v[1:] * pq.mV).sum()), 0)
            h.quit()


# class TestNeuronMWE(TestCase):
# 
#     def test_neuron_load(self):
#         # -------------------------------------------------------------------
#         # Set up PyNN section
#         # -------------------------------------------------------------------
#         pnn = h.Section()
#         pnn.L = 10
#         pnn.diam = 10 / pi
#         pnn.cm = 1.0
#         pnn_izhi = h.Izhikevich(0.5, sec=pnn)  # @UnusedVariable
#         # Specify current injection
#         stim = h.IClamp(1.0, sec=pnn)
#         stim.delay = 1   # ms
#         stim.dur = 100   # ms
#         stim.amp = 0.2   # nA
#         # Record Time from NEURON (neuron.h._ref_t)
#         rec = h.Vector()
#         rec.record(pnn(0.5)._ref_v)
#         # ---------------------------------------------------------------------
#         # Set up 9ML cell
#         # ---------------------------------------------------------------------
#         izhi = Izhikevich9ML()
#         print izhi.a
#         izhi.inject_current(neo.AnalogSignal([0.0] + [0.2] * 9, units='nA',
#                                              sampling_period=1 * pq.ms))
#         izhi.record('v')
#         simulator.initialize()  # @UndefinedVariable
#         izhi.u = -14.0 * pq.mV / pq.ms
#         pnn_izhi.u = -14.0
#         simulator.run(10, reset=False)  # @UndefinedVariable
#         nml_v = izhi.recording('v')
#         pnn_t, pnn_v = rec.recording('v')  # @UnusedVariable
#         self.assertAlmostEqual(float((nml_v - pnn_v[1:] * pq.mV).sum()), 0)
#         plt.plot(pnn_t[:-1], pnn_v[1:])
#         plt.plot(nml_v.times, nml_v)
#         plt.legend(('PyNN v', '9ML v'))
#         plt.show()
#         h.quit()


class Recorder(object):

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
    t = TestNeuronLoad()
    t.test_neuron_load()
