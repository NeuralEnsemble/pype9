if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport
# from pype9.cells.neuron import CellMetaClass
from os import path
from utils import test_data_dir
import pylab as plt
from pype9.cells.nest import (
    CellMetaClass, simulation_controller as simulator)
from nineml.user_layer import Property
from nineml.abstraction_layer import units as un
import quantities as pq
import neo
import nest


class TestNestLoad(TestCase):

    izhikevich_file = path.join(test_data_dir, 'xml', 'Izhikevich2003.xml')
    izhikevich_name = 'IzhikevichBuiltIn'

    def test_nest_load(self):
        Izhikevich9ML = CellMetaClass(
            self.izhikevich_file, name=self.izhikevich_name,
            build_mode='lazy', verbose=True, membrane_voltage='V',
            ode_solver='euler',
            membrane_capacitance=Property('Cm', 0.001, un.nF))
        # ---------------------------------------------------------------------
        # Set up PyNN section
        # ---------------------------------------------------------------------
#         params = {'a': 0.02,
#                   'b': 0.2,
#                   'c': -65.0,
#                   'd': 2}
        pynn = nest.Create('izhikevich')
        multimeter = nest.Create('multimeter')
        nest.SetStatus(multimeter, {'record_from': ['V_m']})
        nest.Connect(multimeter, pynn)
        # ---------------------------------------------------------------------
        # Set up 9ML cell
        # ---------------------------------------------------------------------
        nml = Izhikevich9ML()
        print nml.a
        nml.inject_current(neo.AnalogSignal([0.0] + [0.2] * 9, units='nA',
                                             sampling_period=1 * pq.ms))
        nml.record('V')
        simulator.initialize()  # @UndefinedVariable
        nml.u = -14.0 * pq.mV / pq.ms
        # pnn_izhi.u = -14.0
        simulator.run(1000, reset=False)  # @UndefinedVariable
        nml_v = nml.recording('V')
        pynn_v = neo.AnalogSignal(
            nest.GetStatus(multimeter, 'events')[0]['V_m'],
            sampling_period=simulator.dt * pq.ms, units='mV')  # @UndefinedVariable @IgnorePep8
#         self.assertAlmostEqual(float((nml_v - pnn_v[1:] * pq.mV).sum()), 0)
        plt.plot(pynn_v.times, pynn_v)
        plt.plot(nml_v.times, nml_v)
        plt.legend(('PyNN v', '9ML v'))
        plt.show()


if __name__ == '__main__':
    t = TestNestLoad()
    t.test_nest_load()
