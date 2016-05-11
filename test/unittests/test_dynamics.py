#!/usr/bin/env python
import quantities as pq
import os.path
from itertools import chain, repeat
import ninemlcatalog
from nineml import units as un
from nineml.user import Property
from nineml.user.multi.component import MultiDynamics
from nineml.user import DynamicsProperties
from pype9.testing import Comparer, input_step, input_freq
from pype9.base.cells import (
    MultiDynamicsWithSynapses, DynamicsWithSynapsesProperties,
    ConnectionParameterSet, ConnectionPropertySet)
from pype9.nest.cells import (
    CellMetaClass as CellMetaClassNEST,
    simulation_controller as simulatorNEST)
from pype9.nest.units import UnitHandler as UnitHandlerNEST
from pype9.neuron.cells import (
    CellMetaClass as CellMetaClassNEURON,
    simulation_controller as simulatorNEURON)
if __name__ == '__main__':
    from utils import DummyTestCase as TestCase  # @UnusedImport
else:
    from unittest import TestCase  # @Reimport

cell_metaclasses = {'neuron': CellMetaClassNEURON,
                    'nest': CellMetaClassNEST}


class TestDynamics(TestCase):

    liaf_initial_states = {'v': -65.0 * pq.mV, 'end_refractory': 0.0 * pq.ms}
    liaf_nest_translations = {
        # the conversion to g_leak is a bit of a hack because it is
        # actually Cm / g_leak
        'Cm': ('C_m', 1), 'g_leak': ('tau_m', 0.4),
        'refractory_period': ('t_ref', 1), 'e_leak': ('E_L', 1),
        'v_reset': ('V_reset', 1), 'v': ('V_m', 1),
        'v_threshold': ('V_th', 1), 'end_refractory': (None, 1)}
    liaf_neuron_translations = {
        'Cm': ('cm', 1), 'g_leak': ('pas.g', 1),
        'refractory_period': ('trefrac', 1), 'e_leak': ('pas.e', 1),
        'v_reset': ('vreset', 1), 'v_threshold': ('vthresh', 1),
        'end_refractory': (None, 1), 'v': ('v', 1)}

    def test_izhi(self, plot=False, print_comparisons=False,
                  simulators=['nest', 'neuron'], dt=0.001, duration=100.0,
                  **kwargs):  # @UnusedVariable
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
            input_signal=input_step('Isyn', 0.02, 50, 100, dt),
            nest_translations={'V': ('V_m', 1), 'U': ('U_m', 1),
                               'weight': (None, 1), 'C_m': (None, 1),
                               'theta': ('V_th', 1),
                               'alpha': (None, 1), 'beta': (None, 1),
                               'zeta': (None, 1)},
            neuron_translations={'C_m': (None, 1), 'weight': (None, 1),
                                 'V': ('v', 1), 'U': ('u', 1),
                                 'alpha': (None, 1), 'beta': (None, 1),
                                 'zeta': (None, 1), 'theta': ('vthresh', 1)},
            neuron_build_args={'build_mode': 'force'},
            nest_build_args={'build_mode': 'force'},
            build_name='Izhikevich9ML')
        comparer.simulate(duration)
        comparisons = comparer.compare()
        if print_comparisons:
            for (name1, name2), diff in comparisons.iteritems():
                print '{} v {}: {}'.format(name1, name2, diff)
        if plot:
            comparer.plot()
        if 'nest' in simulators and 'neuron' in simulators:
            self.assertLess(
                comparisons[('9ML-nest', '9ML-neuron')], 0.4 * pq.mV,
                "Izhikevich NEURON 9ML simulation did not match NEST 9ML")
        if 'neuron' in simulators:
            self.assertLess(
                comparisons[('9ML-neuron', 'Ref-neuron')], 0.0015 * pq.mV,
                "Izhikevich NEURON 9ML simulation did not match reference "
                "PyNN")
        if 'nest' in simulators:
            self.assertLess(
                comparisons[('9ML-nest', 'Ref-nest')], 0.02 * pq.mV,
                "Izhikevich NEST 9ML simulation did not match reference "
                "built-in")

    def test_hh(self, plot=False, print_comparisons=False,
                simulators=['nest', 'neuron'], dt=0.001, duration=100.0,
                **kwargs):  # @UnusedVariable
        # Perform comparison in subprocess
        comparer = Comparer(
            nineml_model=ninemlcatalog.load(
                'neuron/HodgkinHuxley', 'PyNNHodgkinHuxley'),
            state_variable='v', dt=dt, simulators=simulators,
            initial_states={'v': -65.0 * pq.mV, 'm': 0.0, 'h': 1.0, 'n': 0.0},
            properties=ninemlcatalog.load(
                'neuron/HodgkinHuxley', 'PyNNHodgkinHuxleyProperties'),
            neuron_ref='hh_traub', nest_ref='hh_cond_exp_traub',
            input_signal=input_step('iExt', 0.5, 50, 100, dt),
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
            nest_build_args={'build_mode': 'force'})
        comparer.simulate(duration)
        comparisons = comparer.compare()
        if print_comparisons:
            for (name1, name2), diff in comparisons.iteritems():
                print '{} v {}: {}'.format(name1, name2, diff)
        if plot:
            comparer.plot()
        # FIXME: Need to work out what is happening with the reference NEURON
        if 'nest' in simulators and 'neuron' in simulators:
            self.assertLess(
                comparisons[('9ML-nest', '9ML-neuron')], 0.5 * pq.mV,
                "HH 9ML NEURON and NEST simulation did not match each other")
        if 'neuron' in simulators:
            self.assertLess(
                comparisons[('9ML-neuron', 'Ref-neuron')], 0.55 * pq.mV,
                "HH 9ML NEURON simulation did not match reference built-in")
        if 'nest' in simulators:
            self.assertLess(
                comparisons[('9ML-nest', 'Ref-nest')], 0.0015 * pq.mV,
                "HH 9ML NEST simulation did not match reference built-in")

    def test_liaf(self, plot=False, print_comparisons=False,
                  simulators=['nest', 'neuron'], dt=0.001, duration=100.0,
                  **kwargs):  # @UnusedVariable
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
            input_signal=input_step('i_synaptic', 1, 50, 100, dt),
            nest_translations=self.liaf_nest_translations,
            neuron_translations=self.liaf_neuron_translations,
            neuron_build_args={'build_mode': 'force'},
            nest_build_args={'build_mode': 'force'},
            extra_mechanisms=['pas'])
        comparer.simulate(duration)
        comparisons = comparer.compare()
        if print_comparisons:
            for (name1, name2), diff in comparisons.iteritems():
                print '{} v {}: {}'.format(name1, name2, diff)
        if plot:
            comparer.plot()
        if 'neuron' in simulators:
            self.assertLess(
                comparisons[('9ML-neuron', 'Ref-neuron')], 0.55 * pq.mV,
                "LIaF NEURON 9ML simulation did not match reference PyNN")
        if 'nest' in simulators:
            self.assertLess(
                comparisons[('9ML-nest', 'Ref-nest')], 0.01 * pq.mV,
                "LIaF NEST 9ML simulation did not match reference built-in")
        if 'nest' in simulators and 'neuron' in simulators:
            self.assertLess(
                comparisons[('9ML-nest', '9ML-neuron')], 0.55 * pq.mV,
                "LIaF NEURON 9ML simulation did not match NEST 9ML simulation")

    def test_alpha_syn(self, plot=False, print_comparisons=False,
                       simulators=['nest', 'neuron'], dt=0.001,
                       duration=100.0, **kwargs):  # @UnusedVariable
        # Perform comparison in subprocess
        iaf = ninemlcatalog.load(
            'neuron/LeakyIntegrateAndFire', 'PyNNLeakyIntegrateAndFire')
        alpha_psr = ninemlcatalog.load(
            'postsynapticresponse/Alpha', 'Alpha')
        static = ninemlcatalog.load(
            'plasticity/Static', 'Static')
        iaf_alpha = MultiDynamics(
            name='IafAlpha',
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
            port_exposures=[('syn', 'spike__psr', 'input_spike')])
        iaf_alpha_with_syn = MultiDynamicsWithSynapses(
            iaf_alpha,
            connection_parameter_sets=[
                ConnectionParameterSet(
                    'input_spike', [iaf_alpha.parameter('weight__pls__syn')])])
        initial_states = {'a__psr__syn': 0.0 * pq.nA,
                          'b__psr__syn': 0.0 * pq.nA}
        initial_regime = 'subthreshold___sole_____sole'
        liaf_properties = ninemlcatalog.load(
            'neuron/LeakyIntegrateAndFire/',
            'PyNNLeakyIntegrateAndFireProperties')
        alpha_properties = ninemlcatalog.load(
            'postsynapticresponse/Alpha', 'AlphaProperties')
        nest_tranlsations = {'tau__psr__syn': ('tau_syn_ex', 1),
                             'a__psr__syn': (None, 1),
                             'b__psr__syn': (None, 1),
                             'input_spike': ('input_spike', 367.55)}
        neuron_tranlsations = {'tau__psr__syn': ('psr.tau', 1),
                               'q__psr__syn': ('psr.q', 1),
                               'input_spike': ('input_spike', 0.36755),
                               'a__psr__syn': (None, 1),
                               'b__psr__syn': (None, 1)}
        initial_states.update(
            (k + '__cell', v) for k, v in self.liaf_initial_states.iteritems())
        properties = DynamicsProperties(
            name='IafAlphaProperties', definition=iaf_alpha,
            properties=dict(
                (p.name + '__' + suffix, p.quantity)
                for p, suffix in chain(
                    zip(liaf_properties.properties, repeat('cell')),
                    zip(alpha_properties.properties, repeat('psr__syn')),
                    [(Property('weight', 10 * un.nA), 'pls__syn')])))
        properties_with_syn = DynamicsWithSynapsesProperties(
            properties,  # @IgnorePep8
            connection_property_sets=[
                ConnectionPropertySet(
                    'input_spike',
                    [properties.property('weight__pls__syn')])])
        nest_tranlsations.update(
            (k + '__cell', v)
            for k, v in self.liaf_nest_translations.iteritems())
        neuron_tranlsations.update(
            (k + '__cell', v)
            for k, v in self.liaf_neuron_translations.iteritems())
        build_dir = os.path.join(os.path.dirname(iaf.url), '9build')
        comparer = Comparer(
            nineml_model=iaf_alpha_with_syn,
            state_variable='v__cell', dt=dt,
            simulators=simulators,
            properties=properties_with_syn,
            initial_states=initial_states,
            initial_regime=initial_regime,
            neuron_ref='ResetRefrac',
            nest_ref='iaf_psc_alpha',
            input_train=input_freq('input_spike', 500 * pq.Hz, duration,
                                   weight=[Property('weight__pls__syn',
                                                    10 * pq.nA)]),
            nest_translations=nest_tranlsations,
            neuron_translations=neuron_tranlsations,
            extra_mechanisms=['pas'],
            extra_point_process='AlphaISyn',
            neuron_build_args={
                'build_mode': 'force',
                'build_dir': os.path.join(build_dir, 'neuron', 'IaFAlpha')},
            nest_build_args={
                'build_mode': 'force',
                'build_dir': os.path.join(build_dir, 'nest', 'IaFAlpha')})
        comparer.simulate(duration)
        comparisons = comparer.compare()
        if print_comparisons:
            for (name1, name2), diff in comparisons.iteritems():
                print '{} v {}: {}'.format(name1, name2, diff)
        if plot:
            comparer.plot()
        if 'nest' in simulators and 'neuron' in simulators:
            self.assertLess(
                comparisons[('9ML-nest', '9ML-neuron')], 0.015 * pq.mV,
                "LIaF with Alpha syn NEST 9ML simulation did not match NEURON "
                "9ML simulation")
        if 'nest' in simulators:
            self.assertLess(
                comparisons[('9ML-nest', 'Ref-nest')], 0.04 * pq.mV,
                "LIaF with Alpha syn NEST 9ML simulation did not match "
                "reference built-in")
        if 'neuron' in simulators:
            self.assertLess(
                comparisons[('9ML-neuron', 'Ref-neuron')], 0.03 * pq.mV,
                "LIaF with Alpha syn NEURON 9ML simulation did not match "
                "reference PyNN")

    def test_izhiFS(self, plot=False, print_comparisons=False,
                    simulators=['nest', 'neuron'], dt=0.001, duration=100.0,
                    **kwargs):  # @UnusedVariable
        # Force compilation of code generation
        # Perform comparison in subprocess
        comparer = Comparer(
            nineml_model=ninemlcatalog.load(
                'neuron/Izhikevich', 'IzhikevichFastSpiking'),
            state_variable='V', dt=dt, simulators=simulators,
            properties=ninemlcatalog.load(
                'neuron/Izhikevich', 'SampleIzhikevichFastSpiking'),
            initial_states={'U': -1.625 * pq.mV / pq.ms, 'V': -65.0 * pq.mV},
            input_signal=input_step('iSyn', 100 * pq.pA, 0, 100, dt),
            initial_regime='subVb',
            neuron_build_args={'build_mode': 'force',
                               'external_currents': ['iSyn']},
            nest_build_args={'build_mode': 'force'},
            auxiliary_states=['U'])
        comparer.simulate(duration)
        comparisons = comparer.compare()
        if print_comparisons:
            for (name1, name2), diff in comparisons.iteritems():
                print '{} v {}: {}'.format(name1, name2, diff)
        if plot:
            comparer.plot()
        if 'nest' in simulators and 'neuron' in simulators:
            self.assertLess(
                comparisons[('9ML-nest', '9ML-neuron')], 0.4 * pq.mV,
                "Izhikevich 2007 NEURON 9ML simulation did not match NEST 9ML")

