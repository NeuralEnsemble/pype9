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
from nineml.user_layer import Property
from nineml import units as un
import quantities as pq
import neo

# from pyNN.neuron.cells import Izhikevich_ as IzhikevichPyNN
# MPI may not be required but NEURON sometimes needs to be initialised after
# MPI so I am doing it here just to be safe (and to save me headaches in the
# future)

from math import pi
import pyNN.neuron  # @UnusedImport loads pyNN mechanisms


class TestNeuronLoad(TestCase):

    izhikevich_file = path.join(test_data_dir, 'xml', 'Izhikevich2003.xml')
    izhikevich_name = 'Izhikevich9ML'

    def test_neuron_load(self):
        Izhikevich9ML = CellMetaClass(
            self.izhikevich_file, name=self.izhikevich_name,
            build_mode='force', verbose=True, membrane_voltage='V',
            membrane_capacitance=Property('Cm', 0.001, un.nF))
        # ---------------------------------------------------------------------
        # Set up PyNN section
        # ---------------------------------------------------------------------
        pnn = h.Section()
        pnn.L = 10
        pnn.diam = 10 / pi
        pnn.cm = 1.0
        pnn_izhi = h.Izhikevich(0.5, sec=pnn)  # @UnusedVariable
        # Specify current injection
        stim = h.IClamp(1.0, sec=pnn)
        stim.delay = 1   # ms
        stim.dur = 100   # ms
        stim.amp = 0.2   # nA
        # Record Time from NEURON (neuron.h._ref_t)
        rec = Recorder(pnn, pnn_izhi)
        rec.record('v')
        # ---------------------------------------------------------------------
        # Set up 9ML cell
        # ---------------------------------------------------------------------
        izhi = Izhikevich9ML()
        print izhi.a
        izhi.inject_current(neo.AnalogSignal([0.0] + [0.2] * 9, units='nA',
                                             sampling_period=1 * pq.ms))
        izhi.record('v')
        simulator.initialize()  # @UndefinedVariable
        izhi.u = -14.0 * pq.mV / pq.ms
        pnn_izhi.u = -14.0
        simulator.run(10, reset=False)  # @UndefinedVariable
        nml_v = izhi.recording('v')
        pnn_t, pnn_v = rec.recording('v')  # @UnusedVariable
        self.assertAlmostEqual(float((nml_v - pnn_v[1:] * pq.mV).sum()), 0)
        plt.plot(pnn_t[:-1], pnn_v[1:])
        plt.plot(nml_v.times, nml_v)
        plt.legend(('PyNN v', '9ML v'))
        plt.show()
        h.quit()


# class TestNeuronMWE(TestCase):
# 
#     def test_neuron_load(self):
#         # ---------------------------------------------------------------------
#         # Set up PyNN section
#         # ---------------------------------------------------------------------
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
