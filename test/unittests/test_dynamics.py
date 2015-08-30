if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport
import quantities as pq
import ninemlcatalog
from pype9.testing import Comparer


class TestDynamics(TestCase):

    dt = 0.001

    def test_izhikevich(self):
        # Force compilation of code generation
        # Perform comparison in subprocess
        comparisons = Comparer.compare_in_subprocess(
            nineml_model=ninemlcatalog.lookup(
                'neurons/basic/Izhikevich2003/Izhikevich2003Properties'),
            state_variable='v', dt=self.dt, simulators=['neuron', 'nest'],
            parameters={'a': 0.02, 'b': 0.2, 'c': -65.0, 'd': 2.0},
            initial_states={'u': -14.0, 'v': -65.0},
            neuron_ref='Izhikevich', nest_ref='izhikevich',
            input_signal=Comparer.input_step('iExt', 0.02, 50, 100, self.dt),
            nest_translations={'v': ('V_m', 1), 'u': ('U_m', 1)},
            neuron_build_args={'build_mode': 'force'},
            nest_build_args={'build_mode': 'force'},
            duration=100.0)
        self.assertLess(
            comparisons[('9ML-neuron', 'Ref-neuron')], 0.0015 * pq.mV,
            "Izhikevich NEURON 9ML simulation did not match reference PyNN")
        self.assertLess(
            comparisons[('9ML-nest', 'Ref-nest')], 0.00015 * pq.mV,
            "Izhikevich NEST 9ML simulation did not match reference built-in")

    def test_hh(self):
        # Perform comparison in subprocess
        comparisons = Comparer.compare_in_subprocess(
            nineml_model=ninemlcatalog.lookup(
                'neurons/basic/HodgkinHuxley/HodgkinHuxleyProperties'),
            state_variable='v', dt=self.dt, simulators=['neuron', 'nest'],
            initial_states={'v': -65.0, 'm': 0.0, 'h': 1.0, 'n': 0.0},
            neuron_ref='hh_traub', nest_ref='hh_cond_exp_traub',
            input_signal=Comparer.input_step('iExt', 0.5, 50, 100, self.dt),
            nest_translations={'v': ('V_m', 1), 'm': ('Act_m', 1),
                               'h': ('Act_h', 1), 'n': ('Inact_n', 1)},
            neuron_build_args={'build_mode': 'force'},
            nest_build_args={'build_mode': 'force'})
        self.assertLess(
            comparisons[('9ML-neuron', 'Ref-neuron')], 0.0015 * pq.mV,
            "HH NEURON 9ML simulation (did not match reference PyNN")
        self.assertLess(
            comparisons[('9ML-nest', 'Ref-nest')], 0.00015 * pq.mV,
            "HH NEST 9ML simulation did not match reference built-in")

    def test_liaf(self):
        # Perform comparison in subprocess
        comparisons = Comparer.compare_in_subprocess(
            nineml_model=ninemlcatalog.lookup(
                'neurons/basic/LeakyIntegrateAndFire/'
                'LeakyIntegrateAndFireProperties'),
            state_variable='v', dt=self.dt, simulators=['neuron', 'nest'],
            parameters={"C_m": 250.0, "tau_m": 20.0, "tau_syn_ex": 0.5,
                        "tau_syn_in": 0.5, "t_ref": 2.0, "E_L": 0.0,
                        "V_reset": 0.0, "V_m": 0.0, "V_th": 20.0},  # {'g': 0.00025, 'e': -70}, { 'vthresh': -55, 'vreset': -70, 'trefrac': 2}
            initial_states={'v': -65 * pq.mV, 'end_refractory': 0.0},
            neuron_ref='ResetRefrac', nest_ref='iaf_psc_alpha',
            input_signal=Comparer.input_step('iExt', 1, 50, 100, self.dt),
            nest_translations={'v': ('V_m', 1), 'end_refractory': (None, 1)},
            neuron_translations={},
            neuron_build_args={'build_mode': 'force'},
            nest_build_args={'build_mode': 'force'})
        self.assertLess(
            comparisons[('9ML-neuron', 'Ref-neuron')], 0.0015 * pq.mV,
            "LIaF NEURON 9ML simulation (did not match reference PyNN")
        self.assertLess(
            comparisons[('9ML-nest', 'Ref-nest')], 0.00015 * pq.mV,
            "LIaF NEST 9ML simulation did not match reference built-in")

    def test_aeif(self):
        # Perform comparison in subprocess
        comparisons = Comparer.compare_in_subprocess(
            nineml_model=ninemlcatalog.lookup(
                'neurons/basic/Izhikevich2003/Izhikevich2003Properties'),
            state_variable='v', dt=self.dt, simulators=['neuron', 'nest'],
            neuron_ref='AdExpIF', nest_ref='aeif_cond_alpha',
            input_signal=Comparer.input_step('iExt', 1, 50, 100, self.dt),
            initial_states={'w': 0.0, 'v': -65.0},
            nest_translations={'w': ('w', 1), 'v': ('V_m', 1)},
            neuron_translations={},
            neuron_build_args={'build_mode': 'force'},
            nest_build_args={'build_mode': 'force'})
        self.assertLess(
            comparisons[('9ML-neuron', 'Ref-neuron')], 0.0015 * pq.mV,
            "AdExpIaF NEURON 9ML simulation (did not match reference PyNN")
        self.assertLess(
            comparisons[('9ML-nest', 'Ref-nest')], 0.00015 * pq.mV,
            "AdExpIaF NEST 9ML simulation did not match reference built-in")