#     def test_aeif(self, plot=False, print_comparisons=False):
#         # Perform comparison in subprocess
#         comparer = Comparer(
#             nineml_model=ninemlcatalog.load(
#                 'neuron/AdExpIaF/AdExpIaF'),
#             state_variable='v', dt=dt, simulators=['nest', 'neuron'],
#             neuron_ref='AdExpIF', nest_ref='aeif_cond_alpha',
#             input_signal=input_step('iExt', 1, 50, 100, dt),
#             initial_states={'w': 0.0 * pq.nA, 'v': -65.0 * pq.mV},
#             properties=ninemlcatalog.load(
#                 'neuron/AdExpIaF/AdExpIaFProperties'),
#             nest_translations={
#                 'w': ('w', 1), 'Cm': ('C_m', 1), 'GL': ('g_L', 1000),
#                 'trefrac': ('t_ref', 1), 'EL': ('E_L', 1), 'a': ('a', 1000),
#                 'tauw': ('tau_w', 1), 'vreset': ('V_reset', 1),
#                 'v': ('V_m', 1), 'vthresh': ('V_th', 1), 'b': ('b', 1000),
#                 'vspike': ('V_peak', 1), 'delta': ('Delta_T', 1)},
#             neuron_translations={
#                 'Cm': ('cm', 1), 'GL': ('pas.g', 0.001), 'EL': ('pas.e', 1)},
#             neuron_build_args={'build_mode': 'force'},
#             nest_build_args={'build_mode': 'force'},
#             extra_mechanisms=['pas'])
#         comparer.simulate(duration)
#         comparisons = comparer.compare()
#         if print_comparisons:
#             for (name1, name2), diff in comparisons.iteritems():
#                 print '{} v {}: {}'.format(name1, name2, diff)
#         if plot:
#             comparer.plot()
#         self.assertLess(
#             comparisons[('9ML-neuron', 'Ref-neuron')], 0.0015 * pq.mV,
#             "AdExpIaF NEURON 9ML simulation did not match reference PyNN")
#         self.assertLess(
#             comparisons[('9ML-nest', 'Ref-nest')], 0.00015 * pq.mV,
#             "AdExpIaF NEST 9ML simulation did not match reference built-in")

    def test_poisson(self, duration=1000 * un.s, rate=100 * un.Hz,
                     print_comparisons=False, simulators=['nest'],  # , 'neuron'] @IgnorePep8
                     dt=0.001, **kwargs):  # @UnusedVariable @IgnorePep8
        nineml_model = ninemlcatalog.load('input/Poisson', 'Poisson')
        build_args = {'neuron': {'build_mode': 'force',
                                 'external_currents': ['iSyn']},
                      'nest': {'build_mode': 'force'}}
        initial_states = {'t_next': 0.0 * un.ms}
        for sim_name in simulators:
            meta_class = cell_metaclasses[sim_name]
            # Build celltype
            celltype = meta_class(
                nineml_model, name=nineml_model.name, **build_args[sim_name])
            # Initialise simulator
            if sim_name == 'neuron':
                # Run NEURON simulation
                import neuron
                simulatorNEURON.reset()
                neuron.h.dt = dt
                simulatorNEURON.run(duration.in_units(un.ms))
            elif sim_name == 'nest':
                # Run NEST simulation
                import nest
                simulatorNEST.reset()
                nest.SetKernelStatus({'resolution': dt})
                simulatorNEST.run(duration.in_units(un.ms))
            else:
                assert False
            # Create and initialise cell
            cell = celltype(rate=rate)
            cell.record('spike_output')
            cell.update_state(initial_states)
            # Run simulation
            if sim_name == 'neuron':
                simulatorNEURON.run(duration.in_units(un.ms))
            elif sim_name == 'nest':
                simulatorNEST.run(duration.in_units(un.ms))
            else:
                assert False
            # Get recording
            spikes = cell.recording('spike_output')
            # Calculate the rate of the modelled process
            recorded_rate = pq.Quantity(
                len(spikes) / (spikes.t_stop - spikes.t_start), 'Hz')
            ref_rate = pq.Quantity(UnitHandlerNEST.to_pq_quantity(rate), 'Hz')
            self.assertAlmostEqual(
                ref_rate, recorded_rate,
                ("Recorded rate of {} poisson generator ({}) did not match "
                 "desired ({}): difference {}".format(
                     sim_name, recorded_rate, ref_rate,
                     recorded_rate - ref_rate)))
            # Calculate the absolute deviation
            isi_avg = pq.Quantity(1.0 / recorded_rate, 'ms')
            isi_std_dev = (abs((spikes[1:] - spikes[:-1]) - isi_avg) /
                           (len(spikes) - 1))
            recorded_cv = isi_std_dev / isi_avg
            ref_cv = 1.0 / ref_rate ** 2.0
            if print_comparisons:
                print "ref cv: {}, recorded cv {}".format(ref_cv, recorded_cv)
            self.assertAlmostEqual(
                recorded_cv, ref_cv,
                "Recorded coefficient of variation ({}) did not match the "
                "expected ({}): difference"
                .format(recorded_cv, ref_cv, recorded_cv - ref_cv))


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
    args = parser.parse_args()
    kwargs = {}
    if args.duration:
        kwargs['duration'] = args.duration
    if args.dt:
        kwargs['dt'] = args.dt
    tester = TestDynamics()
    test = getattr(tester, 'test_' + args.test)
    test(plot=args.plot, print_comparisons=args.print_comparisons,
         simulators=args.simulators, **kwargs)
    print "done"
