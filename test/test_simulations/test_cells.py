#!/usr/bin/env python
from __future__ import print_function
from __future__ import division
from builtins import zip
from past.utils import old_div
import sys
import quantities as pq
from itertools import chain, repeat
import logging
import ninemlcatalog
from nineml import units as un
from nineml.user import Property
from nineml.user.multi.dynamics import MultiDynamics
from nineml.user import DynamicsProperties
from pype9.simulate.common.cells import (
    MultiDynamicsWithSynapses, DynamicsWithSynapsesProperties,
    ConnectionParameterSet, ConnectionPropertySet)
from pype9.simulate.neuron import (
    CellMetaClass as NeuronCellMetaClass,
    Simulation as NeuronSimulation)
argv = sys.argv[1:]  # Save argv before it is clobbered by the NEST init.
from pype9.simulate.nest import (  # @IgnorePep8
    CellMetaClass as NESTCellMetaClass,
    Simulation as NESTSimulation)
from pype9.utils.testing import Comparer, input_step, input_freq  # @IgnorePep8
from pype9.simulate.nest.units import UnitHandler as UnitHandlerNEST  # @IgnorePep8
if __name__ == '__main__':
    from pype9.utils.testing import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport


logger = logging.getLogger('pype9')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


cell_metaclasses = {'neuron': NeuronCellMetaClass,
                    'nest': NESTCellMetaClass}

NEST_RNG_SEED = 1234567890
NEURON_RNG_SEED = 987654321

SIMULATORS_TO_TEST = ['neuron', 'nest']
PLOT_DEFAULT = True  # False


