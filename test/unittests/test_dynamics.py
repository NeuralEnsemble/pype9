if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport
import quantities as pq
import ninemlcatalog
from pype9.testing import compare, input_step


class TestDynamics(TestCase):

    dt = 0.001

    def test_izhikevich(self, in_subprocess=False, plot=False):
        # Force compilation of code generation
        # Perform comparison in subprocess
        comparisons = compare(
            nineml_model=ninemlcatalog.lookup(
                'neurons/basic/Izhikevich2003/Izhikevich2003Properties'),
            state_variable='v', dt=self.dt, simulators=['neuron', 'nest'],
            parameters={'a': 0.02, 'b': 0.2, 'c': -65.0, 'd': 2.0},
            initial_states={'u': -14.0, 'v': -65.0},
            neuron_ref='Izhikevich', nest_ref='izhikevich',
            input_signal=input_step('iExt', 0.02, 50, 100, self.dt),
            nest_translations={'v': ('V_m', 1), 'u': ('U_m', 1)},
            neuron_build_args={'build_mode': 'force'},
            nest_build_args={'build_mode': 'force'},
            duration=100.0, in_subprocess=in_subprocess, plot=plot)
        self.assertLess(
            comparisons[('9ML-neuron', 'Ref-neuron')], 0.0015 * pq.mV,
            "Izhikevich NEURON 9ML simulation did not match reference PyNN")
        self.assertLess(
            comparisons[('9ML-nest', 'Ref-nest')], 0.00015 * pq.mV,
            "Izhikevich NEST 9ML simulation did not match reference built-in")

    def test_hh(self, in_subprocess=False, plot=False):
        # Perform comparison in subprocess
        comparisons = compare(
            nineml_model=ninemlcatalog.lookup(
                'neurons/basic/HodgkinHuxley/HodgkinHuxleyProperties'),
            state_variable='v', dt=self.dt, simulators=['neuron', 'nest'],
            initial_states={'v': -65.0, 'm': 0.0, 'h': 1.0, 'n': 0.0},
            neuron_ref='hh_traub', nest_ref='hh_cond_exp_traub',
            input_signal=input_step('iExt', 0.5, 50, 100, self.dt),
            nest_translations={'v': ('V_m', 1), 'm': ('Act_m', 1),
                               'h': ('Act_h', 1), 'n': ('Inact_n', 1)},
            neuron_build_args={'build_mode': 'force'},
            nest_build_args={'build_mode': 'force'},
            duration=100.0, in_subprocess=in_subprocess, plot=plot)
        # FIXME: Need to work out what is happening with the reference NEURON
        self.assertLess(
            comparisons[('9ML-nest', '9ML-neuron')], 0.15 * pq.mV,
            "HH NEURON 9ML simulation did not match reference PyNN")
        self.assertLess(
            comparisons[('9ML-nest', 'Ref-nest')], 0.3 * pq.mV,
            "HH NEST 9ML simulation did not match reference built-in")

    def test_liaf(self, in_subprocess=False, plot=False):
        # Perform comparison in subprocess
        comparisons = compare(
            nineml_model=ninemlcatalog.lookup(
                'neurons/basic/LeakyIntegrateAndFire/'
                'LeakyIntegrateAndFireProperties'),
            state_variable='v', dt=self.dt, simulators=['neuron', 'nest'],
            parameters={
                "Cm": 250.0, "g_leak": 25.0, "refactory_period": 2.0,
                "e_leak": -70.0, "v_reset": -70.0, "v_threshold": -55},
            initial_states={'v': -65.0, 'end_refractory': 0.0},
            neuron_ref='ResetRefrac', nest_ref='iaf_psc_alpha',
            input_signal=input_step('iExt', 1, 50, 100, self.dt),
            nest_translations={
                # the conversion to g_leak is a bit of a hack because it is
                # actually Cm / g_leak
                'Cm': ('C_m', 1), 'g_leak': ('tau_m', 0.4),
                'refactory_period': ('t_ref', 1), 'e_leak': ('E_L', 1),
                'v_reset': ('V_reset', 1), 'v': ('V_m', 1),
                'v_threshold': ('V_th', 1), 'end_refractory': (None, 1)},
            neuron_translations={
                'Cm': ('cm', 1), 'g_leak': ('pas.g', 0.001),
                'refactory_period': ('trefrac', 1), 'e_leak': ('pas.e', 1),
                'v_reset': ('vreset', 1), 'v_threshold': ('vthresh', 1),
                'end_refractory': (None, 1)},
            neuron_build_args={'build_mode': 'force'},
            nest_build_args={'build_mode': 'force'},
            duration=100.0, in_subprocess=in_subprocess, plot=plot)
        # FIXME: The spike threshold is hit after the in-built neuron and nest
        #        versions
        self.assertLess(
            comparisons[('9ML-neuron', 'Ref-neuron')], 0.55 * pq.mV,
            "LIaF NEURON 9ML simulation did not match reference PyNN")
        self.assertLess(
            comparisons[('9ML-nest', 'Ref-nest')], 0.001 * pq.mV,
            "LIaF NEST 9ML simulation did not match reference built-in")

    def test_aeif(self, in_subprocess=False, plot=False):
        # Perform comparison in subprocess
        comparisons = compare(
            nineml_model=ninemlcatalog.lookup(
                'neurons/basic/AdExpIaF/AdExpIaFProperties'),
            state_variable='v', dt=self.dt, simulators=['neuron', 'nest'],
            neuron_ref='AdExpIF', nest_ref='aeif_cond_alpha',
            input_signal=input_step('iExt', 1, 50, 100, self.dt),
            initial_states={'w': 0.0, 'v': -65.0},
            parameters={'EL': 70.6, 'GL': 0.03, 'a': 0.004, 'b': 0.0805,
                        'Cm': 1, 'delta': 2.0, 'tauw': 144.0, 'trefrac': 1.0,
                        'vreset': -60.0, 'vspike': -40.0, 'vthresh': -50.0},
            nest_translations={
                'w': ('w', 1), 'Cm': ('C_m', 1), 'GL': ('g_L', 1000),
                'trefrac': ('t_ref', 1), 'EL': ('E_L', 1), 'a': ('a', 1000),
                'tauw': ('tau_w', 1), 'vreset': ('V_reset', 1),
                'v': ('V_m', 1), 'vthresh': ('V_th', 1), 'b': ('b', 1000),
                'vspike': ('V_peak', 1), 'delta': ('Delta_T', 1)},
            neuron_translations={
                'Cm': ('cm', 1), 'GL': ('pas.g', 0.001), 'EL': ('pas.e', 1)},
            neuron_build_args={'build_mode': 'force'},
            nest_build_args={'build_mode': 'force'},
            duration=100.0, in_subprocess=in_subprocess, plot=plot)
        self.assertLess(
            comparisons[('9ML-neuron', 'Ref-neuron')], 0.0015 * pq.mV,
            "AdExpIaF NEURON 9ML simulation did not match reference PyNN")
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
    tester.test_liaf(in_subprocess=False, plot=True)
    print "done"