#     models = [('Izhikevich2003', 'Izhikevich', 'izhikevich'),
#               ('AdExpIaF', 'AdExpIF', 'aeif_cond_alpha'),
#               ('HodgkinHuxley', 'hh_traub', 'hh_cond_exp_traub'),
#               ('LeakyIntegrateAndFire', 'ResetRefrac', 'iaf_psc_alpha')]
# 
#     initial_states = {'Izhikevich2003': {'u': -14 * pq.mV / pq.ms,
#                                          'v': -65.0 * pq.mV},
#                       'AdExpIaF': {'w': 0.0 * pq.nA,
#                                    'v': -65 * pq.mV},
#                       'HodgkinHuxley': {'v': -65 * pq.mV,
#                                         'm': 0, 'h': 1, 'n': 0},
#                       'LeakyIntegrateAndFire': {'v': -65 * pq.mV,
#                                                 'end_refractory': 0.0}}
# 
#     neuron_pas = {'Izhikevich2003': None,
#                   'AdExpIaF': None,
#                   'HodgkinHuxley': None,
#                   'LeakyIntegrateAndFire': {'g': 0.00025, 'e': -70}}
#     neuron_params = {'Izhikevich2003': None,
#                      'AdExpIaF': None,
#                      'HodgkinHuxley': None,
#                      'LeakyIntegrateAndFire': {
#                          'vthresh': -55,
#                          'vreset': -70,
#                          'trefrac': 2}}
# 
#     nest_states = {'Izhikevich2003': {'u': 'U_m', 'v': 'V_m'},
#                    'AdExpIaF': {'w': 'w', 'v': 'V_m'},
#                    'HodgkinHuxley': {'v': 'V_m', 'm': 'Act_m', 'h': 'Act_h',
#                                      'n': 'Inact_n'},
#                    'LeakyIntegrateAndFire': {'v': 'V_m',
#                                              'end_refractory': None}}
#     nest_params = {'Izhikevich2003': {'a': 0.02, 'c': -65.0, 'b': 0.2,
#                                       'd': 2.0},
#                    'AdExpIaF': {},
#                    'HodgkinHuxley': {},
#                    'LeakyIntegrateAndFire': {"C_m": 250.0,
#                                              "tau_m": 20.0,
#                                              "tau_syn_ex": 0.5,
#                                              "tau_syn_in": 0.5,
#                                              "t_ref": 2.0,
#                                              "E_L": 0.0,
#                                              "V_reset": 0.0,
#                                              "V_m": 0.0,
#                                              "V_th": 20.0}}
#     paradigms = {'Izhikevich2003': {'duration': 100 * pq.ms,
#                                     'stim_amp': 0.02 * pq.nA,
#                                     'stim_start': 20 * pq.ms,
#                                     'dt': 0.02 * pq.ms},
#                  'AdExpIaF': {'duration': 50 * pq.ms,
#                               'stim_amp': 1 * pq.nA,
#                               'stim_start': 25 * pq.ms,
#                               'dt': 0.002 * pq.ms},
#                  'HodgkinHuxley': {'duration': 100 * pq.ms,
#                                    'stim_amp': 0.5 * pq.nA,
#                                    'stim_start': 50 * pq.ms,
#                                    'dt': 0.002 * pq.ms},
#                  'LeakyIntegrateAndFire': {'duration': 50 * pq.ms,
#                                            'stim_amp': 1 * pq.nA,
#                                            'stim_start': 25 * pq.ms,
#                                            'dt': 0.002 * pq.ms}}

if __name__ == '__main__':
    tester = TestDynamics()
    tester.test_izhikevich()
