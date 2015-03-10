if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport
from pype9.cells.neuron import CellMetaClass
from os import path
from utils import test_data_dir
import neuron
from neuron import h
import pylab as plt
from pyNN.neuron.cells import Izhikevich_ as IzhikevichPyNN


class TestNeuronLoad(TestCase):

    izhikevich_file = path.join(test_data_dir, 'xml', 'Izhikevich2003.xml')
    izhikevich_name = 'Izhikevich9ML'

    def test_neuron_load(self):
        pnn = IzhikevichPyNN()
        Izhikevich9ML = CellMetaClass(self.izhikevich_file,
                                      name=self.izhikevich_name,
                                      build_mode='compile_only', verbose=True,
                                      membrane_voltage='V',
                                      membrane_capacitance='Cm')
        nml = Izhikevich9ML()
        # PyNN version
        for sec in (pnn, nml.source_section):
            # Specify current injection
            stim = h.IClamp(1.0, sec=sec)
            stim.delay = 1   # ms
            stim.dur = 100   # ms
            stim.amp = 0.2   # nA
            # Record Time from NEURON (neuron.h._ref_t)
            rec_t = neuron.h.Vector()
            rec_t.record(neuron.h._ref_t)
            # Record Voltage from the center of the soma
            rec_v = neuron.h.Vector()
            rec_v.record(sec(0.5)._ref_v)
            neuron.h.finitialize(-60)
            neuron.init()
            neuron.run(5)
            plt.plot(rec_t, rec_v)
        plt.show()


if __name__ == '__main__':
    t = TestNeuronLoad()
    t.test_neuron_load()
