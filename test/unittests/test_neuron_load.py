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
from nineml.abstraction_layer import units as un
import quantities as pq

# from pyNN.neuron.cells import Izhikevich_ as IzhikevichPyNN
# MPI may not be required but NEURON sometimes needs to be initialised after
# MPI so I am doing it here just to be safe (and to save me headaches in the
# future)

from math import pi
import pyNN.neuron  # @UnusedImport loads pyNN mechanisms


class Cell(object):

    def __init__(self):
        self.source_section = h.Section()  # @UndefinedVariable
        self._hoc = h.Izhikevich9ML(0.5, sec=self.source_section)


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
        tests = ('v', 'Cm')
        for test in tests:
            rec.record(test)
        # ---------------------------------------------------------------------
        # Set up 9ML cell
        # ---------------------------------------------------------------------
#         izhi = Izhikevich9ML(a=0.02 * 1 / pq.ms, b=0.2 * 1.0 / pq.ms,
#                              c=-65.0 * pq.mV, d=2 * pq.mV / pq.ms,
#                              vthresh=30 * pq.mV)
        izhi = Izhikevich9ML()
        print izhi.a
#         izhi.inject_current(neo.AnalogSignal([0.0] + [0.2] * 9, units='nA',
#                                             sampling_period=1 * pq.ms))
        stim2 = h.IClamp(1.0, sec=izhi.source_section)
        stim2.delay = 1   # ms
        stim2.dur = 100   # ms
        stim2.amp = 0.2   # nA
        for test in tests:
            izhi.record(test)
        simulator.initialize()  # @UndefinedVariable
        izhi.u = -14 * pq.mV / pq.ms
        simulator.run(10, reset=False)  # @UndefinedVariable
        leg = []
        for test in tests:
            n = izhi.recording(test)
            t, p = rec.recording(test)
            plt.plot(t, p)
            plt.plot(n.times, n)
            leg.extend(('PyNN ' + test, '9ML ' + test))
        plt.legend(leg)
        plt.show()
        h.quit()


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
