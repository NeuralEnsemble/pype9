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
from nineml import units as un
import quantities as pq
import neo
import nest


class TestNestLoad(TestCase):

    dt = 0.01

    izhikevich_file = path.join(test_data_dir, 'xml', 'Izhikevich2003.xml')
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
            'dc_generator', 1, {'start': 2.0, 'stop': 95.0, 'amplitude': 25.0})
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
            build_mode='force', verbose=True, membrane_voltage='V_m',
            ode_solver='euler', ss_solver=None,
            membrane_capacitance=Property('Cm', 0.001, un.nF))
        nml = Izhikevich9ML()
        nml_iclamp = nest.Create(
            'dc_generator', 1, {'start': 2.0, 'stop': 95.0, 'amplitude': 25.0})
        nest.Connect(nml_iclamp, nml._cell,
                     syn_spec={"receptor_type": nml.receive_ports['iExt']})
#         nml.inject_current(neo.AnalogSignal([0.0] + [0.2] * 9, units='nA',
#                                             sampling_period=1 * pq.ms))
        nml.record('V_m')
        nml.record('U_m')
        simulator.initialize()  # @UndefinedVariable
        nml.V_m = -70 * pq.mV
        nml.U_m = -14.0 * pq.mV / pq.ms
        # ---------------------------------------------------------------------
        # Run Simulation
        # ---------------------------------------------------------------------
        simulator.run(100, reset=False)  # @UndefinedVariable
        # ---------------------------------------------------------------------
        # Get PyNN results
        # ---------------------------------------------------------------------
        pynn_v = neo.AnalogSignal(
            nest.GetStatus(pynn_multimeter, 'events')[0]['V_m'],
            sampling_period=simulator.dt * pq.s, units='mV')  # @UndefinedVariable @IgnorePep8
        pynn_u = neo.AnalogSignal(
            nest.GetStatus(pynn_multimeter, 'events')[0]['U_m'],
            sampling_period=simulator.dt * pq.s, units='mV')  # @UndefinedVariable @IgnorePep8
        # ---------------------------------------------------------------------
        # Get 9ML results
        # ---------------------------------------------------------------------
        nml_v = nml.recording('V_m')
        nml_u = nml.recording('U_m')
        # ---------------------------------------------------------------------
        # Plot voltage
        # ---------------------------------------------------------------------
        plt.figure()
        plt.plot(pynn_v.times, pynn_v)
        plt.plot(nml_v.times * 100, nml_v)
        plt.legend(('PyNN v', '9ML v'))
        # ---------------------------------------------------------------------
        # Plot U
        # ---------------------------------------------------------------------
        plt.figure()
        plt.plot(pynn_u.times, pynn_u)
        plt.plot(nml_u.times * 100, nml_u)
        plt.legend(('PyNN u', '9ML u'))
        plt.show()
        self.assertEqual(pynn_v, nml_v,
                         "PyNN and 9ML versions of Izhikevich model are "
                         "not identical")
