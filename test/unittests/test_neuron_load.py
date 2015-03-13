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
import neo
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
        Izhikevich9ML = CellMetaClass(self.izhikevich_file,
                                      name=self.izhikevich_name,
                                      build_mode='compile_only', verbose=True,
                                      membrane_voltage='V',
                                      membrane_capacitance='Cm')
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
        rec_t = neuron.h.Vector()
        rec_t.record(neuron.h._ref_t)
        # Record Voltage from the center of the soma
        rec_v = neuron.h.Vector()
        rec_v.record(pnn(0.5)._ref_v)
        # ---------------------------------------------------------------------
        # Set up 9ML cell
        # ---------------------------------------------------------------------
        nml = Izhikevich9ML()
        nml.inject_current(neo.AnalogSignal([1.0], units='nA',
                                            sampling_period=100 * pq.ms))
        nml.record('v')
        simulator.run(10)
        v = nml.recording('v')
        pnn_v = numpy.array(rec_v)
        pnn_t = numpy.array(rec_t)
        plt.plot(pnn_t, pnn_v)
        plt.plot(v.times, v)
        plt.show()
        h.quit()


if __name__ == '__main__':
    t = TestNeuronLoad()
    t.test_neuron_load()