class TestDynamics(TestCase):

    liaf_initial_states = {'v': -65.0 * pq.mV, 'end_refractory': 0.0 * pq.ms}
    liaf_nest_translations = {
        # the conversion to g_leak is a bit of a hack because it is
        # actually Cm / g_leak
        'Cm': ('C_m', 1), 'tau': ('tau_m', 1),
        'refractory_period': ('t_ref', 1), 'e_leak': ('E_L', 1),
        'v_reset': ('V_reset', 1), 'v': ('V_m', 1),
        'v_threshold': ('V_th', 1), 'end_refractory': (None, 1)}
    liaf_neuron_translations = {
        'tau': ('pas.g', 0.25),  # Hack to translate tau_m to g_leak
        'Cm': ('cm', 1),
        'refractory_period': ('trefrac', 1), 'e_leak': ('pas.e', 1),
        'v_reset': ('vreset', 1), 'v_threshold': ('vthresh', 1),
        'end_refractory': (None, 1), 'v': ('v', 1)}

    def test_izhi(self, plot=PLOT_DEFAULT, print_comparisons=False,
                  simulators=SIMULATORS_TO_TEST,
                  dt=0.001, duration=100.0,
                  build_mode='force', **kwargs):  # @UnusedVariable
        # Force compilation of code generation
        # Perform comparison in subprocess
        comparer = Comparer(
            nineml_model=ninemlcatalog.load(
                'neuron/Izhikevich', 'Izhikevich'),
            state_variable='V', dt=dt, simulators=simulators,
            properties=ninemlcatalog.load(
                'neuron/Izhikevich', 'SampleIzhikevich'),
            initial_states={'U': -14.0 * pq.mV / pq.ms, 'V': -65.0 * pq.mV},
            neuron_ref='Izhikevich', nest_ref='izhikevich',
            # auxiliary_states=['U'],
            input_signal=input_step('Isyn', 0.02, 50, 100, dt, 30),
            nest_translations={'V': ('V_m', 1), 'U': ('U_m', 1),
                               'weight': (None, 1), 'C_m': (None, 1),
                               'theta': ('V_th', 1),
                               'alpha': (None, 1), 'beta': (None, 1),
                               'zeta': (None, 1)},
            neuron_translations={'C_m': (None, 1), 'weight': (None, 1),
                                 'V': ('v', 1), 'U': ('u', 1),
                                 'alpha': (None, 1), 'beta': (None, 1),
                                 'zeta': (None, 1), 'theta': ('vthresh', 1)},
            neuron_build_args={'build_mode': build_mode,
                               'build_version': 'TestDyn'},
            nest_build_args={'build_mode': build_mode,
                             'build_version': 'TestDyn'})
        comparer.simulate(duration * un.ms, nest_rng_seed=NEST_RNG_SEED,
                          neuron_rng_seed=NEURON_RNG_SEED)
        comparisons = comparer.compare()
        if print_comparisons:
            for (name1, name2), diff in comparisons.items():
                print('{} v {}: {}'.format(name1, name2, diff))
        if plot:
            comparer.plot()
        if 'nest' in simulators and 'neuron' in simulators:
            self.assertLess(
                comparisons[('9ML-nest', '9ML-neuron')], 0.4 * pq.mV,
                "Izhikevich NEURON 9ML simulation did not match NEST 9ML "
                "within {} ({})".format(
                    0.4 * pq.mV, comparisons[('9ML-nest', '9ML-neuron')]))
        if 'neuron' in simulators:
            self.assertLess(
                comparisons[('9ML-neuron', 'Ref-neuron')], 0.01 * pq.mV,
                "Izhikevich NEURON 9ML simulation did not match reference "
                "PyNN within {} ({})".format(
                    0.01 * pq.mV, comparisons[('9ML-neuron', 'Ref-neuron')]))
        if 'nest' in simulators:
            self.assertLess(
                comparisons[('9ML-nest', 'Ref-nest')], 0.02 * pq.mV,
                "Izhikevich NEST 9ML simulation did not match reference "
                "built-in within {} ({})".format(
                    0.02 * pq.mV, comparisons[('9ML-nest', 'Ref-nest')]))

    def test_hh(self, plot=PLOT_DEFAULT, print_comparisons=False,
                simulators=SIMULATORS_TO_TEST, dt=0.001, duration=100.0,
                build_mode='force', **kwargs):  # @UnusedVariable
        # Perform comparison in subprocess
        comparer = Comparer(
            nineml_model=ninemlcatalog.load(
                'neuron/HodgkinHuxley', 'PyNNHodgkinHuxley'),
            state_variable='v', dt=dt, simulators=simulators,
            initial_states={'v': -65.0 * pq.mV, 'm': 0.0, 'h': 1.0, 'n': 0.0},
            properties=ninemlcatalog.load(
                'neuron/HodgkinHuxley', 'PyNNHodgkinHuxleyProperties'),
            neuron_ref='hh_traub', nest_ref='hh_cond_exp_traub',
            input_signal=input_step('iExt', 0.5, 50, 100, dt, 10),
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
            # auxiliary_states=['m', 'h', 'n'],
            neuron_build_args={'build_mode': build_mode},
            nest_build_args={'build_mode': build_mode})
        comparer.simulate(duration * un.ms, nest_rng_seed=NEST_RNG_SEED,
                          neuron_rng_seed=NEURON_RNG_SEED)
        comparisons = comparer.compare()
        if print_comparisons:
            for (name1, name2), diff in comparisons.items():
                print('{} v {}: {}'.format(name1, name2, diff))
        if plot:
            comparer.plot()
        # FIXME: Need to work out what is happening with the reference NEURON
        if 'nest' in simulators and 'neuron' in simulators:
            self.assertLess(
                comparisons[('9ML-nest', '9ML-neuron')], 0.5 * pq.mV,
                "HH 9ML NEURON and NEST simulation did not match each other "
                "within {} ({})".format(
                    0.5 * pq.mV, comparisons[('9ML-nest', '9ML-neuron')]))
        if 'neuron' in simulators:
            self.assertLess(
                comparisons[('9ML-neuron', 'Ref-neuron')], 0.55 * pq.mV,
                "HH 9ML NEURON simulation did not match reference built-in "
                "within {} ({})".format(
                    0.55 * pq.mV, comparisons[('9ML-neuron', 'Ref-neuron')]))
        if 'nest' in simulators:
            self.assertLess(
                comparisons[('9ML-nest', 'Ref-nest')], 0.0015 * pq.mV,
                "HH 9ML NEST simulation did not match reference built-in "
                "within {} ({})".format(
                    0.0015 * pq.mV, comparisons[('9ML-nest', 'Ref-nest')]))

    def test_liaf(self, plot=PLOT_DEFAULT, print_comparisons=False,
                  simulators=SIMULATORS_TO_TEST, dt=0.001, duration=100.0,
                  build_mode='force', **kwargs):  # @UnusedVariable
        # Perform comparison in subprocess
        comparer = Comparer(
            nineml_model=ninemlcatalog.load(
                'neuron/LeakyIntegrateAndFire',
                'PyNNLeakyIntegrateAndFire'),
            state_variable='v', dt=dt, simulators=simulators,
            properties=ninemlcatalog.load(
                'neuron/LeakyIntegrateAndFire',
                'PyNNLeakyIntegrateAndFireProperties'),
            initial_states=self.liaf_initial_states,
            initial_regime='subthreshold',
            neuron_ref='ResetRefrac', nest_ref='iaf_psc_alpha',
            input_signal=input_step('i_synaptic', 1, 50, 100, dt, 20),
            nest_translations=self.liaf_nest_translations,
            neuron_translations=self.liaf_neuron_translations,
            neuron_build_args={'build_mode': build_mode},
            nest_build_args={'build_mode': build_mode},
            # auxiliary_states=['end_refractory'],
            extra_mechanisms=['pas'])
        comparer.simulate(duration * un.ms, nest_rng_seed=NEST_RNG_SEED,
                          neuron_rng_seed=NEURON_RNG_SEED)
        comparisons = comparer.compare()
        if print_comparisons:
            for (name1, name2), diff in comparisons.items():
                print('{} v {}: {}'.format(name1, name2, diff))
        if plot:
            comparer.plot()
        if 'neuron' in simulators:
            self.assertLess(
                comparisons[('9ML-neuron', 'Ref-neuron')], 0.55 * pq.mV,
                "LIaF NEURON 9ML simulation did not match reference PyNN "
                "within {} ({})".format(
                    0.55 * pq.mV, comparisons[('9ML-neuron', 'Ref-neuron')]))
        if 'nest' in simulators:
            self.assertLess(
                comparisons[('9ML-nest', 'Ref-nest')], 0.01 * pq.mV,
                "LIaF NEST 9ML simulation did not match reference built-in "
                "within {} ({})".format(
                    0.01 * pq.mV, comparisons[('9ML-nest', 'Ref-nest')]))
        if 'nest' in simulators and 'neuron' in simulators:
            self.assertLess(
                comparisons[('9ML-nest', '9ML-neuron')], 0.55 * pq.mV,
                "LIaF NEURON 9ML simulation did not match NEST 9ML simulation "
                "within {} ({})".format(
                    0.55 * pq.mV, comparisons[('9ML-nest', '9ML-neuron')]))

    def test_alpha_syn(self, plot=PLOT_DEFAULT, print_comparisons=False,
                       simulators=SIMULATORS_TO_TEST, dt=0.001,
                       duration=100.0, min_delay=5.0, device_delay=5.0,
                       build_mode='force', **kwargs):  # @UnusedVariable
        # Perform comparison in subprocess
        iaf = ninemlcatalog.load(
            'neuron/LeakyIntegrateAndFire', 'PyNNLeakyIntegrateAndFire')
        alpha_psr = ninemlcatalog.load(
            'postsynapticresponse/Alpha', 'PyNNAlpha')
        static = ninemlcatalog.load(
            'plasticity/Static', 'Static')
        iaf_alpha = MultiDynamics(
            name='IafAlpha_sans_synapses',
            sub_components={
                'cell': iaf,
                'syn': MultiDynamics(
                    name="IafAlaphSyn",
                    sub_components={'psr': alpha_psr, 'pls': static},
                    port_connections=[
                        ('pls', 'fixed_weight', 'psr', 'q')],
                    port_exposures=[('psr', 'i_synaptic'),
                                    ('psr', 'spike')])},
            port_connections=[
                ('syn', 'i_synaptic__psr', 'cell', 'i_synaptic')],
            port_exposures=[('syn', 'spike__psr', 'spike')])
        iaf_alpha_with_syn = MultiDynamicsWithSynapses(
            'IafAlpha',
            iaf_alpha,
            connection_parameter_sets=[
                ConnectionParameterSet(
                    'spike', [iaf_alpha.parameter('weight__pls__syn')])])
        initial_states = {'a__psr__syn': 0.0 * pq.nA,
                          'b__psr__syn': 0.0 * pq.nA}
        initial_regime = 'subthreshold___sole_____sole'
        liaf_properties = ninemlcatalog.load(
            'neuron/LeakyIntegrateAndFire/',
            'PyNNLeakyIntegrateAndFireProperties')
        alpha_properties = ninemlcatalog.load(
            'postsynapticresponse/Alpha', 'SamplePyNNAlphaProperties')
        nest_tranlsations = {'tau__psr__syn': ('tau_syn_ex', 1),
                             'a__psr__syn': (None, 1),
                             'b__psr__syn': (None, 1),
                             'spike': ('spike', 1000.0)}
        neuron_tranlsations = {'tau__psr__syn': ('psr.tau', 1),
                               'q__psr__syn': ('psr.q', 1),
                               'spike': ('spike', 1),
                               'a__psr__syn': (None, 1),
                               'b__psr__syn': (None, 1)}
        initial_states.update(
            (k + '__cell', v) for k, v in self.liaf_initial_states.items())
        properties = DynamicsProperties(
            name='IafAlphaProperties', definition=iaf_alpha,
            properties=dict(
                (p.name + '__' + suffix, p.quantity)
                for p, suffix in chain(
                    list(zip(liaf_properties.properties, repeat('cell'))),
                    list(zip(alpha_properties.properties, repeat('psr__syn'))),
                    [(Property('weight', 10 * un.nA), 'pls__syn')])))
        properties_with_syn = DynamicsWithSynapsesProperties(
            'IafAlpha_props_with_syn',
            properties,  # @IgnorePep8
            connection_property_sets=[
                ConnectionPropertySet(
                    'spike',
                    [properties.property('weight__pls__syn')])])
        nest_tranlsations.update(
            (k + '__cell', v)
            for k, v in self.liaf_nest_translations.items())
        neuron_tranlsations.update(
            (k + '__cell', v)
            for k, v in self.liaf_neuron_translations.items())
        comparer = Comparer(
            nineml_model=iaf_alpha_with_syn,
            state_variable='v__cell', dt=dt,
            simulators=simulators,
            properties=properties_with_syn,
            initial_states=initial_states,
            initial_regime=initial_regime,
            neuron_ref='ResetRefrac',
            nest_ref='iaf_psc_alpha',
            input_train=input_freq('spike', 450 * pq.Hz, duration * pq.ms,
                                   weight=[Property('weight__pls__syn',
                                                    10 * un.nA)],  # 20.680155243 * un.pA
                                   offset=duration / 2.0),
            nest_translations=nest_tranlsations,
            neuron_translations=neuron_tranlsations,
            extra_mechanisms=['pas'],
            extra_point_process='AlphaISyn',
            neuron_build_args={
                'build_mode': build_mode},
            nest_build_args={
                'build_mode': build_mode},
            min_delay=min_delay,
            # auxiliary_states=['end_refractory__cell'],
            device_delay=device_delay)
        comparer.simulate(duration * un.ms, nest_rng_seed=NEST_RNG_SEED,
                          neuron_rng_seed=NEURON_RNG_SEED)
        comparisons = comparer.compare()
        if print_comparisons:
            for (name1, name2), diff in comparisons.items():
                print('{} v {}: {}'.format(name1, name2, diff))
        if plot:
            comparer.plot()
        if 'nest' in simulators and 'neuron' in simulators:
            self.assertLess(
                comparisons[('9ML-nest', '9ML-neuron')], 0.015 * pq.mV,
                "LIaF with Alpha syn NEST 9ML simulation did not match NEURON "
                "9ML simulation within {} ({})".format(
                    0.015 * pq.mV, comparisons[('9ML-nest', '9ML-neuron')]))
        if 'nest' in simulators:
            self.assertLess(
                comparisons[('9ML-nest', 'Ref-nest')], 0.04 * pq.mV,
                "LIaF with Alpha syn NEST 9ML simulation did not match "
                "reference built-in within {} ({})".format(
                    0.04 * pq.mV, comparisons[('9ML-nest', 'Ref-nest')]))
        if 'neuron' in simulators:
            self.assertLess(
                comparisons[('9ML-neuron', 'Ref-neuron')], 0.03 * pq.mV,
                "LIaF with Alpha syn NEURON 9ML simulation did not match "
                "reference PyNN within {} ({})".format(
                    0.03 * pq.mV, comparisons[('9ML-neuron', 'Ref-neuron')]))

    def test_izhiFS(self, plot=PLOT_DEFAULT, print_comparisons=False,
                    simulators=SIMULATORS_TO_TEST, dt=0.001, duration=100.0,
                    build_mode='force', **kwargs):  # @UnusedVariable
        # Force compilation of code generation
        # Perform comparison in subprocess
        comparer = Comparer(
            nineml_model=ninemlcatalog.load(
                'neuron/Izhikevich', 'IzhikevichFastSpiking'),
            state_variable='V', dt=dt, simulators=simulators,
            properties=ninemlcatalog.load(
                'neuron/Izhikevich', 'SampleIzhikevichFastSpiking'),
            initial_states={'U': -1.625 * pq.pA, 'V': -65.0 * pq.mV},
            input_signal=input_step('iSyn', 100 * pq.pA, 25.0, 100, dt, 15),
            initial_regime='subVb',
            neuron_build_args={'build_mode': build_mode,
                               'external_currents': ['iSyn']},
            # auxiliary_states=['U'],
            nest_build_args={'build_mode': build_mode})
        comparer.simulate(duration * un.ms, nest_rng_seed=NEST_RNG_SEED,
                          neuron_rng_seed=NEURON_RNG_SEED)
        comparisons = comparer.compare()
        if print_comparisons:
            for (name1, name2), diff in comparisons.items():
                print('{} v {}: {}'.format(name1, name2, diff))
        if plot:
            comparer.plot()
        if 'nest' in simulators and 'neuron' in simulators:
            self.assertLess(
                comparisons[('9ML-nest', '9ML-neuron')], 0.4 * pq.mV,
                "Izhikevich 2007 NEURON 9ML simulation did not match NEST 9ML")

    def test_poisson(self, duration=100 * un.s, rate=100 * un.Hz,
                     t_next=0.0 * un.ms, print_comparisons=False, dt=0.1,
                     simulators=SIMULATORS_TO_TEST, build_mode='force',
                     **kwargs):  # @UnusedVariable @IgnorePep8
        nineml_model = ninemlcatalog.load('input/Poisson', 'Poisson')
        build_args = {'neuron': {'build_mode': build_mode,
                                 'external_currents': ['iSyn']},
                      'nest': {'build_mode': build_mode}}  #, 'debug': {'states': ['transition']}}} @IgnorePep8
        for sim_name in simulators:
            meta_class = cell_metaclasses[sim_name]
            # Build celltype
            celltype = meta_class(nineml_model, **build_args[sim_name])
            # Initialise simulator
            if sim_name == 'neuron':
                # Run NEURON simulation
                Simulation = NeuronSimulation(dt=dt * un.ms,
                                              seed=NEURON_RNG_SEED)
            elif sim_name == 'nest':
                Simulation = NESTSimulation(dt=dt * un.ms, seed=NEST_RNG_SEED)
            else:
                assert False
            with Simulation as sim:
                # Create and initialize cell
                cell = celltype(rate=rate, t_next=t_next)
                cell.record('spike_output')
                sim.run(duration)
            # Get recording
            spikes = cell.recording('spike_output')
            # Calculate the rate of the modelled process
            recorded_rate = pq.Quantity(
                old_div(len(spikes), (spikes.t_stop - spikes.t_start)), 'Hz')
            ref_rate = pq.Quantity(UnitHandlerNEST.to_pq_quantity(rate), 'Hz')
            rate_difference = abs(ref_rate - recorded_rate)
            if print_comparisons:
                print("Reference rate: {}".format(ref_rate))
                print("{} recorded rate: {}".format(sim_name, recorded_rate))
                print("{} difference: {}".format(sim_name, rate_difference))
            self.assertLess(
                rate_difference, 5 * pq.Hz,
                ("Recorded rate of {} poisson generator ({}) did not match "
                 "desired ({}) within {}: difference {}".format(
                     sim_name, recorded_rate, ref_rate, 2.5 * pq.Hz,
                     recorded_rate - ref_rate)))



            # Calculate the absolute deviation
