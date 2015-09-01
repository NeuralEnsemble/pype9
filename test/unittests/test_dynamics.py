if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport
import quantities as pq
from itertools import chain
import ninemlcatalog
from nineml.abstraction.dynamics import Dynamics
from nineml.user import DynamicsProperties
from pype9.testing import compare, input_step, input_freq


class TestDynamics(TestCase):

    dt = 0.001
    duration = 100.0

    liaf_initial_states = {'v': -65.0 * pq.mV, 'end_refractory': 0.0 * pq.ms}
    liaf_nest_translations = {
        # the conversion to g_leak is a bit of a hack because it is
        # actually Cm / g_leak
        'Cm': ('C_m', 1), 'g_leak': ('tau_m', 0.4),
        'refactory_period': ('t_ref', 1), 'e_leak': ('E_L', 1),
        'v_reset': ('V_reset', 1), 'v': ('V_m', 1),
        'v_threshold': ('V_th', 1), 'end_refractory': (None, 1)}
    liaf_neuron_translations = {
        'Cm': ('cm', 1), 'g_leak': ('pas.g', 1),
        'refactory_period': ('trefrac', 1), 'e_leak': ('pas.e', 1),
        'v_reset': ('vreset', 1), 'v_threshold': ('vthresh', 1),
        'end_refractory': (None, 1)}

    def test_aeif(self, in_subprocess=False, plot=False):
        # Perform comparison in subprocess
        comparisons = compare(
            nineml_model=ninemlcatalog.lookup(
                'neurons/basic/AdExpIaF/AdExpIaF'),
            state_variable='v', dt=self.dt, simulators=['neuron', 'nest'],
            neuron_ref='AdExpIF', nest_ref='aeif_cond_alpha',
            input_signal=input_step('iExt', 1, 50, 100, self.dt),
            initial_states={'w': 0.0 * pq.nA, 'v': -65.0 * pq.mV},
            properties=ninemlcatalog.lookup(
                'neurons/basic/AdExpIaF/AdExpIaFProperties'),
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
            duration=self.duration, in_subprocess=in_subprocess, plot=plot)
        self.assertLess(
            comparisons[('9ML-neuron', 'Ref-neuron')], 0.0015 * pq.mV,
            "AdExpIaF NEURON 9ML simulation did not match reference PyNN")
        self.assertLess(
            comparisons[('9ML-nest', 'Ref-nest')], 0.00015 * pq.mV,
            "AdExpIaF NEST 9ML simulation did not match reference built-in")

    def test_izhikevich(self, in_subprocess=False, plot=False,
                        print_comparisons=False):
        # Force compilation of code generation
        # Perform comparison in subprocess
        comparisons = compare(
            nineml_model=ninemlcatalog.lookup(
                'neurons/basic/Izhikevich2003/Izhikevich2003'),
            state_variable='v', dt=self.dt, simulators=['neuron', 'nest'],
            properties=ninemlcatalog.lookup(
                'neurons/basic/Izhikevich2003/Izhikevich2003Properties'),
            initial_states={'u': -14.0 * pq.mV / pq.ms, 'v': -65.0 * pq.mV},
            neuron_ref='Izhikevich', nest_ref='izhikevich',
            input_signal=input_step('iExt', 0.02, 50, 100, self.dt),
            nest_translations={'v': ('V_m', 1), 'u': ('U_m', 1),
                               'weight': (None, 1), 'Cm': (None, 1),
                               'vthresh': ('V_th', 1)},
            neuron_translations={'Cm': (None, 1), 'weight': (None, 1)},
            neuron_build_args={'build_mode': 'force'},
            nest_build_args={'build_mode': 'force'},
            duration=self.duration, in_subprocess=in_subprocess, plot=plot)
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
                'neurons/basic/HodgkinHuxley/HodgkinHuxley'),
            state_variable='v', dt=self.dt, simulators=['neuron', 'nest'],
            initial_states={'v': -65.0 * pq.mV, 'm': 0.0, 'h': 1.0, 'n': 0.0},
            properties=ninemlcatalog.lookup(
                'neurons/basic/HodgkinHuxley/HodgkinHuxleyProperties'),
            neuron_ref='hh_traub', nest_ref='hh_cond_exp_traub',
            input_signal=input_step('iExt', 0.5, 50, 100, self.dt),
            nest_translations={
                'v': ('V_m', 1), 'm': ('Act_m', 1),
                'h': ('Act_h', 1), 'n': ('Inact_n', 1),
                'eNa': ('E_Na', 1), 'eK': ('E_K', 1), 'C': ('C_m', 1),
                'gLeak': ('g_L', 1), 'eLeak': ('E_L', 1),
                'gbarNa': ('g_Na', 1), 'gbarK': ('g_K', 1),
                'v_rest': ('V_T', 1), 'v_threshold': (None, 1),
                'm_alpha_A': (None, 1), 'm_alpha_V0': (None, 1),
                'm_alpha_K': (None, 1), 'm_beta_A': (None, 1),
                'm_beta_V0': (None, 1), 'm_beta_K': (None, 1),
                'h_alpha_A': (None, 1), 'h_alpha_V0': (None, 1),
                'h_alpha_K': (None, 1), 'h_beta_A': (None, 1),
                'h_beta_V0': (None, 1), 'h_beta_K': (None, 1),
                'n_alpha_A': (None, 1), 'n_alpha_V0': (None, 1),
                'n_alpha_K': (None, 1), 'n_beta_A': (None, 1),
                'n_beta_V0': (None, 1), 'n_beta_K': (None, 1)},
            neuron_translations={
                'eNa': ('ena', 1), 'eK': ('ek', 1), 'C': ('cm', 1),
                'gLeak': ('gl', 1), 'eLeak': ('el', 1),
                'gbarNa': ('gnabar', 1), 'gbarK': ('gkbar', 1),
                'v_rest': ('vT', 1), 'v_threshold': (None, 1),
                'm_alpha_A': (None, 1), 'm_alpha_V0': (None, 1),
                'm_alpha_K': (None, 1), 'm_beta_A': (None, 1),
                'm_beta_V0': (None, 1), 'm_beta_K': (None, 1),
                'h_alpha_A': (None, 1), 'h_alpha_V0': (None, 1),
                'h_alpha_K': (None, 1), 'h_beta_A': (None, 1),
                'h_beta_V0': (None, 1), 'h_beta_K': (None, 1),
                'n_alpha_A': (None, 1), 'n_alpha_V0': (None, 1),
                'n_alpha_K': (None, 1), 'n_beta_A': (None, 1),
                'n_beta_V0': (None, 1), 'n_beta_K': (None, 1)},
            neuron_build_args={'build_mode': 'force'},
            nest_build_args={'build_mode': 'force'},
            duration=self.duration, in_subprocess=in_subprocess, plot=plot)
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
                'neurons/basic/LeakyIntegrateAndFire/LeakyIntegrateAndFire'),
            state_variable='v', dt=self.dt, simulators=['neuron', 'nest'],
            properties=ninemlcatalog.lookup(
                'neurons/basic/LeakyIntegrateAndFire/'
                'LeakyIntegrateAndFireProperties'),
            initial_states=self.liaf_initial_states,
            neuron_ref='ResetRefrac', nest_ref='iaf_psc_alpha',
            input_signal=input_step('iExt', 1, 50, 100, self.dt),
            nest_translations=self.liaf_nest_translations,
            neuron_translations=self.liaf_neuron_translations,
            neuron_build_args={'build_mode': 'force'},
            nest_build_args={'build_mode': 'force'},
            duration=self.duration, in_subprocess=in_subprocess, plot=plot)
        self.assertLess(
            comparisons[('9ML-neuron', 'Ref-neuron')], 0.55 * pq.mV,
            "LIaF NEURON 9ML simulation did not match reference PyNN")
        self.assertLess(
            comparisons[('9ML-nest', 'Ref-nest')], 0.001 * pq.mV,
            "LIaF NEST 9ML simulation did not match reference built-in")

    def test_alpha_syn(self, in_subprocess=False, plot=False):
        # Perform comparison in subprocess
        iaf = ninemlcatalog.lookup(
            'neurons/basic/LeakyIntegrateAndFire/LeakyIntegrateAndFire')
        alpha_psr = ninemlcatalog.lookup(
            'postsynapticresponses/Alpha/Alpha')
        iaf_alpha = Dynamics(
            name='IafAlpha', subnodes={'neuron': iaf, 'psr': alpha_psr})
        iaf_alpha_flat = iaf_alpha.flatten()
        initial_states = {'a': 0.0 * pq.nA, 'b': 0.0 * pq.nA}
        liaf_properties = ninemlcatalog.lookup(
            'neurons/basic/LeakyIntegrateAndFire/'
            'LeakyIntegrateAndFireProperties')
        alpha_properties = ninemlcatalog.lookup(
            'postsynapticresponses/Alpha/AlphaProperties')
        nest_tranlsations = {'tau': ('tau_synE', 1)}
        neuron_tranlsations = {}
        initial_states.update(self.liaf_initial_states)
        properties = DynamicsProperties(
            name='IafAlphaProperties', definition=iaf_alpha_flat,
            properties=dict(
                (p.name, (p.value, p.units))
                for p in chain(liaf_properties.properties,
                               alpha_properties.properties)))
        properties.update(self.liaf_properties)
        nest_tranlsations.update(self.liaf_nest_translations)
        neuron_tranlsations.update(self.liaf_neuron_translations)
        comparisons = compare(
            nineml_model=iaf_alpha_flat,
            state_variable='v', dt=self.dt, simulators=['neuron', 'nest'],
            properties=properties,
            initial_states=initial_states,
            neuron_ref='ResetRefrac', nest_ref='iaf_psc_alpha',
            input_train=input_freq('spike', 100, self.duration),
            nest_translations=nest_tranlsations,
            neuron_translations=neuron_tranlsations,
            neuron_build_args={'build_mode': 'force'},
            nest_build_args={'build_mode': 'force'},
            duration=self.duration, in_subprocess=in_subprocess, plot=plot)
        self.assertLess(
            comparisons[('9ML-neuron', 'Ref-neuron')], 0.55 * pq.mV,
            "LIaF NEURON 9ML simulation did not match reference PyNN")
        self.assertLess(
            comparisons[('9ML-nest', 'Ref-nest')], 0.001 * pq.mV,
            "LIaF NEST 9ML simulation did not match reference built-in")

if __name__ == '__main__':
    tester = TestDynamics()
    tester.test_alpha_syn(in_subprocess=False, plot=True)
    print "done"
