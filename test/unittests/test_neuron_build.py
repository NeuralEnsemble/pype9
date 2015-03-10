if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport
from pype9.cells.code_gen.neuron import CodeGenerator
from os import path
from utils import test_data_dir
import neuron
from neuron import h, init, run
import pylab as plt
from pyNN.neuron.cells import Izhikevich_


class TestNeuronBuild(TestCase):

    izhikevich_file = path.join(test_data_dir, 'xml', 'Izhikevich.xml')
    izhikevich_name = 'Izhikevich9ML'

    def setUp(self):
        self.code_generator = CodeGenerator()

    def test_neuron_build(self):
        self.code_generator.generate(self.izhikevich_file,
                                     name=self.izhikevich_name,
                                     build_mode='force',
                                     ode_solver='derivimplicit',
                                     membrane_voltage='V',
                                     membrane_capacitance='Cm')

    def test_kinetics_build(self):
        component_file = path.join(test_data_dir, 'xml',
                                   'kinetic_mechanism.xml')
        self.code_generator.generate(component_file,
                                     build_mode='force',
                                     ode_solver='derivimplicit')

    def test_built_mechanism(self):
#         self.code_generator.generate(self.izhikevich_file,
#                                      name=self.izhikevich_name,
#                                      build_mode='lazy',
#                                      ode_solver='derivimplicit',
#                                      membrane_voltage='V',
#                                      membrane_capacitance='Cm')
        izhi = Izhikevich_()

        # Specify current injection
        stim = h.IClamp(1.0, sec=izhi)
        stim.delay = 1   # ms
        stim.dur = 100   # ms
        stim.amp = 0.2   # nA

        # Record Time from NEURON (neuron.h._ref_t)
        rec_t = neuron.h.Vector()
        rec_t.record(neuron.h._ref_t)
        # Record Voltage from the center of the soma
        rec_v = neuron.h.Vector()
        rec_v.record(izhi(0.5)._ref_v)

        neuron.h.finitialize(-60)
        neuron.init()
        neuron.run(5)

        plt.plot(rec_t, rec_v)
        plt.show()

if __name__ == '__main__':
    t = TestNeuronBuild()
    t.test_built_mechanism()
#     t.test_neuron_build()