#             isi_avg = 1.0 / recorded_rate.rescale(pq.ms)
#             isi_std_dev = (abs((spikes[1:] - spikes[:-1]) - isi_avg) /
#                            (len(spikes) - 1))
#             recorded_cv = isi_std_dev / isi_avg
#             ref_cv = 1.0 / ref_rate ** 2.0
#             if print_comparisons:
#                 print "ref cv: {}, recorded cv {}".format(ref_cv, recorded_cv)
#             self.assertAlmostEqual(
#                 recorded_cv, ref_cv,
#                 "Recorded coefficient of variation ({}) did not match the "
#                 "expected ({}): difference"
#                 .format(recorded_cv, ref_cv, recorded_cv - ref_cv))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', type=str, default='izhi',
                        help=("Which test to run, can be one of: 'alpha_syn', "
                              "'izhi', 'izhiFS', 'liaf', 'poisson' or 'hh' "
                              "(default: %(default)s )"))
    parser.add_argument('--plot', action='store_true',
                        help="Plot the traces on the same plot")
    parser.add_argument('--print_comparisons', action='store_true',
                        help=("Print the differences between the traces summed"
                              " over every time point"))
    parser.add_argument('--simulators', nargs='+', default=['nest', 'neuron'],
                        help="Which simulators to run the test for "
                        "(default %(default)s)")
    parser.add_argument('--duration', type=float,
                        help="Override the duration of the test")
    parser.add_argument('--dt', type=float,
                        help="Override the dt of the test")
    parser.add_argument('--build_mode', type=str, default='force',
                        help=("the build mode used to run the test (typically "
                              "'force' is used to regenerate the code but "
                              "'recompile' can be useful in debugging)"))
    args = parser.parse_args(argv)
    kwargs = {}
    if args.duration:
        kwargs['duration'] = args.duration * un.ms
    if args.dt:
        kwargs['dt'] = args.dt * un.ms
    tester = TestDynamics()
    test = getattr(tester, 'test_' + args.test)
    test(plot=args.plot, print_comparisons=args.print_comparisons,
         simulators=args.simulators, build_mode=args.build_mode, **kwargs)
    print("done")
