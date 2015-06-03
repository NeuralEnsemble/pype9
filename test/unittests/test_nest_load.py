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
from nineml.user import Property
from nineml import units as un
import quantities as pq
import neo
import nest


class TestNestLoad(TestCase):

    dt = 0.01
    amp = 25.0

    izhikevich_file = path.join('/Users', 'tclose', 'git', 'nineml_catalog',
                                'pynn_nmodl_import', 'neurons',
                                'Izhikevich.xml')
    izhikevich_name = 'Izhikevich'

    def test_nest_load(self):
        # ---------------------------------------------------------------------
        # Set up PyNN section
        # ---------------------------------------------------------------------
        nest.SetKernelStatus({'resolution': 0.01})
        pynn_cells = nest.Create(
            'izhikevich', 1,
            {'a': 0.02, 'c': -65.0, 'b': 0.2, 'd': 6.0})
        pynn_iclamp = nest.Create(
            'dc_generator', 1, {'start': 2.0, 'stop': 95.0,
                                'amplitude': self.amp})
        nest.Connect(pynn_iclamp, pynn_cells)
        pynn_multimeter = nest.Create('multimeter', 1, {"interval": self.dt})
        nest.SetStatus(pynn_multimeter, {'record_from': ['V_m', 'U_m']})
        nest.Connect(pynn_multimeter, pynn_cells)
        nest.SetStatus(pynn_cells, {'V_m': -70.0, 'U_m': -14.0})
        # ---------------------------------------------------------------------
        # Set up 9ML cell
        # ---------------------------------------------------------------------
        Izhikevich9ML = CellMetaClass(
            self.izhikevich_file, name=self.izhikevich_name,
            build_mode='lazy', verbose=True, ode_solver='euler',
            ss_solver=None)
        nml = Izhikevich9ML()
        nml.play('iExt',
                 neo.AnalogSignal([0.0] * 2 + [self.amp] * 93 + [0.0] * 5,
                                  sampling_period=1 * pq.ms, units='nA'))
        nml.record('V_m')
        nml.record('u')
        nml.update_state({'V_m': -70 * pq.mV,
                          'u': -14.0 * pq.mV / pq.ms})
        simulator.initialize()  # @UndefinedVariable
        # ---------------------------------------------------------------------
        # Run Simulation
        # ---------------------------------------------------------------------
        simulator.run(100, reset=False)  # @UndefinedVariable
        # ---------------------------------------------------------------------
        # Get PyNN results
        # ---------------------------------------------------------------------
        pynn_v = neo.AnalogSignal(
            nest.GetStatus(pynn_multimeter, 'events')[0]['V_m'],
            sampling_period=simulator.dt * pq.ms, units='mV')  # @UndefinedVariable @IgnorePep8
        pynn_u = neo.AnalogSignal(
            nest.GetStatus(pynn_multimeter, 'events')[0]['U_m'],
            sampling_period=simulator.dt * pq.ms, units='mV')  # @UndefinedVariable @IgnorePep8
        # ---------------------------------------------------------------------
        # Get 9ML results
        # ---------------------------------------------------------------------
        nml_v = nml.recording('V_m')
        nml_u = nml.recording('u')
        # ---------------------------------------------------------------------
        # Plot voltage
        # ---------------------------------------------------------------------
        plt.figure()
        plt.plot(pq.Quantity(pynn_v.times, 'ms'), pq.Quantity(pynn_v, 'mV'))
        plt.plot(pq.Quantity(nml_v.times, 'ms'), pq.Quantity(nml_v, 'mV'))
        plt.legend(('PyNN v', '9ML v'))
        # ---------------------------------------------------------------------
        # Plot U
        # ---------------------------------------------------------------------
        plt.figure()
        plt.plot(pq.Quantity(pynn_u.times, 'ms'), pynn_u)
        plt.plot(pq.Quantity(nml_u.times, 'ms'), nml_u)
        plt.legend(('PyNN u', '9ML u'))
        plt.show()
        self.assertAlmostEqual(
            float((pynn_v - nml_v).sum()), 0.0,
            msg="9ML version of Izhikevich model does not match built-in.")
